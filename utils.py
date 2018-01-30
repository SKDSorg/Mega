import re
from datetime import datetime


class Utils:
    def __init__(self, system, bot, me):
        self.S = system
        self.B = bot
        self.d_len = 20
        self.l_len = 50
        self.me = me

    def check_context(self, m, ctype):
        if ctype == "admin_add":
            return m.reply_to_message is not None and \
                   self.S.activate_admin(m.from_user.id, m.reply_to_message.message_id, m.text) and \
                   self.S.get_context(m.chat.id, m.reply_to_message.message_id) == ctype
        else:
            return m.reply_to_message is not None and \
                   self.S.get_context(m.chat.id, m.reply_to_message.message_id) == ctype

    def check_connect(self, c):
        data = c.data.split(" ")
        if len(data) == 2 and data[0] == "mconn":
            if self.S.get_mega(data[1]) is not None:
                return True
        return False

    def check_approve(self, c):
        data = c.data.split(" ")
        if len(data) == 3 and (data[0] == "nappr" or data[0] == "yappr"):
            if self.S.get_mega_chat_id(data[1], data[2]) is not None:
                return True
        return False

    def pattern_detect(self, m):
        pattern = self.S.get_pattern(m.chat.id)
        if m.text is not None:
            if m.text[:5].lower() == "бронь":
                return m.text
        if pattern is not None:
            pattern = re.compile(pattern % (self.d_len, self.l_len))
            return pattern.findall(m.text)
        return False

    def mega_check(self, m):
        mega = self.S.get_mega(m.chat.id)
        if self.pattern_detect(m) is not None and mega is not None or self.S.get_mega_chat_id(m.chat.id, m.message_id):
            now = datetime.now()
            st = datetime.strptime(f"{now.day}-{now.month}-{now.year} {mega['time_op']}", "%d-%m-%Y %H:%M")
            ed = datetime.strptime(f"{now.day}-{now.month}-{now.year} {mega['time_ed']}", "%d-%m-%Y %H:%M")
            if st <= now <= ed:
                return True
        return False

    def isprivategroup(self, func):
        def w(m):
            if self.S.get_mega_chat(m.chat.id) is not None:
                func(m)
            else:
                self.B.reply_to(m, "Эту команду можно использовать только в группе кураторов меги.")

        return w

    def isnotmega(self, func):
        def w(m):
            if self.S.get_mega(m.chat.id) is None:
                func(m)
            else:
                self.B.reply_to(m, "Эту команду необходимо использовать в группе кураторов меги.")

        return w

    def grouptype(self, gtype):
        def w1(func):
            def w2(m):
                if m.chat.type == gtype:
                    func(m)
                else:
                    if gtype == "supergroup":
                        self.B.reply_to(m, "Эту команду можно использовать только в супергруппе.")
                    if gtype == "private":
                        self.B.reply_to(m, "Эту команду можно использовать только в приватном чате с ботом.")

            return w2

        return w1

    def isadmin(self, callback=False):
        def w1(func):
            def w2(m):
                if self.S.get_admin(m.from_user.id) is not None:
                    func(m)
                else:
                    if callback:
                        self.B.answer_callback_query(callback_query_id=m.id, show_alert=False,
                                                     text="Это действие может выполнить только администратор.")
                    else:
                        self.B.reply_to(m, "Это действие может выполнить только администратор.")

            return w2

        return w1

    def del_context(self, func):
        def w(m):
            func(m)
            self.S.del_context(m.chat.id, m.reply_to_message.message_id)

        return w

    def issupergroup(self, func):
        def w(m):
            r = self.B.get_chat(m.chat.id).wait()
            if r.type == "supergroup":
                func(m)
            else:
                self.B.reply_to(m, "Эту команду можно использовать только в супергруппе.")

        return w

    def isbotadmin(self, func):
        def w(m):
            r = self.B.get_chat_administrators(m.chat.id).wait()
            error_text = ""
            for user in r:
                if user.user.id == self.me.id:

                    # Optional. Restricted only. True, if user may add web page previews
                    # to his messages, implies can_send_media_messages
                    # if user.can_add_web_page_previews is None or not True:
                    #     error_text += "• Добавление веб-превью\n"

                    # Optional. Administrators only. True, if the bot is allowed to edit
                    # administrator privileges of that user
                    # if user.can_be_edited is None or not True:
                    #     error_text += ""

                    # Optional. Administrators only. True, if the administrator can change
                    # the chat title, photo and other settings
                    if user.can_change_info is None or not True:
                        error_text += "• Редактирование информации чата\n"

                    # Optional. Administrators only. True, if the administrator can delete
                    # messages of other users
                    if user.can_delete_messages is None or not True:
                        error_text += "• Удаление сообщений\n"

                    # Optional. Administrators only. True, if the administrator can edit messages
                    # of other users and can pin messages, channels only
                    # if user.can_edit_messages is None or not True:
                    #     error_text += "• Редактирование сообщений\n"

                    # Optional. Administrators only. True, if the administrator can invite new
                    # users to the chat
                    # if user.can_invite_users is None or not True:
                    #     error_text += "• Приглашать пользователей\n"

                    # Optional. Administrators only. True, if the administrator can pin
                    # messages, supergroups only
                    if user.can_pin_messages is None or not True:
                        error_text += "• Закрепление сообщений\n"

                    # Optional. Administrators only. True, if the administrator can post
                    # in the channel, channels only
                    # if user.can_post_messages is None or not True:
                    #     error_text += ""

                    # Optional. Administrators only. True, if the administrator can
                    # add new administrators with a subset of his own privileges or
                    # demote administrators that he has promoted, directly
                    # or indirectly (promoted by administrators that were appointed by the user)
                    # if user.can_promote_members is None or not True:
                    #     error_text += ""

                    # Optional. Administrators only. True, if the administrator can
                    # restrict, ban or unban chat members
                    if user.can_restrict_members is None or not True:
                        error_text += "• Бан, мут пользователей\n"

                    # Optional. Restricted only. True, if the user can send audios, documents,
                    # photos, videos, video notes and voice notes, implies can_send_messages
                    # if user.can_send_media_messages is None or not True:
                    #     error_text += "• Отправка медиа-сообщений\n"

                    # Optional. Restricted only. True, if the user can send text messages,
                    # contacts, locations and venues
                    # if user.can_send_messages is None or not True:
                    #     error_text += "• Отправка сообщений\n"

                    # Optional. Restricted only. True, if the user can send animations, games,
                    # stickers and use inline bots, implies can_send_media_messages
                    # if user.can_send_other_messages is None or not True:
                    #     error_text += "• Отправка стикеров, гифок\n"

                    if len(error_text) != 0:
                        self.B.reply_to(m, f"Боту необходимо предоставить разрешения:\n{error_text}")
                        break

                    func(m)
                    return
            self.B.reply_to(m, "Бот должен быть администратором в этом чате.")

        return w

    def add_context(self, arg):
        def w1(func):
            def w2(m):
                r = func(m)
                if r is not None:
                    self.S.add_context(r.chat.id, r.message_id, arg)

            return w2

        return w1

    def parse_vars(self, pchat_id, text):
        mega = self.S.get_mega(self.S.get_mega_chat(pchat_id))
        text = text.replace('%CHANNEL_LIST%', f"<code>СПИСОК КАНАЛОВ</code>")
        text = text.replace('%MEGA_NAME%', f"{mega['name']}")
        text = text.replace('%TIME_END%', f"{mega['time_ed']}")
        return text

    @staticmethod
    def to_html(msg):
        text = msg.text
        tlen = 0

        link_text_regex = "[^]]+"
        url_regex = "http[s]?://[^)]+"
        md_link_regex = '\[({0})]\(\s*({1})\s*\)'.format(link_text_regex, url_regex)

        if msg.entities is not None:
            for entity in msg.entities:
                ln = entity.length
                off_tlen = entity.offset + tlen
                if entity.type == "bold":
                    text = f"{text[:off_tlen]}<b>{text[off_tlen:off_tlen+ln]}</b>" \
                           f"{text[off_tlen+ln:]}"
                    tlen += 7
                if entity.type == "italic":
                    text = f"{text[:off_tlen]}<i>{text[off_tlen:off_tlen+ln]}</i>" \
                           f"{text[off_tlen+ln:]}"
                    tlen += 7
                if entity.type == "code":
                    text = f"{text[:off_tlen]}<code>{text[off_tlen:off_tlen+ln]}</code>" \
                           f"{text[off_tlen+ln:]}"
                    tlen += 13

        for link_text, link in re.findall(md_link_regex, text):
            text = text.replace(f"[{link_text}]({link})", f"<a href='{link}'>{link_text}</a>")

        return text
