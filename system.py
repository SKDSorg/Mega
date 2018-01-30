import collections
import json
import os
import uuid

from strings import strings_default as txt


class System:
    def __init__(self, base_dir="data/", admins_file="admins.json", chats_file="chats.json",
                 settings_file="settings.json", context_file="context.json", megas_file="megas.json"):
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        self.__admins_path = os.path.join(base_dir, admins_file)
        self.__chats_path = os.path.join(base_dir, chats_file)
        self.__settings_path = os.path.join(base_dir, settings_file)
        self.__context_path = os.path.join(base_dir, context_file)
        self.__megas_path = os.path.join(base_dir, megas_file)

        self.admins = self.load_from_file(self.__admins_path) if self.check_file(self.__admins_path) else None
        self.chats = self.load_from_file(self.__chats_path) if self.check_file(self.__chats_path) else None
        self.settings = self.load_from_file(self.__settings_path) if self.check_file(self.__settings_path) else None
        self.context = self.load_from_file(self.__context_path) if self.check_file(self.__context_path) else None
        self.megas = self.load_from_file(self.__megas_path) if self.check_file(self.__megas_path) else None

        self.admins = {} if self.admins is None else self.admins
        self.chats = {} if self.chats is None else self.chats
        self.settings = {} if self.settings is None else self.settings
        self.context = {} if self.context is None else self.context
        self.megas = {} if self.megas is None else self.megas

        if "API_key" not in self.settings.keys():
            self.API_key = input(txt["API_key_request"])
            self.settings["API_key"] = self.API_key
        else:
            self.API_key = self.settings["API_key"]

        if "bot_threads" not in self.settings.keys():
            self.bot_threads = 2
            self.settings["bot_threads"] = self.bot_threads
        else:
            self.bot_threads = self.settings["bot_threads"]

        self.write_to_file(self.__admins_path, self.admins)
        self.write_to_file(self.__chats_path, self.chats)
        self.write_to_file(self.__settings_path, self.settings)
        self.write_to_file(self.__context_path, self.context)
        self.write_to_file(self.__megas_path, self.megas)

    def add_admin(self, user_id, code):
        self.admins[str(user_id)] = {"activated": False, "code": f"{str(user_id)}-{code}"}
        self.write_to_file(self.__admins_path, self.admins)
        return

    def activate_admin(self, user_id, message_id, code):
        if str(user_id) not in self.admins.keys() or self.admins[str(user_id)]["activated"] is True:
            return False
        cd = self.admins[str(user_id)]["code"].split("-")
        if cd[0] == str(user_id) and cd[1] == str(message_id) and cd[2] == code:
            self.admins[str(user_id)]["activated"] = True
            del self.admins[str(user_id)]["code"]
            self.write_to_file(self.__admins_path, self.admins)
            return True
        return False

    def enable_mega(self, mega_id):
        if str(mega_id) in self.chats:
            self.chats[str(mega_id)]["enabled"] = True
            self.write_to_file(self.__chats_path, self.chats)
            return True
        return False

    def disable_mega(self, mega_id):
        if str(mega_id) in self.chats:
            self.chats[str(mega_id)]["enabled"] = False
            self.write_to_file(self.__chats_path, self.chats)
            return True
        return False

    def get_admin(self, user_id):
        if str(user_id) in self.admins and self.admins[str(user_id)]["activated"]:
            return self.admins[str(user_id)]
        return None

    def get_free_megas(self):
        lst = [{"name": self.chats[k]["name"], "id": k} for k in self.chats.keys() if self.chats[k]["group"] is None]
        if len(lst) > 0:
            return lst
        return None

    def close_mega(self, mega_id):
        if str(mega_id) in self.megas:
            self.megas[str(mega_id)]["open"] = False
            self.write_to_file(self.__megas_path, self.megas)
            return True
        return False

    def del_mega(self, mega_id):
        if str(mega_id) in self.megas:
            del self.megas[str(mega_id)]
            self.write_to_file(self.__megas_path, self.megas)
            return True
        return False

    def del_chat(self, mega_id):
        if str(mega_id) in self.chats:
            del self.chats[str(mega_id)]
            self.write_to_file(self.__chats_path, self.chats)
            return True
        return False

    def mega_link_msg(self, mega_id, link, message_id):
        self.megas[str(mega_id)]["list"][link]["chat_id"] = str(message_id)
        self.write_to_file(self.__megas_path, self.megas)

    def build_mega(self, mega_id):
        pass

    def set_mega_msg(self, mega_id, msg_id):
        if str(mega_id) in self.megas:
            self.megas[str(mega_id)]["mega_msg"] = msg_id
            return True
        return False

    def get_mega_id(self, pchat_id):
        mchat_id = self.get_mega_chat(pchat_id)
        if mchat_id is not None:
            if str(mchat_id) in self.megas:
                return self.megas[str(mchat_id)]["mega_msg"]
        return None

    def build_mega_list(self, pchat_id):
        mchat_id = self.get_mega_chat(pchat_id)
        if mchat_id is not None:
            if mchat_id in self.megas:
                result = ""
                temparr = [{"id": self.megas[mchat_id]["list"][i]["msg_id"],
                            "text": self.megas[mchat_id]["list"][i]["text"],
                            "link": self.megas[mchat_id]["list"][i]["link"]}
                           for i in self.megas[mchat_id]["list"].keys()
                           if self.megas[mchat_id]["list"][i]["approved"]]
                if len(temparr) is 0:
                    return "%CHANNEL_LIST%\n"
                newarr = sorted(temparr, key=lambda x: x["id"])
                for link in newarr:
                    # result += f"[{link['text']}]({link['link']})\n"
                    result += f"<a href='{link['link']}'>{link['text']}</a>\n"
                return result
        return None

    def mega_msg_construct(self, mega_id, orig_message_id, matches):
        isnew = False
        if str(mega_id) not in self.megas:
            isnew = True
            self.megas[str(mega_id)] = {
                "mega_msg": None,
                "list": collections.OrderedDict()
            }

        new_list = collections.OrderedDict()

        for match in matches:
            link = match.split("](")[1][:-1]
            link_text = match.split("](")[0][1:]
            new_list[link] = {
                "text": link_text,
                "link": link,
                "msg_id": str(orig_message_id),
                "approved": False
            }

        added = []
        changed = []

        for k in new_list.keys():
            if k in self.megas[str(mega_id)]["list"].keys():
                if new_list[k]["text"] != self.megas[str(mega_id)]["list"][k]["text"]:
                    changed.append({"id": int(self.megas[str(mega_id)]["list"][k]["chat_id"]),
                                    "text": new_list[k]["text"],
                                    "link": self.megas[str(mega_id)]["list"][k]["link"]})
            else:
                self.megas[str(mega_id)]["list"][k] = {}
                added.append(new_list[k])
            for n in new_list[k].keys():
                self.megas[str(mega_id)]["list"][k][n] = new_list[k][n]

        comp_dict = collections.OrderedDict()

        for k in self.megas[str(mega_id)]["list"].keys():
            if self.megas[str(mega_id)]["list"][k]["msg_id"] == str(orig_message_id):
                comp_dict[k] = self.megas[str(mega_id)]["list"][k]

        deleted = []

        for k in comp_dict.keys():
            if k not in new_list.keys():
                deleted.append({"id": int(self.megas[str(mega_id)]["list"][k]["chat_id"]),
                                "text": self.megas[str(mega_id)]["list"][k]["text"]})
                del self.megas[str(mega_id)]["list"][k]

        self.write_to_file(self.__megas_path, self.megas)

        return isnew, deleted, changed, added

    def connect_mega(self, mega_id, mega_chat_id):
        if str(mega_id) in self.chats:
            self.chats[str(mega_id)]["group"] = str(mega_chat_id)
            self.write_to_file(self.__chats_path, self.chats)
            return True
        return False

    def approve_link(self, mega_id, message_id):
        if str(mega_id) in self.megas:
            for link in self.megas[str(mega_id)]["list"].keys():
                if self.megas[str(mega_id)]["list"][link]["chat_id"] == str(message_id):
                    self.megas[str(mega_id)]["list"][link]["approved"] = True
                    self.write_to_file(self.__megas_path, self.megas)
                    return True
        return False

    def disapprove_link(self, mega_id, message_id):
        if str(mega_id) in self.megas:
            for link in self.megas[str(mega_id)]["list"].keys():
                if self.megas[str(mega_id)]["list"][link]["chat_id"] == str(message_id):
                    self.megas[str(mega_id)]["list"][link]["approved"] = False
                    self.write_to_file(self.__megas_path, self.megas)
                    return True
        return False

    def set_mega_text(self, mega_id, text):
        if str(mega_id) in self.chats:
            self.chats[str(mega_id)]["mega_text"] = text
            self.write_to_file(self.__chats_path, self.chats)
            return True
        return False

    def set_op(self, mega_id, text):
        if str(mega_id) in self.chats:
            self.chats[str(mega_id)]["op_text"] = text
            self.write_to_file(self.__chats_path, self.chats)
            return True
        return False

    def set_ed(self, mega_id, text):
        if str(mega_id) in self.chats:
            self.chats[str(mega_id)]["ed_text"] = text
            self.write_to_file(self.__chats_path, self.chats)
            return True
        return False

    def set_time(self, mega_id, text):
        time = text.split("-")
        if str(mega_id) in self.chats:
            self.chats[str(mega_id)]["time_op"] = time[0]
            self.chats[str(mega_id)]["time_ed"] = time[1]
            self.write_to_file(self.__chats_path, self.chats)
            return True
        return False

    def get_mega(self, mega_chat_id):
        if str(mega_chat_id) in self.chats.keys():
            return self.chats[str(mega_chat_id)]
        return None

    def get_mega_chat_id(self, mega_id, message_id):
        if str(mega_id) in self.megas:
            for k in self.megas[str(mega_id)]["list"].keys():
                if self.megas[str(mega_id)]["list"][k]["chat_id"] == str(message_id):
                    return True
        return False

    def add_mega(self, mega_chat_id, mega_name):
        if str(mega_chat_id) in self.chats.keys() and self.chats[str(mega_chat_id)]["group"] is not None:
            return False
        self.chats[str(mega_chat_id)] = {
            "group": None,
            "name": mega_name,
            "enabled": False,
            "pattern": "\[[^)(\][]{1,%s}\]\(https://t\.me/[A-z/0-9]{1,%s}\)",
            "mega_text": txt["default_mega_text"],
            "op_text": txt["default_op_text"],
            "ed_text": txt["default_ed_text"],
            "time_op": "12:00",
            "time_ed": "20:00"
        }
        self.write_to_file(self.__chats_path, self.chats)
        return True

    def get_mega_chat(self, private_chat_id):
        for k in self.chats.keys():
            if self.chats[k]["group"] == str(private_chat_id):
                return k
        return None

    def get_private_chat(self, mega_chat_id):
        if str(mega_chat_id) not in self.chats.keys():
            return None
        return int(self.chats[str(mega_chat_id)]["group"])

    def get_pattern(self, mega_id):
        if str(mega_id) in self.chats.keys():
            return self.chats[str(mega_id)]["pattern"]
        return None

    def add_context(self, chat_id, message_id, mtype):
        self.context[f"{str(chat_id)}-{str(message_id)}"] = mtype
        self.write_to_file(self.__context_path, self.context)

    def del_context(self, chat_id, message_id):
        if f"{str(chat_id)}-{str(message_id)}" in self.context.keys():
            del self.context[f"{str(chat_id)}-{str(message_id)}"]
            self.write_to_file(self.__context_path, self.context)

    def get_context(self, chat_id, message_id):
        if f"{str(chat_id)}-{str(message_id)}" in self.context.keys():
            return self.context[f"{str(chat_id)}-{str(message_id)}"]
        return None

    @staticmethod
    def get_uuid():
        return str(uuid.uuid4())[:8]

    @staticmethod
    def check_file(filename):
        try:
            open(filename, 'r')
        except IOError:
            open(filename, 'w')
            return False
        return True

    @staticmethod
    def write_to_file(path, obj):
        with open(path, 'w+', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False)

    @staticmethod
    def load_from_file(path):
        try:
            return json.loads(open(path, 'r', encoding='utf-8').read())
        except ValueError:
            return None
