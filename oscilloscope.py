import time
import math
import lib.rp_devices as devs


class oscilloscope:
    def __init__(self, buffer_size=256, buffer_handler: function = None) -> None:
        self.buffer = []
        self.buffer_size = buffer_size
        self.buffer_handler = buffer_handler
        self.setup()

    def setup(self):
        devs.adc_dma_init()

    def capture(self):
        return devs.adc_capture()
