import time

import telebot
from strings import strings_default as txt
from system import System
from telebot import types
from threads import ThreadsController
from utils import Utils

S = System()

bot = telebot.AsyncTeleBot(S.API_key, num_threads=S.bot_threads)

U = Utils(S, bot, bot.get_me().wait())
T = ThreadsController(U, S, bot)


@bot.callback_query_handler(func=lambda c: U.check_connect(c))
@U.isadmin(True)
def f(c):
    mega_id = c.data.split(" ")[1]
    S.connect_mega(mega_id, c.message.chat.id)
    T.start_thread(mega_id)
    bot.answer_callback_query(callback_query_id=c.id, show_alert=False, text=txt["mega_connect_success_query"])
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                          text=txt["mega_connect_success"].replace("%MEGA_NAME%", S.get_mega(mega_id)['name']),
                          parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: U.check_approve(c))
def f(c):
    mega_id = c.data.split(" ")[1]
    msg_id = c.data.split(" ")[2]
    if c.data.split(" ")[0] == "yappr":
        r = S.approve_link(mega_id, msg_id)
        if r:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text=txt["decline_link"],
                                              callback_data=f"nappr {mega_id} {msg_id}"))
            bot.answer_callback_query(callback_query_id=c.id, show_alert=False, text=txt["link_approve_text"])
            bot.edit_message_reply_markup(chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=kb)
    if c.data.split(" ")[0] == "nappr":
        r = S.disapprove_link(mega_id, msg_id)
        if r:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text=txt["approve_link"],
                                              callback_data=f"yappr {mega_id} {msg_id}"))
            bot.answer_callback_query(callback_query_id=c.id, show_alert=False, text=txt["link_decline_text"])
            bot.edit_message_reply_markup(chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=kb)
    mega_list = S.build_mega_list(c.message.chat.id)
    if mega_list is not None:
        mchat_id = S.get_mega_chat(c.message.chat.id)
        if mchat_id is not None:
            mega = S.get_mega(mchat_id)
            if mega is not None:
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton(text=txt["approve_mega"],
                                                  callback_data=f"sendmega {mchat_id}"))
                msg_text = mega["mega_text"].replace("%CHANNEL_LIST%", mega_list)
                bot.edit_message_text(chat_id=c.message.chat.id, message_id=S.get_mega_id(c.message.chat.id),
                                      text=msg_text, parse_mode='HTML', reply_markup=kb, disable_web_page_preview=True)


@bot.message_handler(commands=['ping'])
def f(m):
    bot.send_message(m.chat.id, str(m)).wait()


@bot.message_handler(commands=['info'])
@U.isprivategroup
def f(m):
    mega = S.get_mega(S.get_mega_chat(m.chat.id))
    if mega is not None:
        info_text = f"<b>НАЗВАНИЕ:</b> <i>{mega['name']}</i>\n" \
                    f"<b>ОТКРЫТИЕ:</b> <code>{mega['time_op']}</code>\n" \
                    f"<b>ЗАКРЫТИЕ:</b> <code>{mega['time_ed']}</code>\n" \
                    f"<b>АКТИВНА:</b> <i>{'Да' if mega['enabled'] else 'Нет'}</i>\n" \
                    f"<b>ФОРМАТ ЗАЯВОК:</b>\n<code>{mega['pattern']}</code>\n" \
                    f"<b>ФОРМА ОТКРЫТИЯ:</b>\n\n{mega['op_text']}\n\n" \
                    f"<b>ФОРМА МЕГИ:</b>\n\n{mega['mega_text']}\n\n" \
                    f"<b>ФОРМА ЗАКРЫТИЯ:</b>\n\n{mega['ed_text']}"
        info_text = U.parse_vars(m.chat.id, info_text)
        bot.send_message(m.chat.id, info_text, parse_mode='HTML', disable_web_page_preview=True).wait()


@bot.message_handler(commands=['admin_add'])
@U.grouptype("private")
@U.add_context("admin_add")
def f(m):
    user = S.get_admin(m.from_user.id)
    if user is not None and user["activated"]:
        bot.reply_to(m, txt["already_admin"])
        return None
    uuid = S.get_uuid()
    T.code_broadcast(m.from_user, uuid)
    msg = bot.reply_to(m, txt["add_admin"])
    S.add_admin(m.from_user.id, f"{msg.wait().message_id}-{uuid}")
    return msg.wait()


