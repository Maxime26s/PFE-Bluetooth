import gc
import array
from machine import Pin, mem32
from rp2 import PIO, StateMachine, asm_pio
from array import array
from math import pi, sin, floor
from uctypes import addressof

fclock = 125000000  # clock frequency of the pico
nbit_dac = 12
sampword=2
maxnword=2048

DMA_BASE = 0x50000000
CH2_READ_ADDR = DMA_BASE+0x080
CH2_WRITE_ADDR = DMA_BASE+0x084
CH2_TRANS_COUNT = DMA_BASE+0x088
CH2_CTRL_TRIG = DMA_BASE+0x08c
CH2_AL1_CTRL = DMA_BASE+0x090
CH3_READ_ADDR = DMA_BASE+0x0c0
CH3_WRITE_ADDR = DMA_BASE+0x0c4
CH3_TRANS_COUNT = DMA_BASE+0x0c8
CH3_CTRL_TRIG = DMA_BASE+0x0cc
CH3_AL1_CTRL = DMA_BASE+0x0d0

PIO0_BASE = 0x50200000
PIO0_TXF0 = PIO0_BASE+0x10
PIO0_SM0_CLKDIV = PIO0_BASE+0xc8

# state machine that just pushes bytes to the pins


@asm_pio(out_init=(PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH, PIO.OUT_HIGH),
         out_shiftdir=PIO.SHIFT_RIGHT, autopull=True, pull_thresh=24)
def stream():
    out(pins, 12)


sm = StateMachine(0, stream, freq=125000000, out_base=Pin(0))
sm.active(1)

# 2-channel chained DMA. channel 0 does the transfer, channel 1 reconfigures
p = array('I', [0])  # global 1-element array


def startDMA(ar, nword):
    # first disable the DMAs to prevent corruption while writing
    mem32[CH2_AL1_CTRL] = 0
    mem32[CH3_AL1_CTRL] = 0
    # setup first DMA which does the actual transfer
    mem32[CH2_READ_ADDR] = addressof(ar)
    print(addressof(ar))
    mem32[CH2_WRITE_ADDR] = PIO0_TXF0
    mem32[CH2_TRANS_COUNT] = nword
    IRQ_QUIET = 0x1  # do not generate an interrupt
    TREQ_SEL = 0x00  # wait for PIO0_TX0
    CHAIN_TO = 3  # start channel 1 when done
    RING_SEL = 0
    RING_SIZE = 0  # no wrapping
    INCR_WRITE = 0  # for write to array
    INCR_READ = 1  # for read from array
    DATA_SIZE = 2  # 32-bit word transfer
    HIGH_PRIORITY = 1
    EN = 1
    CTRL2 = (IRQ_QUIET << 21) | (TREQ_SEL << 15) | (CHAIN_TO << 11) | (RING_SEL << 10) | (RING_SIZE << 9) | (
        INCR_WRITE << 5) | (INCR_READ << 4) | (DATA_SIZE << 2) | (HIGH_PRIORITY << 1) | (EN << 0)
    mem32[CH2_AL1_CTRL] = CTRL2
    # setup second DMA which reconfigures the first channel
    p[0] = addressof(ar)
    mem32[CH3_READ_ADDR] = addressof(p)
    print(addressof(p))
    mem32[CH3_WRITE_ADDR] = CH2_READ_ADDR
    mem32[CH3_TRANS_COUNT] = 1
    IRQ_QUIET = 0x1  # do not generate an interrupt
    TREQ_SEL = 0x3f  # no pacing
    CHAIN_TO = 2  # start channel 0 when done
    RING_SEL = 0
    RING_SIZE = 0  # no wrapping
    INCR_WRITE = 0  # single write
    INCR_READ = 0  # single read
    DATA_SIZE = 2  # 32-bit word transfer
    HIGH_PRIORITY = 1
    EN = 1
    CTRL3 = (IRQ_QUIET << 21) | (TREQ_SEL << 15) | (CHAIN_TO << 11) | (RING_SEL << 10) | (RING_SIZE << 9) | (
        INCR_WRITE << 5) | (INCR_READ << 4) | (DATA_SIZE << 2) | (HIGH_PRIORITY << 1) | (EN << 0)
    mem32[CH3_CTRL_TRIG] = CTRL3
    print("ok")


def setupwave(buf, f, w):
    gc.collect()
    # required clock division for maximum buffer size
    div = fclock/(f*maxnword*sampword)
    if div < 2.0:  # can't speed up clock, duplicate wave instead
        dup = int(2.0/div)
        nword = int((maxnword*div*dup/2.0+0.5))
        clkdiv = 2.0
    else:  # stick with integer clock division only
        clkdiv = int(div)+2.0
        nword = int(maxnword*div/clkdiv+0.5)
        dup = 1
    nsamp=nword*sampword

    # fill the buffer
    for iword in range(nword):
        word=0
        for i in range(sampword):
            isamp=iword*sampword+i
            val=max(0,min((1<<12)-1,int((1<<12)*(0.5+0.5*eval(w,dup*(isamp+0.5)/nsamp)))))
            word=word+(val<<(i*(nbit_dac)))
        buf[iword*4+0]=(word&(255<< 0))>> 0
        buf[iword*4+1]=(word&(255<< 8))>> 8
        buf[iword*4+2]=(word&(255<<16))>>16
        buf[iword*4+3]=(word&(255<<24))>>24
    # set the clock divider
    print(clkdiv)
    clkdiv_int = min(int(clkdiv), 65535)
    clkdiv_frac = 0  # fractional clock division results in jitter
    mem32[PIO0_SM0_CLKDIV] = (clkdiv_int << 16) | (clkdiv_frac << 8)

    # start DMA
    startDMA(buf, nword)
    gc.collect()

