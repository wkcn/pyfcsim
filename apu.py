from numpy import *
from defines import *

lengthTable = array([
	10, 254, 20, 2, 40, 4, 80, 6, 160, 8, 60, 10, 14, 12, 26, 14,
	12, 16, 24, 18, 48, 20, 96, 22, 192, 24, 72, 26, 16, 28, 32, 30,
], dtype = uint8)

dutyTable = array([
	[0, 1, 0, 0, 0, 0, 0, 0],
	[0, 1, 1, 0, 0, 0, 0, 0],
	[0, 1, 1, 1, 1, 0, 0, 0],
	[1, 0, 0, 1, 1, 1, 1, 1]], dtype = uint8)

triangleTable = array([
	15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0,
	0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], dtype = uint8
)

noiseTable = array([
	4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762, 1016, 2034, 4068], dtype = uint16)

dmcTable = array([
	214, 190, 170, 160, 143, 127, 113, 107, 95, 80, 71, 64, 53, 42, 36, 27], dtype = uint8)

pulseTable = zeros(31, dtype = float32)
tndTable = zeros(203, dtype = float32)

frameCounterRate = CPUFrequency / 240.0

def init():
    for i in range(31):
        pulseTable[i] = 95.52 / (8128.0/ float32(i) + 100)
    for i in range(203): 
        tndTable[i] = 163.67 / (24329.0/float32(i) + 100)

