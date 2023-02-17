from machine import UART
from bluetooth import bluetooth
from oscilloscope import oscilloscope
from function_generator import function_generator
import struct
import json


class controller:
    def __init__(self) -> None:
        uart = UART(0, 9600)
        uart.init()
        self.bt = bluetooth(uart)

        settings_oscilloscope = dict()
        settings_oscilloscope["trigger"] = 0
        settings_oscilloscope["base_de_temps"] = 0
        settings_oscilloscope["volt_cell"] = 0
        settings_oscilloscope["auto"] = False
        settings_oscilloscope["pause"] = False

        settings_source = dict()
        settings_source["enabled"] = False
        settings_source["voltage"] = 0
        settings_source["amperage"] = 0

        settings_generateur = dict()
        settings_generateur["enabled"] = False
        settings_generateur["amplitude"] = 0
        settings_generateur["frequence"] = 0

        self.settings = dict()
        self.settings["oscilloscope"] = settings_oscilloscope
        self.settings["source"] = settings_source
        self.settings["generateur"] = settings_generateur

        self.oscilloscope = oscilloscope(
            buffer_handler=self.buffer_handler_json)

        self.generator = function_generator()

    def loop(self):
        while True:
            self.message_handler(self.bt.read_message())

    def get_settings(self):
        return json.dumps(self.settings)

    def set_settings(self, message):
        data = json.loads(message)
        for key in self.settings.keys():
            if key in data:
                self.settings[key] = data[key]
        print(f"NEW SETTINGS: {self.settings}")

    def bytes_to_string(self, message: bytes | bytearray) -> str:
        return message.decode("utf-8")

    def message_handler(self, message):
        if len(message) == 0:
            return

        message = self.bytes_to_string(message)
        if message == "OK+CONN":
            self.bt.is_connected = True
        elif message == "OK+LOST":
            self.bt.is_connected = False
        elif message == "GET+SETTINGS":
            self.bt.write(self.get_settings())
        elif message.startswith("SET+SETTINGS"):
            self.set_settings(message[8:])
        elif message == "CAPTURE":
            adc_buff = self.oscilloscope.capture()
            self.bt.write(json.dumps(adc_buff))
        elif message == "GEN START":
            self.generator.start()
            self.bt.write(self.generator.running)
        elif message == "GEN STOP":
            self.generator.stop()
            self.bt.write(self.generator.running)
        elif message.startswith("GEN SET_WAVE"):
            self.generator.set_wave(message[13:])
            self.bt.write(self.generator.wave.toJSON())
