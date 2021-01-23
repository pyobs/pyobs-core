import logging
from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CallbackContext

from pyobs.events import Event
from pyobs import Module
from pyobs.interfaces import IAutonomous
from pyobs.object import get_class_from_string

log = logging.getLogger(__name__)


class TelegramUserState(Enum):
    IDLE = 0,
    AUTH = 1,
    EXEC_MODULE = 2,
    EXEC_METHOD = 3


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
        self._user_states = {}
        self._updater = None

    def open(self):
        from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
        Module.open(self)

        # get dispatcher
        self._updater = Updater(token=self._token)
        dispatcher = self._updater.dispatcher

        # add /start handler
        start_handler = CommandHandler('start', self._command_start)
        dispatcher.add_handler(start_handler)
        exec_handler = CommandHandler('exec', self._command_exec)
        dispatcher.add_handler(exec_handler)

        # add text handler
        echo_handler = MessageHandler(Filters.text & (~Filters.command), self._process_message)
        dispatcher.add_handler(echo_handler)

        dispatcher.add_handler(CallbackQueryHandler(self.button))

        # start polling
        self._updater.start_polling()

    def close(self):
        Module.close(self)
        self._updater.stop()

    def _is_user_known(self, user_id: int) -> bool:
        # try to load file
        try:
            config = self.vfs.read_yaml('/pyobs/telegram.yaml')
        except FileNotFoundError:
            return False

        # does user exist in file_
        return 'user_ids' in config and user_id in config['user_ids']

    def _store_user(self, user_id: int, name: str):
        # load config
        try:
            config = self.vfs.read_yaml('/pyobs/telegram.yaml')
        except FileNotFoundError:
            config = {}

        # add user
        if 'user_ids' not in config:
            config['user_ids'] = {}

        # append user
        config['user_ids'][user_id] = name

        # store it
        self.vfs.write_yaml(config, '/pyobs/telegram.yaml')

    def _command_start(self, update, context):
        # is user already known?
        if self._is_user_known(update.message.from_user.id):
            # welcome him back
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Welcome back %s!' % update.message.from_user.first_name)
        else:
            # go to AUTH state
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="I'm the pyobs bot for IAG50. Password?")
            self._user_states[update.message.from_user.id] = TelegramUserState.AUTH

    def _command_exec(self, update, context):
        # not logged in?
        if not self._is_user_known(update.message.from_user.id):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Not logged in')
            return

        # list modules
        #clients = '\n'.join(self.comm.clients)
        #context.bot.send_message(chat_id=update.effective_chat.id, text='Modules:\n' + clients)

        keyboard = [[InlineKeyboardButton(c, callback_data=c)] for c in self.comm.clients]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose module:', reply_markup=reply_markup)

        self._user_states[update.message.from_user.id] = TelegramUserState.EXEC_MODULE

    def button(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query.answer()

        # what state are we in?
        user_id = query.from_user.id
        if self._user_states[user_id] == TelegramUserState.EXEC_MODULE:
            # get proxy for selected module
            proxy = self.proxy(query.data)

            keyboard = [[InlineKeyboardButton(m, callback_data='%s.%s' % (query.data, m))]
                        for m in proxy.method_names]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text='Chose method in %s:' % query.data)
            query.edit_message_reply_markup(reply_markup)

            self._user_states[user_id] = TelegramUserState.EXEC_METHOD

        elif self._user_states[user_id] == TelegramUserState.EXEC_METHOD:
            # get proxy for selected
            query.edit_message_text(text='Enter parameters for %s:' % query.data)
            #query.edit_message_reply_markup(InlineKeyboardMarkup([]))


        #query.edit_message_text(text=f"Selected option: {query.data}")

    def _process_message(self, update, context):
        # get user id and create state, if necessary
        user_id = update.message.from_user.id
        if user_id not in self._user_states:
            self._user_states[user_id] = TelegramUserState.IDLE

        # what state is user in?
        if self._user_states[user_id] == TelegramUserState.AUTH:
            # AUTH, so we expect a password. Is it valid?
            if update.message.text == self._password:
                # Yes, successful AUTH
                context.bot.send_message(chat_id=update.effective_chat.id, text='AUTH successful.')
                self._user_states[user_id] = TelegramUserState.IDLE
                self._store_user(user_id, update.message.from_user.first_name)

            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text='AUTH failed, try again.')

        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='CHAT')


__all__ = ['Telegram']