class APU:
    def __init__(self, console):
        self.console = console
        self.channel = float32()
        self.sampleRate = float64()
        self.pulse1 = Pulse() 
        self.pulse2 = Pulse()
        self.Triangle = Triangle()
        self.noise = Noise()
        self.dmc = DMC()
        self.cycle = uint64() 
        self.framePeriod = uint8()
        self.frameValue = uint8()
        self.frameIRQ = False
        self.filterChain = None
        self.noise.shiftRegister = 1
        self.pulse1.channel = 1
        self.pulse2.channel = 2
        self.dmc.cpu = console.CPU

    def Step(self):
        cycle = self.cycle
        self.cycle += uint64(1) 
        cycle2 = apu.cycle
        self.stepTimer()
        f1 = int(float(cycle1) / frameCounterRate)
        f2 = int(float(cycle2) / frameCounterRate)
        if f1 != f2 :
            self.stepFrameCounter()
        s1 = int(float(cycle1) / self.sampleRate)
        s2 = int(float(cycle2) / self.sampleRate)
        if s1 != s2 :
            self.sendSample()

    def sendSample(apu):
        output = apu.filterChain.Step(apu.output())
        # TODO

    def output(apu):
        p1 = apu.pulse1.output()
        p2 = apu.pulse2.output()
        t = apu.triangle.output()
        n = apu.noise.output()
        d = apu.dmc.output()
        pulseOut = pulseTable[p1+p2]
        tndOut = tndTable[3*t+2*n+d]
        return pulseOut + tndOut

    def stepFrameCounter(apu):
        if apu.framePeriod == 4:
            apu.frameValue = (apu.frameValue + uint8(1)) % uint8(4)
            if apu.frameValue in [0, 2]:
                apu.stepEnvelope()
            elif apu.frameValue == 1:
                apu.stepEnvelope()
                apu.stepSweep()
                apu.stepLength()
            elif apu.frameValue == 3:
                apu.stepEnvelope()
                apu.stepSweep()
                apu.stepLength()
                apu.fireIRQ()
        elif apu.framePeriod == 5:
            apu.frameValue = (apu.frameValue + uint8(1)) % uint8(5)
            if apu.frameValue in [1,3]:
                apu.stepEnvelope()
            elif apu.frameValue in [0,2]:
                apu.stepEnvelope()
                apu.stepSweep()
                apu.stepLength()

        def stepTimer(apu):
            if apu.cycle % 2 == 0:
                apu.pulse1.stepTimer()
                apu.pulse2.stepTimer()
                apu.noise.stepTimer()
                apu.dmc.stepTimer()
            apu.triangle.stepTimer()


        def stepEnvelope(apu): 
            apu.pulse1.stepEnvelope()
            apu.pulse2.stepEnvelope()
            apu.triangle.stepCounter()
            apu.noise.stepEnvelope()


        def stepSweep(apu):
            apu.pulse1.stepSweep()
            apu.pulse2.stepSweep()

        def stepLength(apu): 
            apu.pulse1.stepLength()
            apu.pulse2.stepLength()
            apu.triangle.stepLength()
            apu.noise.stepLength()

        def fireIRQ(apu):
            if apu.frameIRQ:
                apu.console.CPU.triggerIRQ()

        def readRegister(apu, address):
            if address == 0x4015:
                return apu.readStatus()
            return uint8(0)

        def writeRegister(apu, address, value):
            if address == 0x4000:
                apu.pulse1.writeControl(value)
            elif address == 0x4001:
                apu.pulse1.writeSweep(value)
            elif address == 0x4002:
                apu.pulse1.writeTimerLow(value)
            elif address == 0x4003:
                apu.pulse1.writeTimerHigh(value)
            elif address == 0x4004:
                apu.pulse2.writeControl(value)
            elif address == 0x4005:
                apu.pulse2.writeSweep(value)
            elif address == 0x4006:
                apu.pulse2.writeTimerLow(value)
            elif address == 0x4007:
                apu.pulse2.writeTimerHigh(value)
            elif address == 0x4008:
                apu.triangle.writeControl(value)
            elif address in [0x4009, 0x4010]:
                apu.dmc.writeControl(value)
            elif address == 0x4011:
                apu.dmc.writeValue(value)
            elif address == 0x4012:
                apu.dmc.writeAddress(value)
            elif address == 0x4013:
                apu.dmc.writeLength(value)
            elif address == 0x400A:
                apu.triangle.writeTimerLow(value)
            elif address == 0x400B:
                apu.triangle.writeTimerHigh(value)
            elif address == 0x400C:
                apu.noise.writeControl(value)
            elif address in [0x400D, 0x400E]:
                apu.noise.writePeriod(value)
            elif address == 0x400F:
                apu.noise.writeLength(value)
            elif address == 0x4015:
                apu.writeControl(value)
            elif address == 0x4017:
                apu.writeFrameCounter(value)

        def readStatus(apu):
            result = uint8(0)
            if apu.pulse1.lengthValue > 0:
                result |= uint8(1)
            if apu.pulse2.lengthValue > 0:
                result |= uint8(2)
            if apu.triangle.lengthValue > 0:
                result |= uint8(4)
            if apu.noise.lengthValue > 0:
                result |= uint8(8)
            if apu.dmc.currentLength > 0:
                result |= uint8(16)
            return result

        def writeControl(apu, value):
            apu.pulse1.enabled = (value&1 == 1)
            apu.pulse2.enabled = (value&2 == 2)
            apu.triangle.enabled = (value&4 == 4)
            apu.noise.enabled = (value&8 == 8)
            apu.dmc.enabled = (value&16 == 16)
            if not apu.pulse1.enabled:
                apu.pulse1.lengthValue = uint8(0)
            if not apu.pulse2.enabled:
                apu.pulse2.lengthValue = uint8(0)
            if not apu.triangle.enabled:
                apu.triangle.lengthValue = uint8(0)
            if not apu.noise.enabled:
                apu.noise.lengthValue = uint8(0)
            if not apu.dmc.enabled:
                apu.dmc.currentLength = uint16(0)
            elif  apu.dmc.currentLength == 0:
                apu.dmc.restart()

        def writeFrameCounter(apu, value):
            apu.framePeriod = uint8(4) + (value>>uint8(7))&uint8(1)
            apu.frameIRQ = ((value>>uint8(6))&uint8(1) == 0)
            if apu.framePeriod == 5:
                apu.stepEnvelope()
                apu.stepSweep()
                apu.stepLength()

