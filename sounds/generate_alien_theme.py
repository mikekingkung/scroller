import math
import struct
import wave

SAMPLE_RATE = 44100


def make_alien_theme(path, duration=8.0, volume=0.35):
    n = int(SAMPLE_RATE * duration)
    frames = bytearray()
    fade_len = SAMPLE_RATE * 0.5
    blip_period = 4.0

    for i in range(n):
        t = i / SAMPLE_RATE

        # slow vibrato modulating detuned drone frequencies for an eerie feel
        vibrato = math.sin(2 * math.pi * 0.15 * t) * 4
        f1 = 110 + vibrato
        f2 = 164.8 + vibrato * 1.3
        f3 = 55 + vibrato * 0.5
        drone = (
            0.5 * math.sin(2 * math.pi * f1 * t)
            + 0.3 * math.sin(2 * math.pi * f2 * t)
            + 0.2 * math.sin(2 * math.pi * f3 * t)
        )

        # periodic UFO-style downward blip sweep
        bt = t % blip_period
        blip = 0.0
        if bt < 0.6:
            sweep_freq = 900 - (bt / 0.6) * 500
            blip_env = math.sin(math.pi * (bt / 0.6))
            blip = 0.25 * math.sin(2 * math.pi * sweep_freq * t) * blip_env

        # fade in/out across the clip so the loop restarts without a click
        fade = 1.0
        if i < fade_len:
            fade = i / fade_len
        elif i > n - fade_len:
            fade = (n - i) / fade_len

        value = (drone + blip) * volume * fade
        value = max(-1.0, min(1.0, value))
        frames += struct.pack('<h', int(value * 32767))

    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(bytes(frames))


if __name__ == '__main__':
    make_alien_theme('sounds/alien_theme.wav')
    print('wrote sounds/alien_theme.wav')
