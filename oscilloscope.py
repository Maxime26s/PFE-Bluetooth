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
    
    def set_channel_2(self,channel_2_state):
        if channel_2_state == "TRUE":
            devs.adc.CS.AINSEL = 0
            devs.adc.CS.RROBIN = 3
        elif channel_2_state == "FALSE":
            devs.adc.CS.AINSEL = 0
            devs.adc.CS.RROBIN = 0
            
    def set_sample_rate(self,sample_rate):
        devs.parameters["xrate"]=int(sample_rate)
        
    def set_number_of_sample(self,number_sample):
        devs.parameters["nsamples"]=int(number_sample)
        