class Pulse:
    def __init__(self):
        self.enabled = False
        self.channel = uint8()
        self.lengthEnabled = False
        self.lengthValue = uint8()
        self.timerPeriod = uint16()
        self.timerValue = uint16()
        self.dutyMode   =   uint8()
        self.dutyValue  =   uint8()
        self.sweepReload = False
        self.sweepEnabled = False
        self.sweepNegate     = False
        self.sweepShift      = uint8()
        self.sweepPeriod     = uint8()
        self.sweepValue      = uint8()
        self.envelopeEnabled = False
        self.envelopeLoop    = False
        self.envelopeStart   = False
        self.envelopePeriod  = uint8()
        self.envelopeValue   = uint8()
        self.envelopeVolume  = uint8()
        self.constantVolume  = uint8()

    def Save(p, encoder):
        encoder.Encode(p.enabled)
        encoder.Encode(p.channel)
        encoder.Encode(p.lengthEnabled)
        encoder.Encode(p.lengthValue)
        encoder.Encode(p.timerPeriod)
        encoder.Encode(p.timerValue)
        encoder.Encode(p.dutyMode)
        encoder.Encode(p.dutyValue)
        encoder.Encode(p.sweepReload)
        encoder.Encode(p.sweepEnabled)
        encoder.Encode(p.sweepNegate)
        encoder.Encode(p.sweepShift)
        encoder.Encode(p.sweepPeriod)
        encoder.Encode(p.sweepValue)
        encoder.Encode(p.envelopeEnabled)
        encoder.Encode(p.envelopeLoop)
        encoder.Encode(p.envelopeStart)
        encoder.Encode(p.envelopePeriod)
        encoder.Encode(p.envelopeValue)
        encoder.Encode(p.envelopeVolume)
        encoder.Encode(p.constantVolume)
        return nil

    def Load(p, decoder):
        decoder.Decode(p.enabled)
        decoder.Decode(p.channel)
        decoder.Decode(p.lengthEnabled)
        decoder.Decode(p.lengthValue)
        decoder.Decode(p.timerPeriod)
        decoder.Decode(p.timerValue)
        decoder.Decode(p.dutyMode)
        decoder.Decode(p.dutyValue)
        decoder.Decode(p.sweepReload)
        decoder.Decode(p.sweepEnabled)
        decoder.Decode(p.sweepNegate)
        decoder.Decode(p.sweepShift)
        decoder.Decode(p.sweepPeriod)
        decoder.Decode(p.sweepValue)
        decoder.Decode(p.envelopeEnabled)
        decoder.Decode(p.envelopeLoop)
        decoder.Decode(p.envelopeStart)
        decoder.Decode(p.envelopePeriod)
        decoder.Decode(p.envelopeValue)
        decoder.Decode(p.envelopeVolume)
        decoder.Decode(p.constantVolume)

        def writeControl(p, value):
            p.dutyMode = (value >> uint8(6)) & uint8(3)
            p.lengthEnabled = ((value>>uint8(5))&uint8(1) == 0)
            p.envelopeLoop = ((value>>5)&1 == 1)
            p.envelopeEnabled = ((value>>4)&1 == 0)
            p.envelopePeriod = value & uint8(15)
            p.constantVolume = value & uint8(15)
            p.envelopeStart = True

        def writeSweep(p, value):
            p.sweepEnabled = ((value>>7)&1 == 1)
            p.sweepPeriod = ((value>>uint8(4))&uint8(7) + uint8(1))
            p.sweepNegate = ((value>>3)&1 == 1)
            p.sweepShift = (value & byte(7))
            p.sweepReload = True

        def writeTimerLow(p, value):
            p.timerPeriod = (p.timerPeriod & uint16(0xFF00)) | uint16(value)

        def writeTimerHigh(p, value):
            p.lengthValue = lengthTable[value>>byte(3)]
            p.timerPeriod = (p.timerPeriod & uint16(0x00FF)) | (uint16(value&uint8(7)) << uint16(8))
            p.envelopeStart = true
            p.dutyValue = byte(0)

        def stepTimer(p):
            if p.timerValue == 0:
                p.timerValue = p.timerPeriod
                p.dutyValue = (p.dutyValue + byte(1)) % byte(8)
            else:
                p.timerValue -= uint16(1)

        def stepEnvelope(p):
            if p.envelopeStart:
                p.envelopeVolume = byte(15)
                p.envelopeValue = p.envelopePeriod
                p.envelopeStart = false
            elif p.envelopeValue > 0:
                p.envelopeValue -= byte(1)
            else:
                if p.envelopeVolume > 0:
                    p.envelopeVolume -= byte(1)
                elif p.envelopeLoop:
                    p.envelopeVolume = byte(15)
                p.envelopeValue = p.envelopePeriod

        def stepSweep(p):
            if p.sweepReload:
                if p.sweepEnabled and p.sweepValue == 0: 
                    p.sweep()
                p.sweepValue = p.sweepPeriod
                p.sweepReload = false
            elif p.sweepValue > 0:
                p.sweepValue -= byte(1)
            else:
                if p.sweepEnabled:
                    p.sweep()
                p.sweepValue = p.sweepPeriod

        def stepLength(p):
            if p.lengthEnabled and p.lengthValue > 0:
                p.lengthValue -= byte(1) 

        def sweep(p):
            delta = (p.timerPeriod >> uint16(p.sweepShift))
            if p.sweepNegate:
                p.timerPeriod -= delta
                if p.channel == 1:
                    p.timerPeriod -= uint16(1)
            else:
                p.timerPeriod += delta

        def output(p):
            if not p.enabled:
                return uint8(0)
            if p.lengthValue == 0:
                return uint8(0)
            if dutyTable[p.dutyMode][p.dutyValue] == 0:
                return uint8(0)
            if p.timerPeriod < 8 or p.timerPeriod > 0x7FF:
                return uint8(0)
            if p.envelopeEnabled:
                return p.envelopeVolume
            else:
                return p.constantVolume

