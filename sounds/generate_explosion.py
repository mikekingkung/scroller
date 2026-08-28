import random
import struct
import wave

SAMPLE_RATE = 44100


def make_explosion(path, duration=0.4, volume=0.6):
    n = int(SAMPLE_RATE * duration)
    raw = [random.uniform(-1, 1) for _ in range(n)]
    # crude 5-tap smoothing to soften harsh white noise into a duller "boom"
    smoothed = []
    for i in range(n):
        lo = max(0, i - 3)
        hi = min(n, i + 4)
        smoothed.append(sum(raw[lo:hi]) / (hi - lo))

    frames = bytearray()
    for i in range(n):
        progress = i / n
        envelope = (1 - progress) ** 3  # fast attack, quick decay
        value = smoothed[i] * envelope * volume
        value = max(-1.0, min(1.0, value))
        frames += struct.pack('<h', int(value * 32767))

    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(bytes(frames))


if __name__ == '__main__':
    make_explosion('sounds/explosion.wav')
    print('wrote sounds/explosion.wav')
