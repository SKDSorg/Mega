import threading
import time
from datetime import datetime


class ThreadsController:
    def __init__(self, utils, system, bot):
        self.U = utils
        self.S = system
        self.bot = bot
        self.t = {}
        for k in self.S.chats.keys():
            self.t[k] = TimerThread(name=self.S.chats[k]["name"], mega=self.S.chats[k], mega_id=k, bot=self.bot,
                                    enabled=self.S.chats[k]["enabled"], system=self.S, utils=self.U)
            self.t[k].start()

    def start_thread(self, mega_id):
        self.t[str(mega_id)] = TimerThread(name=self.S.chats[str(mega_id)]["name"], mega=self.S.chats[str(mega_id)],
                                           mega_id=mega_id, bot=self.bot, enabled=self.S.chats[str(mega_id)]["enabled"],
                                           system=self.S, utils=self.U)
        self.t[str(mega_id)].start()

    def code_broadcast(self, user, code):
        username = user.first_name
        text = f"Код для повышения пользователя {username} до админа: {code}"
        print(text)
        username, code = f"*{username}*", f"`{code}`"
        text = f"Код для повышения пользователя {username} до админа: {code}"
        for k in self.S.admins.keys():
            if self.S.admins[k]["activated"]:
                self.bot.send_message(int(k), text, parse_mode='markdown')


class TimerThread(threading.Thread):
    def __init__(self, name, mega, mega_id, bot, enabled, system, utils, *args, **kwargs):
        super(TimerThread, self).__init__(*args, **kwargs)
        self.U = utils
        self.name = name
        self.now = datetime.now()
        self.enabled = enabled
        self.m_id = mega_id
        self.m = mega
        self.b = bot
        self.S = system
        self._pause = threading.Event()
        self._kill = False
        if enabled:
            self._pause.set()

    def run(self):
        print(f"Running {self.name} thread.")
        while True:
            self._pause.wait()
            if self._kill:
                print(f"{self.name} thread killed.")
                return
            now = datetime.now()
            st = datetime.strptime(f"{now.day}-{now.month}-{now.year} {self.m['time_op']}", "%d-%m-%Y %H:%M")
            ed = datetime.strptime(f"{now.day}-{now.month}-{now.year} {self.m['time_ed']}", "%d-%m-%Y %H:%M")
            s = (st - now).total_seconds()
            e = (ed - now).total_seconds()
            if 0.0 <= s < 10.0:
                time.sleep(s)
                text = self.U.parse_vars(self.S.get_private_chat(self.m_id), self.m["op_text"])
                self.b.send_message(int(self.m_id), text, parse_mode='HTML')
                continue
            if 0.0 <= e < 10.0:
                time.sleep(e)
                text = self.U.parse_vars(self.S.get_private_chat(self.m_id), self.m["ed_text"])
                self.b.send_message(int(self.m_id), text, parse_mode='HTML')
                continue
            time.sleep(10)

    def kill(self):
        self.S.del_mega(self.m_id)
        self.S.del_chat(self.m_id)
        self._kill = True
        self._pause.clear()

    def pause(self):
        self.S.disable_mega(self.m_id)
        self._pause.clear()

    def resume(self):
        self.S.enable_mega(self.m_id)
        self._pause.set()
