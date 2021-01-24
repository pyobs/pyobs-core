import io
import logging
from enum import Enum
from inspect import Parameter
from pprint import pprint
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CallbackContext

from pyobs import Module

log = logging.getLogger(__name__)


class TelegramUserState(Enum):
    IDLE = 0,
    AUTH = 1,
    EXEC_MODULE = 2,
    EXEC_METHOD = 3,
    EXEC_PARAMS = 4,
    LOG_LEVEL = 5


class Telegram(Module):
    """A telegram bot."""

    def __init__(self, token: str, password: str, *args, **kwargs):
        """Initialize a new bot.

        Args:
            token: The telegram API token.
            password: Password for users to log in.

        """
        Module.__init__(self, *args, **kwargs)

        # store
        self._token = token
        self._password = password
        self._updater = None

    def open(self):
        """Open module."""
        from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
        Module.open(self)

        # get dispatcher
        self._updater = Updater(token=self._token)
        dispatcher = self._updater.dispatcher

        # add command handler
        dispatcher.add_handler(CommandHandler('start', self._command_start))
        dispatcher.add_handler(CommandHandler('exec', self._command_exec))
        dispatcher.add_handler(CommandHandler('modules', self._command_modules))
        dispatcher.add_handler(CommandHandler('loglevel', self._command_loglevel))

        # add text handler
        echo_handler = MessageHandler(Filters.text & (~Filters.command), self._process_message)
        dispatcher.add_handler(echo_handler)

        # add callback handler for buttons
        dispatcher.add_handler(CallbackQueryHandler(self._handle_buttons))

        # start polling
        self._updater.start_polling()

    def close(self):
        """Close module."""
        Module.close(self)

        # stop telegram
        self._updater.stop()

    def _load_users(self) -> dict:
        """Load user file."""
        # try to load file
        try:
            return self.vfs.read_yaml('/pyobs/telegram.yaml')
        except FileNotFoundError:
            return {}

    def _save_users(self, users: dict):
        """Save user file.

        Args:
            users: Users dictionary.
        """
        self.vfs.write_yaml(users, '/pyobs/telegram.yaml')

    def _is_user_authorized(self, user_id: int) -> bool:
        """Is user authorized?

        Args:
            user_id: ID of user.

        Returns:
            Whether user is known and authorized to give commands.
        """
        users = self._load_users()
        return 'users' in users and user_id in users['users']

    def _store_user(self, user_id: int, name: str):
        """Store new user in auth database.

        Args:
            user_id: ID of user.
            name: Name of user.
        """

        # add user
        users = self._load_users()
        users['users'][user_id] = {
            'name': name,
            'log_level': None
        }
        self._save_users(users)

    def _command_start(self, update: Update, context: CallbackContext):
        """Handle /start command.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        # is user already known?
        if self._is_user_authorized(update.message.from_user.id):
            # welcome him back
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Welcome back %s!' % update.message.from_user.first_name)
        else:
            # go to AUTH state
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="I'm the pyobs bot for IAG50. Password?")
            context.user_data['state'] = TelegramUserState.AUTH

    def _command_exec(self, update: Update, context: CallbackContext):
        """Handle /exec command.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        # not logged in?
        if not self._is_user_authorized(update.message.from_user.id):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Not logged in')
            return

        # create buttons for all modules
        keyboard = [[InlineKeyboardButton(c, callback_data=c)] for c in self.comm.clients] + \
                   [[InlineKeyboardButton('Cancel', callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose module:', reply_markup=reply_markup)

        # go to EXEC_MODULE state
        context.user_data['state'] = TelegramUserState.EXEC_MODULE

    def _reset_state(self, context):
        """Reset state."""
        context.user_data['state'] = TelegramUserState.IDLE
        context.user_data['method'] = None
        context.user_data['params'] = []
        context.user_data['exec_query'] = None

    def _handle_buttons(self, update: Update, context: CallbackContext):
        """Handle click on buttons.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        # get query
        query = update.callback_query

        # not logged in?
        if not self._is_user_authorized(query.from_user.id):
            query.edit_message_text(text='Not logged in.')
            return

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query.answer()

        # cancel?
        if query.data == 'cancel':
            # reset state
            self._reset_state(context)

            # remove markup
            query.edit_message_text('Canceled.')

        # what state are we in?
        if context.user_data['state'] == TelegramUserState.EXEC_MODULE:
            # get proxy for selected module
            proxy = self.proxy(query.data)

            # show buttons for all modules
            keyboard = [[InlineKeyboardButton(m, callback_data='%s.%s' % (query.data, m))]
                        for m in proxy.method_names] + \
                       [[InlineKeyboardButton('Cancel', callback_data='cancel')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text='Chose method in %s:' % query.data)
            query.edit_message_reply_markup(reply_markup)

            # change to EXEC_MEHOD state
            context.user_data['state'] = TelegramUserState.EXEC_METHOD

        elif context.user_data['state'] == TelegramUserState.EXEC_METHOD:
            # init command
            context.user_data['method'] = query.data
            context.user_data['params'] = []
            context.user_data['exec_query_message'] = update.callback_query.message.message_id
            context.user_data['exec_query_chat'] = update.callback_query.message.chat_id

            # show buttons for all methods
            keyboard = [[InlineKeyboardButton('Cancel', callback_data='cancel')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text='Executing %s...' % query.data)
            query.edit_message_reply_markup(reply_markup)

            # go to EXEC_PARAMS state
            context.user_data['state'] = TelegramUserState.EXEC_PARAMS

            # see whether this command runs without parameters
            self._handle_params(update, context)

        elif context.user_data['state'] == TelegramUserState.LOG_LEVEL:
            # set log level
            users = self._load_users()
            users['users'][query.from_user.id]['loglevel'] = query.data
            self._save_users(users)

            # change to IDLE state
            query.edit_message_text(text='Changed log level to %s.' % query.data)
            context.user_data['state'] = TelegramUserState.IDLE

    def _handle_params(self, update: Update, context: CallbackContext):
        """Handle input of params when in EXEC_PARAMS state.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        # wrong state?
        if context.user_data['state'] != TelegramUserState.EXEC_PARAMS:
            return

        # get proxy and method signature
        module, method = context.user_data['method'].split('.')
        proxy = self.proxy(module)
        signature = proxy.signature(method)

        # get list of parameters
        params = [(name, param) for name, param in signature.parameters.items()
                  if name not in ['self', 'args', 'kwargs']]

        # append param, if new one was received
        if update.message is not None:
            # get type of new parameter
            param_type = params[len(context.user_data['params'])][1].annotation

            # cast it
            value = param_type(update.message.text)

            # append it
            context.user_data['params'].append(value)

        # got enough params?
        nparams = len(context.user_data['params'])
        if nparams >= len(params):
            # ID for command?
            if 'ncalls' not in context.user_data:
                context.user_data['ncalls'] = 0
            context.user_data['ncalls'] += 1
            call_id = context.user_data['ncalls']

            # build command
            command = '/exec ' + context.user_data['method'] + '(' + \
                      ', '.join(['"%s"' % p if isinstance(p, str) else str(p)
                                 for p in context.user_data['params']]) + \
                      ')'

            # remove cancel button, and show command
            msg = 'Executing #%d:\n%s' % (call_id, command)
            context.bot.edit_message_text(text=msg,
                                          message_id=context.user_data['exec_query_message'],
                                          chat_id=context.user_data['exec_query_chat'])

            # start call
            Thread(target=self._call_method, args=(context, update.effective_chat.id, call_id,
                                                   context.user_data['method'],
                                                   context.user_data['params'])).run()

            # reset
            self._reset_state(context)

        else:
            # no, print next one
            next_param: Parameter = params[nparams][1]

            # format it
            print(next_param.default, type(next_param.default))
            message = 'Value for ' + next_param.name
            if next_param.annotation is not None:
                message += ': ' + next_param.annotation.__name__
            if next_param.default != Parameter.empty:
                message += ' = ' + str(next_param.default)
            message += '?'

            # send it
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    def _call_method(self, context: CallbackContext, chat_id: int, call_id: int, method: str,
                     params: list):
        """

        Args:
            context: Telegram context.
            chat_id: Telegram chat ID.
            call_id: ID of command.
            method: Method to call as <module>.<method>
            params: List of parameters.
        """
        # get proxy
        module, method_name = method.split('.')
        proxy = self.proxy(module)

        # call it
        func = getattr(proxy, method_name)
        response = func(*params).wait()

        # format message
        with io.StringIO() as sio:
            pprint(response, stream=sio, indent=2, sort_dicts=False)
            message = 'Finished #%d:\n%s' % (call_id, sio.getvalue())

        # send reply
        context.bot.send_message(chat_id=chat_id, text=message)

    def _process_message(self, update: Update, context: CallbackContext):
        """Handle normal text messages, e.g. for login or method parameters.

        Args:
            update: Telegram message.
            context: Telegram context.
        """

        # what state is user in?
        if context.user_data['state'] == TelegramUserState.AUTH:
            # AUTH, so we expect a password. Is it valid?
            if update.message.text == self._password:
                # Yes, successful AUTH
                context.bot.send_message(chat_id=update.effective_chat.id, text='AUTH successful.')
                context.user_data['state'] = TelegramUserState.IDLE
                self._store_user(update.message.from_user.id, update.message.from_user.first_name)

            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text='AUTH failed, try again.')

        elif context.user_data['state'] == TelegramUserState.EXEC_PARAMS:
            # we're expecting params, so handle them
            self._handle_params(update, context)

    def _command_modules(self, update: Update, context: CallbackContext):
        """Handle /modules command that shows list of modules.

        Args:
            update: Message to process.
            context: Telegram context.
        """

        # not logged in?
        if not self._is_user_authorized(update.message.from_user.id):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Not logged in')
            return

        # list all modules
        message = 'Available modules:\n' + '\n'.join(['- ' + c for c in self.comm.clients])
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    def _command_loglevel(self, update: Update, context: CallbackContext):
        """Handle /loglevel command that sets the log level

        Args:
            update: Message to process.
            context: Telegram context.
        """

        # not logged in?
        if not self._is_user_authorized(update.message.from_user.id):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Not logged in')
            return

        # set state
        context.user_data['state'] = TelegramUserState.LOG_LEVEL

        # get named log levels
        levels = [logging.getLevelName(x) for x in range(1, 101)
                  if not logging.getLevelName(x).startswith('Level')]

        # get current level
        users = self._load_users()
        current_level = users['users'][update.message.from_user.id]['loglevel']

        # create buttons for all log levels
        keyboard = [[InlineKeyboardButton(l, callback_data=l)] for l in levels] + \
                   [[InlineKeyboardButton('Cancel', callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Current log level: %s\nPlease choose new log level:' % current_level,
                                  reply_markup=reply_markup)


__all__ = ['Telegram']