@bot.message_handler(commands=['add'])
@U.isadmin()
@U.issupergroup
@U.isbotadmin
def f(m):
    mega = S.get_mega(m.chat.id)
    if mega is not None:
        bot.reply_to(m, txt["mega_exists"])
        return
    msg = bot.reply_to(m, txt["add_mega"].replace("%MEGA_NAME%", m.chat.title), parse_mode='HTML')
    S.add_mega(m.chat.id, m.chat.title)
    return msg.wait()


@bot.message_handler(commands=['connect'])
@U.isadmin()
@U.isbotadmin
@U.isnotmega
def f(m):
    kb = types.InlineKeyboardMarkup()
    lst = S.get_free_megas()
    if lst is None:
        bot.reply_to(m, "Нет свободных мег.", reply_markup=kb)
    else:
        for mega in lst:
            kb.add(types.InlineKeyboardButton(text=mega["name"], callback_data=f"mconn {mega['id']}"))
        bot.reply_to(m, txt["mega_choose_connect"], reply_markup=kb)


@bot.message_handler(commands=['enable'], func=lambda m: S.get_mega_chat(m.chat.id) is not None)
@U.isprivategroup
def f(m):
    T.t[S.get_mega_chat(m.chat.id)].resume()
    bot.reply_to(m, txt["mega_resumed"], parse_mode='markdown')


@bot.message_handler(commands=['disable'], func=lambda m: S.get_mega_chat(m.chat.id) is not None)
@U.isprivategroup
def f(m):
    T.t[S.get_mega_chat(m.chat.id)].pause()
    bot.reply_to(m, txt["mega_paused"], parse_mode='markdown')


@bot.message_handler(commands=['delete'], func=lambda m: S.get_mega(m.chat.id) is not None)
@U.isadmin()
def f(m):
    msg = "Мега удалена."
    if m.chat.id in T.t:
        T.t[m.chat.id].kill()
    else:
        if not S.del_mega(m.chat.id) and not S.del_chat(m.chat.id):
            msg = "Эта группа не была зарегистрирована как мега."
    bot.reply_to(m, msg, parse_mode='markdown')


@bot.message_handler(commands=['text'], func=lambda m: S.get_mega_chat(m.chat.id) is not None)
@U.isprivategroup
@U.add_context("text")
def f(m):
    msg = bot.send_message(m.chat.id, "set mega text", parse_mode='markdown')
    return msg.wait()


@bot.message_handler(commands=['op'], func=lambda m: S.get_mega_chat(m.chat.id) is not None)
@U.isprivategroup
@U.add_context("op")
def f(m):
    msg = bot.send_message(m.chat.id, txt["set_op_text"], parse_mode='markdown')
    return msg.wait()


@bot.message_handler(commands=['ed'], func=lambda m: S.get_mega_chat(m.chat.id) is not None)
@U.isprivategroup
@U.add_context("ed")
def f(m):
    msg = bot.send_message(m.chat.id, txt["set_ed_text"], parse_mode='markdown')
    return msg.wait()


@bot.message_handler(commands=['time'], func=lambda m: S.get_mega_chat(m.chat.id) is not None)
@U.isprivategroup
@U.add_context("time")
def f(m):
    msg = bot.send_message(m.chat.id, txt["set_time_text"], parse_mode='markdown')
    return msg.wait()


