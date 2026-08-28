import math
import random
import struct
import wave

SAMPLE_RATE = 44100


def make_thrust(path, duration=0.5, volume=0.35):
    n = int(SAMPLE_RATE * duration)
    raw = [random.uniform(-1, 1) for _ in range(n)]
    # heavy smoothing turns hiss into a duller engine-roar texture
    window = 6
    smoothed = []
    for i in range(n):
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        smoothed.append(sum(raw[lo:hi]) / (hi - lo))

    fade_len = int(SAMPLE_RATE * 0.015)
    frames = bytearray()
    for i in range(n):
        t = i / SAMPLE_RATE
        # low rocket-engine rumble under the filtered noise
        rumble = math.sin(2 * math.pi * 70 * t) * 0.4 + math.sin(2 * math.pi * 110 * t) * 0.2
        fade = 1.0
        if i < fade_len:
            fade = i / fade_len
        elif i > n - fade_len:
            fade = (n - i) / fade_len
        value = (smoothed[i] * 0.6 + rumble) * volume * fade
        value = max(-1.0, min(1.0, value))
        frames += struct.pack('<h', int(value * 32767))

    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(bytes(frames))


if __name__ == '__main__':
    make_thrust('sounds/thrust.wav')
    print('wrote sounds/thrust.wav')
