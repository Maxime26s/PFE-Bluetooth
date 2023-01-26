import time
import math


class oscilloscope():
    def __init__(self, buffer_size=256, buffer_handler: function = None) -> None:
        self.buffer = []
        self.buffer_size = buffer_size
        self.buffer_handler = buffer_handler

    def read(self):
        return math.sin(time.ticks_ms()/1000)

    def read_to_buffer(self):
        data = self.read()
        print(f"DATA: {data}")
        self.buffer.append(data)
        if len(self.buffer) == self.buffer_size:
            self.buffer_handler(self.buffer)
            self.buffer = []