// Triangle

type Triangle struct {
	enabled       bool
	lengthEnabled bool
	lengthValue   uint8
	timerPeriod   uint16
	timerValue    uint16
	dutyValue     uint8
	counterPeriod uint8
	counterValue  uint8
	counterReload bool
}

func (t *Triangle) Save(encoder *gob.Encoder) error {
	encoder.Encode(t.enabled)
	encoder.Encode(t.lengthEnabled)
	encoder.Encode(t.lengthValue)
	encoder.Encode(t.timerPeriod)
	encoder.Encode(t.timerValue)
	encoder.Encode(t.dutyValue)
	encoder.Encode(t.counterPeriod)
	encoder.Encode(t.counterValue)
	encoder.Encode(t.counterReload)
	return nil
}

func (t *Triangle) Load(decoder *gob.Decoder) error {
	decoder.Decode(&t.enabled)
	decoder.Decode(&t.lengthEnabled)
	decoder.Decode(&t.lengthValue)
	decoder.Decode(&t.timerPeriod)
	decoder.Decode(&t.timerValue)
	decoder.Decode(&t.dutyValue)
	decoder.Decode(&t.counterPeriod)
	decoder.Decode(&t.counterValue)
	decoder.Decode(&t.counterReload)
	return nil
}

func (t *Triangle) writeControl(value uint8) {
	t.lengthEnabled = (value>>7)&1 == 0
	t.counterPeriod = value & 0x7F
}

func (t *Triangle) writeTimerLow(value uint8) {
	t.timerPeriod = (t.timerPeriod & 0xFF00) | uint16(value)
}

func (t *Triangle) writeTimerHigh(value uint8) {
	t.lengthValue = lengthTable[value>>3]
	t.timerPeriod = (t.timerPeriod & 0x00FF) | (uint16(value&7) << 8)
	t.timerValue = t.timerPeriod
	t.counterReload = true
}

func (t *Triangle) stepTimer() {
	if t.timerValue == 0 {
		t.timerValue = t.timerPeriod
		if t.lengthValue > 0 && t.counterValue > 0 {
			t.dutyValue = (t.dutyValue + 1) % 32
		}
	} else {
		t.timerValue--
	}
}

