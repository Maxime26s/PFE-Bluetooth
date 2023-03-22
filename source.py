import machine
import utime
import ustruct
import sys

###############################################################################
# Constants

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

def writein(spi,cs,data):
        # Write 1 byte to the specified register.
        cs.value(0)
        spi.write(data)
        print(data)
        cs.value(1)
       
# Wait before taking measurements
    # Définir la plage de valeurs pour le troisième argument
#start_val = 0
#end_val = 255

# Boucle pour incrémenter le troisième argument et appeler la fonction writein()
spi = machine.SPI(0,
                  baudrate=100000,
                  polarity=1,
                  phase=1,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(18),
                  mosi=machine.Pin(19))
cs = machine.Pin(17, machine.Pin.OUT)

writein (spi,cs,b'\x00')
utime.sleep(5)
    
    



    
    
