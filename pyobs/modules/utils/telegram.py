import asyncio
import io
import logging
from enum import Enum
from inspect import Parameter
from pprint import pprint
from typing import Any, Optional, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CallbackContext, Application

from pyobs.modules import Module
from pyobs.events import LogEvent, Event

log = logging.getLogger(__name__)


class TelegramUserState(Enum):
    IDLE = (0,)
    AUTH = (1,)
    EXEC_MODULE = (2,)
    EXEC_METHOD = (3,)
    EXEC_PARAMS = (4,)
    LOG_LEVEL = 5


class Telegram(Module):
    """A telegram bot."""

    __module__ = "pyobs.modules.utils"

    def __init__(self, token: str, password: str, allow_new_users: bool = True, **kwargs: Any):
        """Initialize a new bot.

        Args:
            token: The telegram API token.
            password: Password for users to log in.
            allow_new_users: Whether new users are allowed to connect.

        """
        Module.__init__(self, **kwargs)

        # store
        self._token = token
        self._password = password
        self._allow_new_users = allow_new_users
        self._message_queue: asyncio.Queue[Any] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._application: Application | None = None  # type: ignore

        # get log levels
        self._log_levels = {
            logging.getLevelName(x): x for x in range(1, 101) if not logging.getLevelName(x).startswith("Level")
        }

        # thread
        self.add_background_task(self._log_sender_thread)

    async def open(self) -> None:
        """Open module."""
        from telegram.ext import CommandHandler, MessageHandler, filters

        await Module.open(self)
        self._loop = asyncio.get_running_loop()

        # get dispatcher
        self._application = Application.builder().token(self._token).build()

        # add command handler
        self._application.add_handler(CommandHandler("start", self._command_start))
        self._application.add_handler(CommandHandler("exec", self._command_exec))
        self._application.add_handler(CommandHandler("modules", self._command_modules))
        self._application.add_handler(CommandHandler("loglevel", self._command_loglevel))

        # add text handler
        echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self._process_message)
        self._application.add_handler(echo_handler)

        # add callback handler for buttons
        self._application.add_handler(CallbackQueryHandler(self._handle_buttons))

        # load storage file
        try:
            self._application.bot_data["storage"] = await self.vfs.read_yaml("/pyobs/telegram.yaml")
        except FileNotFoundError:
            self._application.bot_data["storage"] = {}

        # start polling
        await self._application.initialize()
        if self._application.updater is None:
            raise ValueError("No telegram updater.")
        await self._application.updater.start_polling()
        await self._application.start()

        # listen to log events
        await self.comm.register_event(LogEvent, self._process_log_entry)

    async def close(self) -> None:
        """Close module."""
        await Module.close(self)

        # stop telegram
        if self._application is not None:
            if self._application.updater is not None:
                await self._application.updater.stop()
            await self._application.stop()
            await self._application.shutdown()

    async def _save_storage(self, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Save storage file.

        Args:
            context: Telegram context.
        """
        await self.vfs.write_yaml("/pyobs/telegram.yaml", context.bot_data["storage"])

    @staticmethod
    def _is_user_authorized(context: CallbackContext[Any, Any, Any, Any], user_id: int) -> bool:
        """Is user authorized?

        Args:
            context: Telegram context.
            user_id: ID of user.

        Returns:
            Whether user is known and authorized to give commands.
        """
        s = context.bot_data["storage"]
        return "users" in s and user_id in s["users"]

    def _store_user(self, context: CallbackContext[Any, Any, Any, Any], user_id: int, name: str) -> None:
        """Store new user in auth database.

        Args:
            context: Telegram context.
            user_id: ID of user.
            name: Name of user.
        """

        # add user
        s = context.bot_data["storage"]
        if "users" not in s:
            s["users"] = {}
        s["users"][user_id] = {"name": name, "loglevel": None}
        if self._loop is None:
            raise ValueError("No event loop.")
        asyncio.run_coroutine_threadsafe(self._save_storage(context), self._loop)

    async def _command_start(self, update: Update, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Handle /start command.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        if context.user_data is None:
            raise ValueError("No user data in context.")
        if update.message is None or update.message.from_user is None or update.effective_chat is None:
            raise ValueError("Invalid message data")

        # is user already known?
        if self._is_user_authorized(context, update.message.from_user.id):
            # welcome him back
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="Welcome back %s!" % update.message.from_user.first_name
            )

        else:
            # do we allow for new users?
            if self._allow_new_users:
                # go to AUTH state
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Password?")
                context.user_data["state"] = TelegramUserState.AUTH

            else:
                # show message
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text="No new users allowed in the system."
                )

    async def _command_exec(self, update: Update, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Handle /exec command.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        if context.user_data is None:
            raise ValueError("No user data in context.")
        if update.message is None or update.message.from_user is None or update.effective_chat is None:
            raise ValueError("Invalid message data")

        # not logged in?
        if not self._is_user_authorized(context, update.message.from_user.id):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Not logged in, use /start.")
            return

        # create buttons for all modules
        keyboard = [[InlineKeyboardButton(c, callback_data=c)] for c in self.comm.clients] + [
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Please choose module:", reply_markup=reply_markup)

        # go to EXEC_MODULE state
        context.user_data["state"] = TelegramUserState.EXEC_MODULE

    @staticmethod
    def _reset_state(context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Reset state."""
        if context.user_data is None:
            raise ValueError("No user data in context.")
        context.user_data["state"] = TelegramUserState.IDLE
        context.user_data["method"] = None
        context.user_data["params"] = []
        context.user_data["exec_query"] = None

    async def _handle_buttons(self, update: Update, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Handle click on buttons.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        if context.user_data is None:
            raise ValueError("No user data in context.")

        # get query
        query = update.callback_query

        if query is None or query.from_user is None:
            raise ValueError("Invalid query data")

        # not logged in?
        if not self._is_user_authorized(context, query.from_user.id):
            await query.edit_message_text(text="Not logged in, use /start.")
            return

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()

        # cancel?
        if query.data == "cancel":
            # reset state
            self._reset_state(context)

            # remove markup
            await query.edit_message_text("Canceled.")

        # what state are we in?
        if context.user_data["state"] == TelegramUserState.EXEC_MODULE:
            # get proxy for selected module
            proxy = await self.proxy(query.data)

            # show buttons for all modules
            keyboard = [
                [InlineKeyboardButton(m, callback_data="%s.%s" % (query.data, m))] for m in proxy.method_names
            ] + [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="Chose method in %s:" % query.data)
            await query.edit_message_reply_markup(reply_markup)

            # change to EXEC_MEHOD state
            context.user_data["state"] = TelegramUserState.EXEC_METHOD

        elif context.user_data["state"] == TelegramUserState.EXEC_METHOD:
            # init command
            context.user_data["method"] = query.data
            context.user_data["params"] = []
            if update.callback_query is None or update.callback_query.message is None:
                raise ValueError("Invalid update message.")
            context.user_data["exec_query_message"] = update.callback_query.message.message_id
            if hasattr(update.callback_query.message, "chat_id"):
                context.user_data["exec_query_chat"] = update.callback_query.message.chat_id

            # show buttons for all methods
            keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="Executing %s..." % query.data)
            await query.edit_message_reply_markup(reply_markup)

            # go to EXEC_PARAMS state
            context.user_data["state"] = TelegramUserState.EXEC_PARAMS

            # see whether this command runs without parameters
            self._handle_params(update, context)

        elif context.user_data["state"] == TelegramUserState.LOG_LEVEL:
            # set log level
            s = context.bot_data["storage"]
            s["users"][query.from_user.id]["loglevel"] = query.data
            await self._save_storage(context)

            # change to IDLE state
            await query.edit_message_text(text="Changed log level to %s." % query.data)
            context.user_data["state"] = TelegramUserState.IDLE

    def _handle_params(self, update: Update, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Handle input of params when in EXEC_PARAMS state.

        Args:
            update: Message to process.
            context: Telegram context.
        """
        if self._loop is None:
            raise ValueError("No event loop.")
        asyncio.run_coroutine_threadsafe(self._handle_params_async(update, context), self._loop)

    async def _handle_params_async(self, update: Update, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Handle input of params when in EXEC_PARAMS state.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        if context.user_data is None:
            raise ValueError("No user data in context.")
        if update.effective_chat is None:
            raise ValueError("No effective chat.")

        # wrong state?
        if context.user_data["state"] != TelegramUserState.EXEC_PARAMS:
            return

        # get proxy and method signature
        module, method = context.user_data["method"].split(".")
        proxy = await self.proxy(module)
        signature = proxy.signature(method)

        # get list of parameters
        params = [
            (name, param) for name, param in signature.parameters.items() if name not in ["self", "args", "kwargs"]
        ]

        # append param, if new one was received
        if update.message is not None:
            # get type of new parameter
            param_type = params[len(context.user_data["params"])][1].annotation

            # cast it
            value = param_type(update.message.text)

            # append it
            context.user_data["params"].append(value)

        # got enough params?
        nparams = len(context.user_data["params"])
        if nparams >= len(params):
            # ID for command?
            if "ncalls" not in context.user_data:
                context.user_data["ncalls"] = 0
            context.user_data["ncalls"] += 1
            call_id = context.user_data["ncalls"]

            # remove cancel button, and show command
            msg = "Executing %s..." % context.user_data["method"]
            await context.bot.edit_message_text(
                text=msg,
                message_id=context.user_data["exec_query_message"],
                chat_id=context.user_data["exec_query_chat"],
            )

            # send message
            command = (
                context.user_data["method"]
                + "("
                + ", ".join(['"%s"' % p if isinstance(p, str) else str(p) for p in context.user_data["params"]])
                + ")"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="Executing #%d:\n%s" % (call_id, command)
            )

            # start call
            asyncio.create_task(
                self._call_method(
                    context, update.effective_chat.id, call_id, context.user_data["method"], context.user_data["params"]
                )
            )

            # reset
            self._reset_state(context)

        else:
            # no, print next one
            next_param: Parameter = params[nparams][1]

            # format it
            message = "Value for " + next_param.name
            if next_param.annotation is not None:
                message += ": " + next_param.annotation.__name__
            if next_param.default != Parameter.empty:
                message += " = " + str(next_param.default)
            message += "?"

            # send it
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    async def _call_method(
        self, context: CallbackContext[Any, Any, Any, Any], chat_id: int, call_id: int, method: str, params: List[Any]
    ) -> None:
        """

        Args:
            context: Telegram context.
            chat_id: Telegram chat ID.
            call_id: ID of command.
            method: Method to call as <module>.<method>
            params: List of parameters.
        """
        # get proxy
        module, method_name = method.split(".")
        proxy = await self.proxy(module)

        # call it
        func = getattr(proxy, method_name)
        response = await func(*params)

        # set message
        if response is None:
            message = "Finished #%d." % call_id

        else:
            # format message
            with io.StringIO() as sio:
                # format response
                pprint(response, stream=sio, indent=2)
                message = "Finished #%d:\n%s" % (call_id, sio.getvalue())

        # send reply
        await context.bot.send_message(chat_id=chat_id, text=message)

    async def _process_message(self, update: Update, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Handle normal text messages, e.g. for login or method parameters.

        Args:
            update: Telegram message.
            context: Telegram context.
        """

        if context.user_data is None:
            raise ValueError("No user data in context.")
        if update.message is None or update.effective_chat is None or update.message.from_user is None:
            raise ValueError("Invalid message.")

        # what state is user in?
        if context.user_data["state"] == TelegramUserState.AUTH:
            # AUTH, so we expect a password. Is it valid?
            if update.message.text == self._password:
                # Yes, successful AUTH
                await context.bot.send_message(chat_id=update.effective_chat.id, text="AUTH successful.")
                context.user_data["state"] = TelegramUserState.IDLE
                self._store_user(context, update.message.from_user.id, update.message.from_user.first_name)

            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="AUTH failed, try again.")

        elif context.user_data["state"] == TelegramUserState.EXEC_PARAMS:
            # we're expecting params, so handle them
            self._handle_params(update, context)

    async def _command_modules(self, update: Update, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Handle /modules command that shows list of modules.

        Args:
            update: Message to process.
            context: Telegram context.
        """
        if update.message is None or update.effective_chat is None or update.message.from_user is None:
            raise ValueError("Invalid message.")

        # not logged in?
        if not self._is_user_authorized(context, update.message.from_user.id):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Not logged in, use /start.")
            return

        # list all modules
        message = "Available modules:\n" + "\n".join(["- " + c for c in self.comm.clients])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    async def _command_loglevel(self, update: Update, context: CallbackContext[Any, Any, Any, Any]) -> None:
        """Handle /loglevel command that sets the log level

        Args:
            update: Message to process.
            context: Telegram context.
        """

        if context.user_data is None:
            raise ValueError("No user data in context.")
        if update.message is None or update.effective_chat is None or update.message.from_user is None:
            raise ValueError("Invalid message.")

        # not logged in?
        if not self._is_user_authorized(context, update.message.from_user.id):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Not logged in, use /start.")
            return

        # set state
        context.user_data["state"] = TelegramUserState.LOG_LEVEL

        # get current level
        s = context.bot_data["storage"]
        current_level = s["users"][update.message.from_user.id]["loglevel"]

        # create buttons for all log levels
        keyboard = [[InlineKeyboardButton(level, callback_data=level)] for level in self._log_levels.keys()] + [
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Current log level: %s\nPlease choose new log level:" % current_level, reply_markup=reply_markup
        )

    async def _process_log_entry(self, entry: Event, sender: str) -> bool:
        """Process a new log entry.

        Args:
            entry: The log event.
            sender: Name of sender.
        """
        if not isinstance(entry, LogEvent):
            return False

        # get numerical value for log level
        level = self._log_levels[entry.level]

        # build log message
        message = "(%s) %s: %s" % (entry.level, sender, entry.message)

        # get storage
        if self._application is None:
            raise ValueError("No update initialised.")
        s = self._application.bot_data["storage"]

        # loop users
        for user_id, user in s["users"].items():
            # get user log level
            user_level = self._log_levels[user["loglevel"]] if user["loglevel"] in self._log_levels else 100

            # is it larger than the log entry level?
            if level >= user_level:
                # queue message
                self._message_queue.put_nowait((user_id, message))

        return True

    async def _log_sender_thread(self) -> None:
        """Thread for sending messages."""

        while True:
            # get next entry
            user_id, message = await self._message_queue.get()

            # send message
            try:
                if self._application is None:
                    raise ValueError("No update initialised.")
                await self._application.bot.send_message(chat_id=user_id, text=message)

            except Exception:
                # something went wrong, sleep a little and queue message again
                await asyncio.sleep(10)
                await self._message_queue.put((user_id, message))


__all__ = ["Telegram"]