func (t *Triangle) stepLength() {
	if t.lengthEnabled && t.lengthValue > 0 {
		t.lengthValue--
	}
}

func (t *Triangle) stepCounter() {
	if t.counterReload {
		t.counterValue = t.counterPeriod
	} else if t.counterValue > 0 {
		t.counterValue--
	}
	if t.lengthEnabled {
		t.counterReload = false
	}
}

func (t *Triangle) output() uint8 {
	if !t.enabled {
		return 0
	}
	if t.lengthValue == 0 {
		return 0
	}
	if t.counterValue == 0 {
		return 0
	}
	return triangleTable[t.dutyValue]
}

// Noise

type Noise struct {
	enabled         bool
	mode            bool
	shiftRegister   uint16
	lengthEnabled   bool
	lengthValue     uint8
	timerPeriod     uint16
	timerValue      uint16
	envelopeEnabled bool
	envelopeLoop    bool
	envelopeStart   bool
	envelopePeriod  uint8
	envelopeValue   uint8
	envelopeVolume  uint8
	constantVolume  uint8
}

func (n *Noise) Save(encoder *gob.Encoder) error {
	encoder.Encode(n.enabled)
	encoder.Encode(n.mode)
	encoder.Encode(n.shiftRegister)
	encoder.Encode(n.lengthEnabled)
	encoder.Encode(n.lengthValue)
	encoder.Encode(n.timerPeriod)
	encoder.Encode(n.timerValue)
	encoder.Encode(n.envelopeEnabled)
	encoder.Encode(n.envelopeLoop)
	encoder.Encode(n.envelopeStart)
	encoder.Encode(n.envelopePeriod)
	encoder.Encode(n.envelopeValue)
	encoder.Encode(n.envelopeVolume)
	encoder.Encode(n.constantVolume)
	return nil
}

func (n *Noise) Load(decoder *gob.Decoder) error {
	decoder.Decode(&n.enabled)
	decoder.Decode(&n.mode)
	decoder.Decode(&n.shiftRegister)
	decoder.Decode(&n.lengthEnabled)
	decoder.Decode(&n.lengthValue)
	decoder.Decode(&n.timerPeriod)
	decoder.Decode(&n.timerValue)
	decoder.Decode(&n.envelopeEnabled)
	decoder.Decode(&n.envelopeLoop)
	decoder.Decode(&n.envelopeStart)
	decoder.Decode(&n.envelopePeriod)
	decoder.Decode(&n.envelopeValue)
	decoder.Decode(&n.envelopeVolume)
	decoder.Decode(&n.constantVolume)
	return nil
}

func (n *Noise) writeControl(value uint8) {
	n.lengthEnabled = (value>>5)&1 == 0
	n.envelopeLoop = (value>>5)&1 == 1
	n.envelopeEnabled = (value>>4)&1 == 0
	n.envelopePeriod = value & 15
	n.constantVolume = value & 15
	n.envelopeStart = true
}

func (n *Noise) writePeriod(value uint8) {
	n.mode = value&0x80 == 0x80
	n.timerPeriod = noiseTable[value&0x0F]
}

func (n *Noise) writeLength(value uint8) {
	n.lengthValue = lengthTable[value>>3]
	n.envelopeStart = true
}

func (n *Noise) stepTimer() {
	if n.timerValue == 0 {
		n.timerValue = n.timerPeriod
		var shift uint8
		if n.mode {
			shift = 6
		} else {
			shift = 1
		}
		b1 := n.shiftRegister & 1
		b2 := (n.shiftRegister >> shift) & 1
		n.shiftRegister >>= 1
		n.shiftRegister |= (b1 ^ b2) << 14
	} else {
		n.timerValue--
	}
}

func (n *Noise) stepEnvelope() {
	if n.envelopeStart {
		n.envelopeVolume = 15
		n.envelopeValue = n.envelopePeriod
		n.envelopeStart = false
	} else if n.envelopeValue > 0 {
		n.envelopeValue--
	} else {
		if n.envelopeVolume > 0 {
			n.envelopeVolume--
		} else if n.envelopeLoop {
			n.envelopeVolume = 15
		}
		n.envelopeValue = n.envelopePeriod
	}
}

