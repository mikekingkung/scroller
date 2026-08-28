import math
import random
import struct
import wave

SAMPLE_RATE = 44100


def write_wav(path, samples):
    frames = bytearray()
    for v in samples:
        v = max(-1.0, min(1.0, v))
        frames += struct.pack('<h', int(v * 32767))
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(bytes(frames))


def make_hyperspace(path, duration=0.45, volume=0.5):
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        # rapid up-then-down pitch warble, classic teleport "blip"
        freq = 300 + 1800 * math.sin(math.pi * progress)
        phase = 2 * math.pi * freq * t
        tone = math.sin(phase)
        noise = random.uniform(-1, 1) * 0.15
        envelope = math.sin(math.pi * progress)
        samples.append((tone + noise) * envelope * volume)
    write_wav(path, samples)


def make_rescue(path, duration=0.35, volume=0.5):
    n = int(SAMPLE_RATE * duration)
    notes = [523.25, 659.25, 783.99]  # C5 E5 G5 - happy ascending chime
    samples = [0.0] * n
    seg = n // len(notes)
    for idx, freq in enumerate(notes):
        start = idx * seg
        end = n if idx == len(notes) - 1 else start + seg
        for i in range(start, end):
            t = (i - start) / SAMPLE_RATE
            local_progress = (i - start) / max(1, end - start)
            envelope = math.sin(math.pi * local_progress)
            samples[i] += math.sin(2 * math.pi * freq * t) * envelope * volume
    write_wav(path, samples)


def make_bomb(path, duration=0.9, volume=0.7):
    n = int(SAMPLE_RATE * duration)
    raw = [random.uniform(-1, 1) for _ in range(n)]
    smoothed = []
    window = 9
    for i in range(n):
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        smoothed.append(sum(raw[lo:hi]) / (hi - lo))
    samples = []
    for i in range(n):
        progress = i / n
        envelope = (1 - progress) ** 2
        rumble = math.sin(2 * math.pi * 40 * (i / SAMPLE_RATE)) * 0.3
        samples.append((smoothed[i] + rumble) * envelope * volume)
    write_wav(path, samples)


if __name__ == '__main__':
    make_hyperspace('sounds/hyperspace.wav')
    make_rescue('sounds/rescue.wav')
    make_bomb('sounds/bomb.wav')
    print('wrote sounds/hyperspace.wav, sounds/rescue.wav, sounds/bomb.wav')
