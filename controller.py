from machine import UART, Pin
from bluetooth import bluetooth
from oscilloscope import oscilloscope
from source import source
from function_generator import function_generator
import struct
import json

class controller:
    def __init__(self) -> None:
        uart = UART(0, 115200)
        uart.init(0, 115200, rx=Pin(17), tx=Pin(16))
        self.bt = bluetooth(uart)

        settings_oscilloscope = dict()
        settings_oscilloscope["enabled"] = False
        settings_oscilloscope["trigger"] = 0
        self.oscilloscope = oscilloscope(settings_oscilloscope)

        settings_source = dict()
        settings_source["enabled"] = False
        settings_source["voltage"] = 0
        self.source = source(settings_source)

        settings_generator = dict()
        settings_generator["enabled"] = False
        self.generator = function_generator(settings_generator)

    def loop(self):
        while True:
            self.message_handler(self.bt.read_message())

    def get_settings(self):
        settings = dict()
        settings["oscilloscope"] = self.oscilloscope.settings
        settings["source"] = self.source.settings
        settings["generator"] = self.generator.settings
        return json.dumps(self.settings)

    def set_settings(self, message):
        # {"oscilloscope":{"enabled":true,"trigger":0.5},"source":{"enabled":true,"voltage":5},"generator":{"enabled":false}}
        data = json.loads(message)

        if "oscilloscope" in data:
            for key in self.data["oscilloscope"].keys():
                if key in self.oscilloscope.settings:
                    self.oscilloscope.settings[key] = data[key]
                    print(f"SET OSCILLOSCOPE {key}: {data[key]}")

        if "source" in data:
            for key in self.data["source"].keys():
                if key in self.source.settings:
                    self.source.settings[key] = data[key]
                    print(f"SET SOURCE {key}: {data[key]}")

        if "generator" in data:
            for key in self.data["generator"].keys():
                if key in self.generator.settings:
                    self.generator.settings[key] = data[key]
                    print(f"SET GENERATOR {key}: {data[key]}")

    def bytes_to_string(self, message: bytes | bytearray) -> str:
        return message.decode("utf-8")

    def message_handler(self, message):
        if len(message) == 0:
            return
        message = self.bytes_to_string(message).strip()
        print(message)

        # AT COMMANDS
        if message == "OK+CONN":
            self.bt.is_connected = True
        elif message == "OK+LOST":
            self.bt.is_connected = False
        # CUSTOM COMMANDS
        elif message == "GET SETTINGS":
            self.bt.write(self.get_settings())
        elif message.startswith("SET SETTINGS"):
            self.set_settings(message[13:])
        elif message == "CAPTURE":
            adc_buff = self.oscilloscope.capture()
            self.bt.write(json.dumps(adc_buff))
        elif message.startswith("SET CHANNEL 2"):          
            self.oscilloscope.set_channel_2(message[14:])
        elif message.startswith("SET SAMPLE RATE"):
            self.oscilloscope.set_sample_rate(message[16:])
        elif message.startswith("SET NUMBER SAMPLE"):
            self.oscilloscope.set_number_of_sample(message[18:])
        # GEN COMMANDS
        if self.message_handler_generator(message):
            return
        
    def message_handler_generator(self, message) -> bool:
        if message == "GEN START":
            self.generator.start()
        elif message == "GEN STOP":
            self.generator.stop()
        elif message.startswith("GEN SET_WAVE"):
            self.generator.set_wave(message[13:])
            self.bt.write("Wave set")
        elif message.startswith("GEN SET_AMP"):
            try:
                self.generator.wave.amplitude = float(message[12:])
                self.bt.write("Wave amplitude set")
            except ValueError as e:
                print("value error",e)
        elif message.startswith("GEN SET_FREQ"):
            try:
                self.generator.wave.frequency = float(message[13:])
                self.bt.write("Wave frequency set")
            except ValueError as e:
                print("value error",e)
        elif message.startswith("GEN SET_OFFSET"):
            try:
                self.generator.wave.offset = float(message[15:])
                self.bt.write("Wave offset set")
            except ValueError as e:
                print("value error",e)
        elif message.startswith("GEN SET_FUNC"):
            try:
                self.generator.set_wave_func(message[13:])
                self.bt.write("Wave func set")
            except ValueError as e:
                print("value error",e)
        elif message.startswith("GEN SET_PARS_RISE"):
            try:
                self.generator.wave.pars[0] = float(message[18:])
                self.bt.write("Wave pars rise set")
            except ValueError as e:
                print("value error",e)
        elif message.startswith("GEN SET_PARS_HIGH"):
            try:
                self.generator.wave.pars[1] = float(message[18:])
                self.bt.write("Wave pars high set")
            except ValueError as e:
                print("value error",e)
        elif message.startswith("GEN SET_PARS_FALL"):
            try:
                self.generator.wave.pars[2] = float(message[18:])
                self.bt.write("Wave pars fall set")
            except ValueError as e:
                print("value error",e)
        else:
            return False

        if message != "GEN START":
            self.generator.start()

        return True
