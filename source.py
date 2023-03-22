import machine
import utime
import ustruct
import sys

class source:
    def __init__(self, settings: dict) -> None:
        # Assign chip select (CS) pin (and start it high)
        # Initialize SPI
        spi = machine.SPI(0,
            baudrate=100000,
            polarity=1,
            phase=1,
            bits=8,
            firstbit=machine.SPI.MSB,
            sck=machine.Pin(18),
            mosi=machine.Pin(19))
        cs = machine.Pin(17, machine.Pin.OUT)
        self.settings = settings

    def set_voltage(self,spi,cs,data):
        # Write 1 byte to the specified register.
        cs.value(0)
        spi.write(data)
        print(data)
        cs.value(1)
