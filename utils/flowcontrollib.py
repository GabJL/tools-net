from enum import Enum
import json


class Event(Enum):
    RECEIVE_ACK = 1
    RECEIVE_NACK = 2
    TIMEOUT = 3
    SEND_FRAME = 4
    TRANS_FRAME_END = 5
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

    def next_event(self):
        if self.queue is None:
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

        for ev in self.queue:
            if ev["type"] == Event.SEND_FRAME:
                ev["time"] = next_time


class ProtocolError(Exception):
    pass


class Protocol:
    def __init__(self, filename):
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
            if info.get("frames lost", []) is not list:
                raise ProtocolError("The list of frames lost should be a list, even if only one is lost.")
            else:
                for v in info.get("frames lost", []):
                    if v < 1:
                        raise ProtocolError("The lost frames should be numbered as 1, 2...")
            if info.get("acks lost", []) is not list:
                raise ProtocolError("The list of acks lost should be a list, even if only one is lost.")
            else:
                for v in info.get("ack lost", []):
                    if v < 1:
                        raise ProtocolError("The lost acks should be numbered as 1, 2...")

            for k, v in info.items:
                if "time" in k and v is not list and v < 0:
                    raise ProtocolError(f"{k} should be >= 0")

            self.__set_default_values()
            for k, v in info.items:
                self.configuration[k] = v

            self.max_number = 2 ** self.configuration["bit for numbering"]
            if self.configuration["protocol"] == "Stop & Wait":
                self.configuration["bit for numbering"] = 1
                self.sender_window_size = 1
                self.receive_window_size = 1
            elif self.configuration["protocol"] == "Go-Back-N":
                if self.configuration.get("sender window", self.max_number) >= self.max_number:
                    raise ProtocolError("Sender window size invalid")
                self.sender_window_size = self.configuration["sender window"]
                self.receive_window_size = 1
            else:
                if self.configuration.get("sender window", self.max_number) > self.max_number / 2:
                    raise ProtocolError("Sender window size invalid")
                self.sender_window_size = self.configuration["sender window"]
                self.receive_window_size = self.configuration["sender window"]

            self.numbering = []
            self.sender_window = []
            self.receiver_window = []
            for i in range(self.configuration["number of frames"]):
                self.numbering.append(i % self.max_number)
                self.sender_window.append(False)
                self.receiver_window.append(False)

            self.sender_window_start = 0

        except FileNotFoundError:
            raise ProtocolError(f"The file {filename} was not found")
        except ValueError:
            raise ProtocolError(f"Error reading json file {filename}")

    def __set_default_values(self):
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

    def __update_sender_windowd(self, n):
        for i, t in enumerate(self.numbering):
            if t == n and not self.sender_window[i]:
                self.sender_window[i] = True
                return

    def run(self):
        log = []
        for i in range(self.sender_window_size):
            self.queue.add_event(Event.SEND_FRAME, 0, self.numbering[i])

        while True:
            ev = self.queue.next_event()
            if ev is None:
                break
            if ev["type"] == Event.SEND_FRAME:
                next_time = ev["time"] + self.configuration["frame transmission time"]
                self.queue.add_event(Event.TRANS_FRAME_END, next_time, ev["seq_number"])
                log.append({"time": ev["time"], "entity": 'sender', "type": "Start to send Frame",
                            "number": ev["seq_number"]})
                self.queue.move_send_next_event()
            elif ev["type"] == Event.TRANS_FRAME_END:
                self.queue.add_event(Event.TIMEOUT, ev["time"] + self.configuration["timeout"], ev["seq_number"])
                log.append({"time": ev["time"], "entity": 'sender', "type": "Frame completely sent",
                            "number": ev["seq_number"]})
                self.frames_sent += 1
                self.__update_sender_window(ev["seq_number"])
                if ev["seq_number"] in self.configuration["frame lost"]:
                    log.append({"time": ev["time"], "entity": 'sender', "type": "Frame lost",
                                "number": ev["seq_number"]})
                else:
                    self.queue.add_event(Event.RECEIVE_FRAME, ev["time"] + self.configuration["frame propagation time"],
                                         ev["seq_number"])
            elif ev["type"] == Event.TIMEOUT:
                pass
            elif ev["type"] == Event.RECEIVE_FRAME:
                next_time = ev["time"] + self.configuration["processing time"]
                self.queue.add_event(Event.PROC_ACK_TIME, next_time, ev["seq_number"])
                log.append({"time": ev["time"], "receiver": 'sender', "type": "Frame received",
                            "number": ev["seq_number"]})
            elif ev["type"] == Event.PROC_ACK_TIME:
                pass
            elif ev["type"] == Event.TRANS_ACK_END:
                pass
            elif ev["type"] == Event.RECEIVE_ACK:
                pass
            elif ev["type"] == Event.TRANS_NACK_END:
                pass
            elif ev["type"] == Event.RECEIVE_NACK:
                pass
