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


def make_shoot(path, duration=0.09, volume=0.4):
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq = 1800 - 900 * progress
        tone = math.sin(2 * math.pi * freq * t)
        square_bite = 1 if tone >= 0 else -1
        envelope = (1 - progress) ** 1.5
        samples.append((tone * 0.6 + square_bite * 0.4) * envelope * volume)
    write_wav(path, samples)


def make_hit(path, duration=0.09, volume=0.5):
    n = int(SAMPLE_RATE * duration)
    raw = [random.uniform(-1, 1) for _ in range(n)]
    samples = []
    for i in range(n):
        progress = i / n
        envelope = (1 - progress) ** 4
        t = i / SAMPLE_RATE
        pop = math.sin(2 * math.pi * 220 * (1 - progress) * t)
        samples.append((raw[i] * 0.5 + pop * 0.5) * envelope * volume)
    write_wav(path, samples)


def make_brain_zap(path, duration=0.35, volume=0.5):
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        wobble = math.sin(2 * math.pi * 14 * t) * 250
        freq = 500 + wobble
        tone = math.sin(2 * math.pi * freq * t)
        bitcrush = 1 if tone >= 0 else -1
        envelope = math.sin(math.pi * progress)
        samples.append((tone * 0.4 + bitcrush * 0.4) * envelope * volume)
    write_wav(path, samples)


def make_extra_life(path, duration=0.55, volume=0.5):
    n = int(SAMPLE_RATE * duration)
    notes = [523.25, 659.25, 783.99, 1046.50]  # C5 E5 G5 C6
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


def make_theme(path, duration=4.0, volume=0.3):
    n = int(SAMPLE_RATE * duration)
    bpm = 150
    beat = 60.0 / bpm
    eighth = beat / 2
    bass_pattern = [110, 110, 130.81, 110, 146.83, 110, 130.81, 98]
    fade_len = int(SAMPLE_RATE * 0.15)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        step = int(t / eighth) % len(bass_pattern)
        freq = bass_pattern[step]
        phase = 2 * math.pi * freq * t
        bass = 1 if math.sin(phase) >= 0 else -1  # square wave bass
        step_progress = (t % eighth) / eighth
        pluck_env = (1 - step_progress) ** 3
        hat = 0.0
        if step_progress < 0.06:
            hat = random.uniform(-1, 1) * 0.15
        fade = 1.0
        if i < fade_len:
            fade = i / fade_len
        elif i > n - fade_len:
            fade = (n - i) / fade_len
        value = (bass * 0.35 * pluck_env + hat) * volume * fade
        samples.append(value)
    write_wav(path, samples)


if __name__ == '__main__':
    make_shoot('sounds/robotron_shoot.wav')
    make_hit('sounds/robotron_hit.wav')
    make_brain_zap('sounds/brain_zap.wav')
    make_extra_life('sounds/extra_life.wav')
    make_theme('sounds/robotron_theme.wav')
    print('wrote robotron_shoot.wav, robotron_hit.wav, brain_zap.wav, extra_life.wav, robotron_theme.wav')