# evaluate the content of a wave


def eval(w, x):
    m, s, p = 1.0, 0.0, 0.0
    if 'phasemod' in w.__dict__:
        p = eval(w.phasemod, x)
    if 'mult' in w.__dict__:
        m = eval(w.mult, x)
    if 'sum' in w.__dict__:
        s = eval(w.sum, x)
    x = x*w.replicate-w.phase-p
    x = x-floor(x)  # reduce x to 0.0-1.0 range
    v = w.func(x, w.pars)
    v = v*w.amplitude*m
    v = v+w.offset+s
    return v

# some common waveforms. combine with sum,mult,phasemod


def sine(x, pars):
    return sin(x*2*pi)


def pulse(x, pars):  # risetime,uptime,falltime
    if x < pars[0]:
        return x/pars[0]
    if x < pars[0]+pars[1]:
        return 1.0
    if x < pars[0]+pars[1]+pars[2]:
        return 1.0-(x-pars[0]-pars[1])/pars[2]
    return 0.0


# make buffers for the waveform.
# large buffers give better results but are slower to fill
maxnsamp = 4096  # must be a multiple of 4. miximum size is 65536
wavbuf = {}
wavbuf[0] = bytearray(maxnword*4)
wavbuf[1] = bytearray(maxnword*4)
ibuf = 0


class wave:
    def __init__(self, amplitude, offset, frequency, func, pars):
        self.amplitude = amplitude
        self.offset = offset
        self.frequency = frequency
        self.func = func
        self.pars = pars
        self.phase = 0.0
        self.replicate = 1.0


class function_generator:
    def __init__(self, settings: dict) -> None:
        self.settings = settings
        self.wave = None

        self.set_wave("SQUARE")
        self.start()

    def start(self):
        setupwave(wavbuf[ibuf], self.wave.frequency, self.wave)

    def stop(self):
        self.set_wave("NONE")

    def set_wave(self, type):
        if type == "SINE":
            self.wave = wave(0.05, 0.2, 20000, sine, [0.0, 0.0, 0.0]) #max amplitude de 0.3 ...
        elif type == "SQUARE":
            self.wave = wave(0.5, 0.0, 1000, pulse, [0.0, 0.5, 0.0])
        elif type == "TRIANGLE":
            self.wave = wave(1.0, -0.5, 20000, pulse, [0.5, 0.0, 0.5])
        elif type == "SAW":
            self.wave = wave(0.5, 0.0, 20000, pulse, [1.0, 0.0, 0.0])
        elif type == "NONE":
            self.wave = wave(0.0, 0.1, 1, pulse, [0.0, 0.0, 0.0])
        else:
            return

    def set_wave_type(self, type):
        if type == "SINE":
            self.wave.func = sine
            self.wave.pars = [0.0, 0.0, 0.0]
        elif type == "SQUARE":
            self.wave.func = pulse
            self.wave.pars = [0.0, 0.5, 0.0]
        elif type == "TRIANGLE":
            self.wave.func = pulse
            self.wave.pars = [0.5, 0.0, 0.5]
        elif type == "SAW":
            self.wave.func = pulse
            self.wave.pars = [1.0, 0.0, 0.0]
        elif type == "NONE":
            self.wave.func = pulse
            self.wave.pars = [0.0, 0.0, 0.0]
        else:
            return

    def set_wave_func(self, func_name):
        if func_name == "SINE":
            self.wave.func = sine
        elif func_name == "PULSE":
            self.wave.func = pulse
        else:
            return
        
    def get_wave_func(self, func_name):
        if func_name == "PULSE":
            return pulse
        else:
            return sine
        
    def new_wave(self, message):
        parts = message.split()
        amp = float(parts[0])
        freq = float(parts[1])
        offset = float(parts[2])
        func_type = parts[3]
        func = self.get_wave_func(func_type)
        rise = float(parts[4])
        high = float(parts[5])
        fall = float(parts[6])
        
        self.wave = wave(amp, offset, freq, func, [rise, high, fall])
        print(amp, freq, offset, func_type, rise, high, fall)
        
if __name__ == "__main__":
    wave = wave(0.5, 0.0, 0.5, pulse, [0.0, 0.5, 0.0])
    print("Free memory before setupwave:", gc.mem_free())
    setupwave(wavbuf[ibuf], wave.frequency, wave)
    print("Free memory after setupwave:", gc.mem_free())