@bot.message_handler(content_types=['text'], func=lambda m: U.mega_check(m))
@bot.edited_message_handler(content_types=['text'], func=lambda m: U.mega_check(m))
def f(m):
    pchat_id = S.get_private_chat(m.chat.id)
    isnew, deleted, changed, added = S.mega_msg_construct(m.chat.id, m.message_id, U.pattern_detect(m))
    if isnew and len(added) > 0:
        mega = S.get_mega(m.chat.id)
        mg = bot.send_message(pchat_id, mega["mega_text"], parse_mode='HTML', disable_web_page_preview=True).wait()
        if S.set_mega_msg(m.chat.id, mg.message_id):
            bot.pin_chat_message(pchat_id, mg.message_id)
    print(f"Added:\n{added}\nChanged:\n{changed}\nDeleted:\n{deleted}")
    for a in added:
        link = a["link"]
        kb = types.InlineKeyboardMarkup()
        msg_text = f"<a href='{a['link']}'>{a['text']}</a>"
        t = bot.send_message(pchat_id, msg_text, parse_mode='HTML', disable_web_page_preview=True).wait()
        kb.add(types.InlineKeyboardButton(text=txt["approve_link"], callback_data=f"yappr {m.chat.id} {t.message_id}"))
        bot.edit_message_reply_markup(chat_id=t.chat.id, message_id=t.message_id, reply_markup=kb)
        S.mega_link_msg(m.chat.id, link, t.message_id)
    for c in changed:
        kb = types.InlineKeyboardMarkup()
        msg_text = f"<a href='{c['link']}'>{c['text']}</a>"
        S.disapprove_link(m.chat.id, c['id'])
        kb.add(types.InlineKeyboardButton(text=txt["approve_link"], callback_data=f"yappr {m.chat.id} {c['id']}"))
        bot.edit_message_text(chat_id=pchat_id, message_id=c["id"], text=msg_text, reply_markup=kb,
                              disable_web_page_preview=True, parse_mode='HTML')

        mega_list = S.build_mega_list(pchat_id)
        if mega_list is not None:
            mchat_id = S.get_mega_chat(pchat_id)
            if mchat_id is not None:
                mega = S.get_mega(mchat_id)
                if mega is not None:
                    kb = types.InlineKeyboardMarkup()
                    kb.add(types.InlineKeyboardButton(text=txt["approve_mega"],
                                                      callback_data=f"sendmega {m.chat.id}"))
                    msg_text = mega["mega_text"].replace("%CHANNEL_LIST%", mega_list)
                    bot.edit_message_text(chat_id=pchat_id, message_id=S.get_mega_id(pchat_id),
                                          text=msg_text, reply_markup=kb, parse_mode='HTML',
                                          disable_web_page_preview=True)


@bot.message_handler(content_types=['text'], func=lambda m: U.check_context(m, "admin_add"))
@U.del_context
def f(m):
    bot.reply_to(m, txt["admin_add_success"])


@bot.message_handler(content_types=['text'], func=lambda m: U.check_context(m, "add"))
@U.del_context
def f(m):
    bot.reply_to(m, txt["mega_add_success"])


@bot.message_handler(content_types=['text'], func=lambda m: U.check_context(m, "text"))
@U.del_context
def f(m):
    text = U.to_html(m)
    r = S.set_mega_text(S.get_mega_chat(m.chat.id), text)
    if r:
        text = f"<b>НОВАЯ ФОРМА МЕГИ:</b>\n\n{text}"
        text = U.parse_vars(m.chat.id, text)
        bot.reply_to(m, text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        bot.reply_to(m, "Failed!")


@bot.message_handler(content_types=['text'], func=lambda m: U.check_context(m, "op"))
@U.del_context
def f(m):
    text = U.to_html(m)
    r = S.set_op(S.get_mega_chat(m.chat.id), text)
    if r:
        text = f"<b>НОВАЯ ФОРМА ОТКРЫТИЯ МЕГИ:</b>\n\n{text}"
        text = U.parse_vars(m.chat.id, text)
        bot.reply_to(m, text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        bot.reply_to(m, "Failed!")


@bot.message_handler(content_types=['text'], func=lambda m: U.check_context(m, "ed"))
@U.del_context
def f(m):
    text = U.to_html(m)
    r = S.set_ed(S.get_mega_chat(m.chat.id), text)
    if r:
        text = f"<b>НОВАЯ ФОРМА ЗАКРЫТИЯ МЕГИ:</b>\n\n{text}"
        text = U.parse_vars(m.chat.id, text)
        bot.reply_to(m, text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        bot.reply_to(m, "Failed!")


@bot.message_handler(content_types=['text'], func=lambda m: U.check_context(m, "time"))
@U.del_context
def f(m):
    r = S.set_time(S.get_mega_chat(m.chat.id), m.text)
    if r:
        mega = S.get_mega(S.get_mega_chat(m.chat.id))
        if mega is not None:
            info_text = f"<b>ОТКРЫТИЕ:</b> <code>{mega['time_op']}</code>\n" \
                        f"<b>ЗАКРЫТИЕ:</b> <code>{mega['time_ed']}</code>\n"
            bot.reply_to(m, info_text, parse_mode='HTML')
    else:
        bot.reply_to(m, "Failed!")


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except KeyboardInterrupt:
            exit()
        except Exception as e:
            print(e)
            time.sleep(15)
            continue
