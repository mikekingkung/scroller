import math
import struct
import wave

SAMPLE_RATE = 44100


def make_laser(path, duration=0.22, start_freq=1600, end_freq=180, volume=0.5):
    n_samples = int(SAMPLE_RATE * duration)
    frames = bytearray()
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        progress = i / n_samples
        # exponential downward frequency sweep - classic "pew" laser
        freq = start_freq * ((end_freq / start_freq) ** progress)
        # slight square-ish tone for an 8-bit arcade feel
        phase = 2 * math.pi * freq * t
        sample = math.sin(phase) + 0.3 * math.sin(3 * phase)
        # exponential amplitude decay envelope
        envelope = (1 - progress) ** 2
        value = sample * envelope * volume
        value = max(-1.0, min(1.0, value))
        frames += struct.pack('<h', int(value * 32767))

    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(bytes(frames))


if __name__ == '__main__':
    make_laser('sounds/laser.wav')
    print('wrote sounds/laser.wav')