func (n *Noise) stepLength() {
	if n.lengthEnabled && n.lengthValue > 0 {
		n.lengthValue--
	}
}

func (n *Noise) output() uint8 {
	if !n.enabled {
		return 0
	}
	if n.lengthValue == 0 {
		return 0
	}
	if n.shiftRegister&1 == 1 {
		return 0
	}
	if n.envelopeEnabled {
		return n.envelopeVolume
	} else {
		return n.constantVolume
	}
}

// DMC

type DMC struct {
	cpu            *CPU
	enabled        bool
	value          uint8
	sampleAddress  uint16
	sampleLength   uint16
	currentAddress uint16
	currentLength  uint16
	shiftRegister  uint8
	bitCount       uint8
	tickPeriod     uint8
	tickValue      uint8
	loop           bool
	irq            bool
}

func (d *DMC) Save(encoder *gob.Encoder) error {
	encoder.Encode(d.enabled)
	encoder.Encode(d.value)
	encoder.Encode(d.sampleAddress)
	encoder.Encode(d.sampleLength)
	encoder.Encode(d.currentAddress)
	encoder.Encode(d.currentLength)
	encoder.Encode(d.shiftRegister)
	encoder.Encode(d.bitCount)
	encoder.Encode(d.tickPeriod)
	encoder.Encode(d.tickValue)
	encoder.Encode(d.loop)
	encoder.Encode(d.irq)
	return nil
}

func (d *DMC) Load(decoder *gob.Decoder) error {
	decoder.Decode(&d.enabled)
	decoder.Decode(&d.value)
	decoder.Decode(&d.sampleAddress)
	decoder.Decode(&d.sampleLength)
	decoder.Decode(&d.currentAddress)
	decoder.Decode(&d.currentLength)
	decoder.Decode(&d.shiftRegister)
	decoder.Decode(&d.bitCount)
	decoder.Decode(&d.tickPeriod)
	decoder.Decode(&d.tickValue)
	decoder.Decode(&d.loop)
	decoder.Decode(&d.irq)
	return nil
}

func (d *DMC) writeControl(value uint8) {
	d.irq = value&0x80 == 0x80
	d.loop = value&0x40 == 0x40
	d.tickPeriod = dmcTable[value&0x0F]
}

func (d *DMC) writeValue(value uint8) {
	d.value = value & 0x7F
}

func (d *DMC) writeAddress(value uint8) {
	// Sample address = %11AAAAAA.AA000000
	d.sampleAddress = 0xC000 | (uint16(value) << 6)
}

func (d *DMC) writeLength(value uint8) {
	// Sample length = %0000LLLL.LLLL0001
	d.sampleLength = (uint16(value) << 4) | 1
}

func (d *DMC) restart() {
	d.currentAddress = d.sampleAddress
	d.currentLength = d.sampleLength
}

func (d *DMC) stepTimer() {
	if !d.enabled {
		return
	}
	d.stepReader()
	if d.tickValue == 0 {
		d.tickValue = d.tickPeriod
		d.stepShifter()
	} else {
		d.tickValue--
	}
}

func (d *DMC) stepReader() {
	if d.currentLength > 0 && d.bitCount == 0 {
		d.cpu.stall += 4
		d.shiftRegister = d.cpu.Read(d.currentAddress)
		d.bitCount = 8
		d.currentAddress++
		if d.currentAddress == 0 {
			d.currentAddress = 0x8000
		}
		d.currentLength--
		if d.currentLength == 0 && d.loop {
			d.restart()
		}
	}
}

func (d *DMC) stepShifter() {
	if d.bitCount == 0 {
		return
	}
	if d.shiftRegister&1 == 1 {
		if d.value <= 125 {
			d.value += 2
		}
	} else {
		if d.value >= 2 {
			d.value -= 2
		}
	}
	d.shiftRegister >>= 1
	d.bitCount--
}

func (d *DMC) output() uint8 {
	return d.value
}
