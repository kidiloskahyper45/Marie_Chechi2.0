import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        chat.kick_member(user.id)
        msg.reply_text("താൻ എന്തൊരു വെറുപ്പിക്കൽ ആണെടോ... ഇങ്ങനെ നിർത്താതെ മെസ്സേജ് അയച്ചാൽ മറ്റുള്ളവർക്ക് ശല്യം ആകില്ലേ.... തന്നെ ഇനി ഈ ഗ്രൂപ്പിന് ആവിശ്യം ഇല്ല ഇറങ്ങി പൊക്കോ....")

        return "<b>{}:</b>" \
               "\n#BANNED" \
               "\n<b>User:</b> {}" \
               "\nFlooded the group.".format(html.escape(chat.title),
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        msg.reply_text("നിങ്ങൾ എനിക്ക് Permissions തരാത്ത കാലത്തോളം ഈ സേവനം നിങ്ങൾക്ക് ഉപയോഗിക്കാൻ കഴിയില്ല.")
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#INFO" \
               "\nDon't have kick permissions, so automatically disabled antiflood.".format(chat.title)


@run_async
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("ചറ പറ മെസ്സേജ് അയക്കുന്നവരെ ഇനി ഞാൻ പുറത്താക്കുന്നതല്ല.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("ചറ പറ മെസ്സേജ് അയക്കുന്നവരെ ഇനി ഞാൻ പുറത്താക്കുന്നതല്ല.")
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nDisabled antiflood.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount < 3:
                message.reply_text("Antiflood has to be either 0 (disabled), or a number bigger than 3!")
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("മെസ്സേജ് നിയന്ത്രണം {} എണ്ണത്തിലേക്ക് ആക്കിയിട്ടുണ്ട് ".format(amount))
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet antiflood to <code>{}</code>.".format(html.escape(chat.title),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text("താങ്കൾ പറയുന്നത് എനിക്ക് മനസ്സിലാകുന്നില്ല.... ഒന്നെങ്കിൽ number ഉപയോഗിക്കുക അല്ലെങ്കിൽ Yes-No  ഉപയോഗിക്കുക ")

    return ""


@run_async
def flood(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]

    limit = sql.get_flood_limit(chat.id)
    if limit == 0:
        update.effective_message.reply_text("ഞാൻ ഇപ്പോൾ മെസ്സേജ് നിയന്ത്രണം നടത്തുന്നില്ല !")
    else:
        update.effective_message.reply_text(
            " {} മെസ്സേജിൽ കൂടുതൽ ഒരേ സമയം അയക്കുന്ന ആളെ ഞാൻ ബൺ കൊടുത്ത് വിടുന്നതാണ്.".format(limit))


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "*Not* currently enforcing flood control."
    else:
        return "മെസ്സേജ് നിയന്ത്രണം `{}` എന്നതിലേക്ക് ആക്കിയിരിക്കുന്നു .".format(limit)


__help__ = """
 - /flood: നിങ്ങൾക്ക് നിലവിലുള്ള മെസ്സേജ് നിയന്ത്രണം അറിയാൻ..

*Admin only:*
 - /setflood <int/'no'/'off'>: enables or disables flood control
"""

__mod_name__ = "നിയന്ത്രണം🗽"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True, filters=Filters.group)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
