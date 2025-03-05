import time
import ast
import mido

class Player:
    def __init__(self):
        self.raws = None
        self.lines_number = None
        self.score_line = {}
        self.playing = False

    def read_file(self, filename: str):
        f = open(filename, 'r')
        self.raws = f.read().splitlines()
        self.lines_number = len(self.raws)
        f.close()
        return self.raws

    def parse_midi_string(self, s):
        params = dict(param.split('=') for param in s.split()[1:])
        message = mido.Message(type=s.split()[0],**{k: int(v) for k, v in params.items()})
        return message