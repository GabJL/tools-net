from enum import IntEnum
import json


class Event(IntEnum):
    RECEIVE_ACK = 1
    RECEIVE_NACK = 2
    TRANS_FRAME_END = 3
    TIMEOUT = 4
    SEND_FRAME = 5
    TRANS_ACK_END = 6
    RECEIVE_FRAME = 7
    PROC_ACK_TIME = 8
    TRANS_NACK_END = 9


class EventQueue:
    def __init__(self):
        self.queue = []

    def add_event(self, event_type, time, seq_number):
        ev = {"type": event_type, "time": time, "seq_number": seq_number}
        self.queue.append(ev)

    def add_event_front(self, event_type, time, seq_number):
        ev = {"type": event_type, "time": time, "seq_number": seq_number}
        self.queue = [ev] + self.queue

    def next_event(self):
        if self.queue is None or len(self.queue) == 0:
            return None

        pos_ev = 0
        for x in range(1, len(self.queue)):
            if self.queue[pos_ev]["time"] > self.queue[x]["time"]:
                pos_ev = x
            elif self.queue[pos_ev]["time"] == self.queue[x]["time"]:
                if self.queue[pos_ev]["type"] > self.queue[x]["type"]:
                    pos_ev = x

        ev = self.queue[pos_ev]
        del self.queue[pos_ev]
        return ev

    def remove_timeout(self, seq_number=-1):
        for i, ev in enumerate(self.queue):
            if ev["type"] == Event.TIMEOUT and (seq_number == -1 or ev["seq_number"] == seq_number):
                del self.queue[i]

    def move_send_next_event(self):
        next_time = -1
        for ev in self.queue:
            if ev["type"] == Event.TRANS_FRAME_END:
                next_time = ev["time"]
        if next_time == -1:
            possible_states = [Event.TIMEOUT, Event.RECEIVE_ACK, Event.RECEIVE_NACK]
            for ev in self.queue:
                if ev["type"] in possible_states and (next_time == -1 or next_time < ev["time"]):
                    next_time = ev["time"]

        for ev in self.queue:
            if ev["type"] == Event.SEND_FRAME:
                ev["time"] = next_time

    def set_send_current_time(self, t):
        for ev in self.queue:
            if ev["type"] == Event.SEND_FRAME:
                ev["time"] = t


class ProtocolError(Exception):
    pass


