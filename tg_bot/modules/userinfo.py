import html
from typing import Optional, List

from telegram import Message, Update, Bot, User
from telegram import ParseMode, MAX_MESSAGE_LENGTH
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.userinfo_sql as sql
from tg_bot import dispatcher, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user


@run_async
def about_me(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(username + " ഇയാളെക്കുറിച്ചുള്ള വിവരം ഇപ്പോൾ ലഭ്യമല്ല !")
    else:
        update.effective_message.reply_text("താങ്കളെക്കുറിച്ചുള്ള വിവരങ്ങൾ ഒന്നും ഇതുവരെയും താങ്കൾ ഇതിൽ ചേർത്തിട്ടില്ല !")


@run_async
def set_about_me(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    user_id = message.from_user.id
    text = message.text
    info = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            message.reply_text("താങ്കളുടെ വിവരങ്ങൾ വിജയകരമായി രേഖപ്പെടുത്തിയിരിക്കുന്നു ")
        else:
            message.reply_text(
                "താങ്കളെ കുറിച്ചുള്ള വിവരണം {} അക്ഷരങ്ങളിൽ ഒതുക്കേണ്ടതാണ് ".format(MAX_MESSAGE_LENGTH // 4, len(info[1])))


@run_async
def about_bio(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text("{} ഇതുവരെ അദ്ദേഹത്തെക്കുറിച്ചുള്ള വിവരങ്ങൾ ഒന്നും ചേർത്തിട്ടില്ല !".format(username))
    else:
        update.effective_message.reply_text("നിങ്ങളെക്കുറിചുള്ള നിങ്ങളുടെ വിവരങ്ങൾ ഇതുവരെ ചേർത്തിട്ടില്ല !")


@run_async
def set_about_bio(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    sender = update.effective_user  # type: Optional[User]
    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id
        if user_id == message.from_user.id:
            message.reply_text("താങ്കൾ താങ്കളുടെ തന്നെ വിവരങ്ങൾ മാറ്റാൻ നോക്കുന്നോ...?? അത് പറ്റില്ല.")
            return
        elif user_id == bot.id and sender.id not in SUDO_USERS:
            message.reply_text("എന്റെ വിവരങ്ങൾ മാറ്റാൻ SUDO USERSനു മാത്രമേ സാധിക്കുകയുള്ളു .")
            return

        text = message.text
        bio = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("{} യയെ കുറിച്ചുള്ള വിവരം വിജയകരമായി ശേഖരിച്ചിരുന്നു !".format(repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "നിങ്ങളെക്കുറിച്ചുള്ള വിവരണം {} അക്ഷരത്തിൽ ഒതുക്കേണ്ടതാണ് ! നിങ്ങൾ ഇപ്പോൾ ശ്രമിച്ച അക്ഷരങ്ങളുടെ എണ്ണം  {} ആണ് .".format(
                        MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text("ആരുടെയെങ്കിലും MESSAGEന് REPLY ആയി കൊടുത്താൽ മാത്രമേ അദ്ദേഹത്തിന്റെ വിവരങ്ങൾ ചേർക്കാൻ കഴിയുകയുള്ളു ")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    if bio and me:
        return "<b>About user:</b>\n{me}\n<b>What others say:</b>\n{bio}".format(me=me, bio=bio)
    elif bio:
        return "<b>What others say:</b>\n{bio}\n".format(me=me, bio=bio)
    elif me:
        return "<b>About user:</b>\n{me}""".format(me=me, bio=bio)
    else:
        return ""


__help__ = """
 - /setbio <text>: മറുപടി നൽകുമ്പോൾ മറ്റൊരു ഉപയോക്താവിന്റെ ബയോ സംരക്ഷിക്കും
 - /bio: നിങ്ങളുടെ അല്ലെങ്കിൽ മറ്റൊരു ഉപയോക്താവിന്റെ ബയോ ലഭിക്കും. ഇത് സ്വയം സജ്ജമാക്കാൻ കഴിയില്ല..
 - /setme <text>: നിങ്ങളുടെ വിവരങ്ങൾ സജ്ജമാക്കും
 - /me: നിങ്ങളുടെ അല്ലെങ്കിൽ മറ്റൊരു ഉപയോക്താവിന്റെ വിവരങ്ങൾ ലഭിക്കും
"""

__mod_name__ = "വിവരങ്ങൾ💹"

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio, pass_args=True)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me, pass_args=True)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)
