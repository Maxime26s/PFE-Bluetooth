import time
import math
import lib.rp_devices as devs


class oscilloscope:
    def __init__(self, settings: dict) -> None:
        self.settings = settings
        self.setup()

    def setup(self):
        devs.adc_dma_init()

    def capture(self):
        return devs.adc_capture()