class Protocol:
    def __init__(self, filename):
        self.configuration = dict()
        self.configuration["frame transmission time"] = 1
        self.configuration["frame propagation time"] = 1
        self.configuration["processing time"] = 0.5
        self.configuration["ack transmission time"] = 0.5
        self.configuration["ack propagation time"] = 1
        self.configuration["timeout"] = 12
        self.frames_sent = 0
        self.acks_sent = 0
        self.queue = EventQueue()
        self.sender_window_start = 0
        self.log = None
        valid_protocols = ["Stop & Wait", "Go-Back-N", "Selective Repeat"]
        try:
            with open(filename) as f:
                info = json.load(f)

            if info.get("protocol", "") not in valid_protocols:
                raise ProtocolError(f"The selected protocol ({info.get('protocol')}) is no valid.")
            if info.get("bit for numbering", 0) < 1:
                raise ProtocolError(f"The number of bits for numbering the frames should be greater than 1.")
            if info.get("number of frames", 0) < 1:
                raise ProtocolError(f"The number of frames to be sent should be greater than 1.")
            if type(info.get("frames lost", [])) is not list:
                raise ProtocolError("The list of frames lost should be a list, even if only one frame is lost.")
            else:
                for v in info.get("frames lost", []):
                    if v < 1:
                        raise ProtocolError("The lost frames should be numbered as 1, 2...")
            if type(info.get("acks lost", [])) is not list:
                raise ProtocolError("The list of acks lost should be a list, even if only one is lost.")
            else:
                for v in info.get("ack lost", []):
                    if v < 1:
                        raise ProtocolError("The lost acks should be numbered as 1, 2...")

            for k, v in info.items():
                if "time" in k and type(v) is not list and v < 0:
                    raise ProtocolError(f"{k} should be >= 0")

            for k, v in info.items():
                self.configuration[k] = v

            self.max_number = 2 ** self.configuration["bit for numbering"]
            if self.configuration["protocol"] == "Stop & Wait":
                self.configuration["bit for numbering"] = 1
                self.sender_window_size = 1
                self.receiver_window_size = 1
                self.max_number = 2
            elif self.configuration["protocol"] == "Go-Back-N":
                if self.configuration.get("sender window", self.max_number) >= self.max_number:
                    raise ProtocolError("Sender window size invalid")
                self.sender_window_size = self.configuration["sender window"]
                self.receiver_window_size = 1
            else:
                if self.configuration.get("sender window", self.max_number) > self.max_number / 2:
                    raise ProtocolError("Sender window size invalid")
                self.sender_window_size = self.configuration["sender window"]
                self.receiver_window_size = self.configuration["sender window"]

            self.numbering = []
            self.sender_window = []
            self.receiver_window = []
            for i in range(self.configuration["number of frames"]):
                self.numbering.append(i % self.max_number)
                self.sender_window.append(False)
                self.receiver_window.append(False)

        except FileNotFoundError:
            raise ProtocolError(f"The file {filename} was not found")
        except ValueError:
            raise ProtocolError(f"Error reading json file {filename}")

    def __update_sender_window(self, n, v):
        for i in range(self.sender_window_size):
            if self.numbering[i + self.sender_window_start] == n:
                self.sender_window[i + self.sender_window_start] = v
                return

    def __is_in_receiver_window(self, n):
        first = None
        is_first = None
        for i, v in enumerate(self.numbering):
            if not self.receiver_window[i] and first is None:
                first = i
            if first is not None and (i - first) < self.receiver_window_size and v == n:
                is_first = i == first
        if is_first is None:
            return False, False, self.numbering[first-1] if first is not None else self.numbering[-1], 0
        else:
            last = 0
            for i, v in enumerate(self.numbering):
                if self.receiver_window[i]:
                    last = i
            if last < first:
                last = first
            return True, is_first, self.numbering[first], self.numbering[last]

    def __update_receiver_window(self, n):
        for i, v in enumerate(self.numbering):
            if v == n and not self.receiver_window[i]:
                self.receiver_window[i] = True
                return

    def __get_position(self, n):
        for i in range(self.sender_window_start, self.sender_window_start+self.sender_window_size):
            if self.numbering[i] == n:
                return i
        return None

    def __sender_window_to_str(self):
        res = "["
        for i in range(self.sender_window_start, self.sender_window_start+self.sender_window_size):
            if i < len(self.sender_window):
                if self.sender_window[i]:
                    res += f" ({self.numbering[i]})"
                else:
                    res += f" {self.numbering[i]}"
        res += " ]"
        return res

    def __receiver_window_to_str(self):
        res = "["
        first = None
        for i, v in enumerate(self.numbering):
            if not self.receiver_window[i] and first is None:
                first = i
            if first is not None and (i - first) < self.receiver_window_size:
                if self.receiver_window[i]:
                    res += f" ({self.numbering[i]})"
                else:
                    res += f" {self.numbering[i]}"
        res += " ]"
        return res

    def __next(self, i):
        return (i+1) % self.max_number

    def run(self):
        log = []
        for i in range(len(self.numbering)):
            self.queue.add_event(Event.SEND_FRAME, 0, self.numbering[i])

        log.append({"time": 0, "entity": 'sender', "type": "Initial State", "number": -1,
                    "window": self.__sender_window_to_str()})
        log.append({"time": 0, "entity": 'receiver', "type": "Initial State", "number": -1,
                    "window": self.__receiver_window_to_str()})

        while True:
            ev = self.queue.next_event()
            if ev is not None:
                if ev["type"] == Event.SEND_FRAME:
                    if ev["seq_number"] in self.numbering[
                                       self.sender_window_start:self.sender_window_size + self.sender_window_start]:
                        next_time = ev["time"] + self.configuration["frame transmission time"]
                        self.queue.add_event(Event.TRANS_FRAME_END, next_time, ev["seq_number"])
                        log.append({"time": ev["time"], "entity": 'sender', "type": "Start to send Frame",
                                    "number": ev["seq_number"], "window": self.__sender_window_to_str()})
                    else:
                        self.queue.add_event_front(ev["type"], ev["time"], ev["seq_number"])
                    self.queue.move_send_next_event()
                elif ev["type"] == Event.TRANS_FRAME_END:
                    self.queue.add_event(Event.TIMEOUT, ev["time"] + self.configuration["timeout"], ev["seq_number"])
                    self.frames_sent += 1
                    self.__update_sender_window(ev["seq_number"], True)
                    log.append({"time": ev["time"], "entity": 'sender', "type": "Frame completely sent",
                                "number": ev["seq_number"], "window": self.__sender_window_to_str()})
                    if self.frames_sent in self.configuration["frames lost"]:
                        log.append({"time": ev["time"], "entity": 'sender', "type": "Frame lost",
                                    "number": ev["seq_number"], "window": self.__sender_window_to_str()})
                    else:
                        self.queue.add_event(Event.RECEIVE_FRAME,
                                             ev["time"] + self.configuration["frame propagation time"],
                                             ev["seq_number"])
                elif ev["type"] == Event.TIMEOUT:
                    if self.configuration["protocol"] == "Go-Back-N":
                        for i in range(self.sender_window_start + self.sender_window_size-1,
                                       self.sender_window_start-1, -1):
                            if self.sender_window[i]:
                                self.queue.add_event_front(Event.SEND_FRAME, ev["time"], self.numbering[i])
                                self.queue.remove_timeout(self.numbering[i])
                                self.__update_sender_window(self.numbering[i], False)
                    else:
                        self.queue.add_event_front(Event.SEND_FRAME, ev["time"], ev["seq_number"])
                        self.__update_sender_window(ev["seq_number"], False)
                    log.append({"time": ev["time"], "entity": 'sender', "type": "Timeout", "number": ev["seq_number"],
                                "window": self.__sender_window_to_str()})
                elif ev["type"] == Event.RECEIVE_FRAME:
                    next_time = ev["time"] + self.configuration["processing time"]
                    self.queue.add_event(Event.PROC_ACK_TIME, next_time, ev["seq_number"])
                    log.append({"time": ev["time"], "entity": 'receiver', "type": "Frame received",
                                "number": ev["seq_number"], "window": self.__receiver_window_to_str()})
                elif ev["type"] == Event.PROC_ACK_TIME:
                    is_in, first, val_ini, val_end = self.__is_in_receiver_window(ev["seq_number"])
                    if is_in:
                        next_time = ev["time"] + self.configuration["ack transmission time"]
                        self.__update_receiver_window(ev["seq_number"])
                        if first:
                            self.queue.add_event(Event.TRANS_ACK_END, next_time, val_end)
                            log.append({"time": ev["time"], "entity": 'receiver', "type": "Start to send ACK",
                                        "number": self.__next(val_end), "window": self.__receiver_window_to_str()})
                        else:
                            self.queue.add_event(Event.TRANS_NACK_END, next_time, val_ini)
                            log.append({"time": ev["time"], "entity": 'receiver', "type": "Start to send NACK",
                                        "number": val_ini, "window": self.__receiver_window_to_str()})
                    else:
                        next_time = ev["time"] + self.configuration["ack transmission time"]
                        self.queue.add_event(Event.TRANS_ACK_END, next_time, val_ini)
                        log.append({"time": ev["time"], "entity": 'receiver', "type": "Start to resend ACK",
                                    "number": self.__next(val_ini), "window": self.__receiver_window_to_str()})

                elif ev["type"] == Event.TRANS_ACK_END:
                    next_time = ev["time"] + self.configuration["ack propagation time"]
                    self.acks_sent += 1
                    if self.acks_sent in self.configuration["acks lost"]:
                        log.append({"time": ev["time"], "entity": 'receiver', "type": "ACK lost",
                                    "number": self.__next(ev["seq_number"]), "window": self.__receiver_window_to_str()})
                    else:
                        self.queue.add_event(Event.RECEIVE_ACK, next_time, ev["seq_number"])
                        log.append({"time": ev["time"], "entity": 'receiver', "type": "ACK sent",
                                    "number": self.__next(ev["seq_number"]), "window": self.__receiver_window_to_str()})
                elif ev["type"] == Event.TRANS_NACK_END:
                    next_time = ev["time"] + self.configuration["ack propagation time"]
                    self.acks_sent += 1
                    if self.acks_sent in self.configuration["acks lost"]:
                        log.append({"time": ev["time"], "entity": 'receiver', "type": "NACK lost",
                                    "number": ev["seq_number"], "window": self.__receiver_window_to_str()})
                    else:
                        self.queue.add_event(Event.RECEIVE_NACK, next_time, ev["seq_number"])
                        log.append({"time": ev["time"], "entity": 'receiver', "type": "NACK sent",
                                    "number": ev["seq_number"], "window": self.__receiver_window_to_str()})
                elif ev["type"] == Event.RECEIVE_ACK:
                    pos = self.__get_position(ev["seq_number"])
                    if pos is not None:
                        for i in range(self.sender_window_start, pos+1):
                            self.queue.remove_timeout(self.numbering[i])
                        self.sender_window_start = pos+1
                        self.queue.set_send_current_time(ev["time"])
                    log.append({"time": ev["time"], "entity": 'sender', "type": "ACK received",
                                "number": self.__next(ev["seq_number"]), "window": self.__sender_window_to_str()})

                elif ev["type"] == Event.RECEIVE_NACK:
                    self.queue.remove_timeout(ev["seq_number"])
                    self.queue.add_event_front(Event.SEND_FRAME, ev["time"], ev["seq_number"])
                    log.append({"time": ev["time"], "entity": 'sender', "type": "NACK received - retransmit",
                                "number": ev["seq_number"], "window": self.__sender_window_to_str()})
            else:
                break
        self.log = log

    def write(self):
        if not self.log:
            return

        print('{0:<6} {1:<20} {2:<30} {3:>30} {4:<20}'.format("time", "Sender Window", "Sender Action",
                                                              "Receiver Activon", "Receiver Window"))
        for e in self.log:
            if 'NACK' in e['type']:
                seq = f" (NACK{str(e['number'])})"
            elif 'ACK' in e['type']:
                seq = f" (ACK{str(e['number'])})"
            else:
                if e['number'] == -1:
                    seq = ''
                else:
                    seq = f" (T{str(e['number'])})"

            if e['entity'] == 'sender':
                print(f"{e['time']:<6} {e['window']:<20} {e['type'] + seq:<30}")
            else:
                print(f"{e['time']:<6} {'':<20} {'':<30} {e['type'] + seq:>30} {e['window']:<20} ")
