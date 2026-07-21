import os
import numpy as np
import soundfile as sf

SR = 44100
OUT = "samples"
PEAK = 0.8


def _envelope(dur, decay_s):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    return np.exp(-t / decay_s)


def _sweep(f0, f1, dur):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    phase = 2 * np.pi * (f0 * t + (f1 - f0) * t ** 2 / (2 * dur))
    return np.sin(phase)


def _white(n):
    return np.random.uniform(-1, 1, n)


def _normalize(x):
    m = np.max(np.abs(x))
    return x * (PEAK / m) if m > 0 else x


def kick():
    dur = 0.35
    env = _envelope(dur, 0.10)
    sig = _sweep(120, 45, dur) * env
    return _normalize(sig)


def snare():
    dur = 0.18
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    tone = np.sin(2 * np.pi * 190 * t)
    noise = _white(n)
    sig = (0.4 * tone + 0.6 * noise) * np.exp(-t / 0.04)
    return _normalize(sig)


def hihat_closed():
    dur = 0.06
    n = int(SR * dur)
    noise = _white(n)
    t = np.linspace(0, dur, n, endpoint=False)
    high = np.exp(-t / 0.005) * 0.5
    sig = noise * high
    return _normalize(sig)


def hihat_open():
    dur = 0.42
    n = int(SR * dur)
    noise = _white(n)
    t = np.linspace(0, dur, n, endpoint=False)
    high = np.exp(-t / 0.08) * 0.5
    sig = noise * high
    return _normalize(sig)


def crash():
    dur = 1.4
    n = int(SR * dur)
    noise = _white(n)
    t = np.linspace(0, dur, n, endpoint=False)
    env = np.minimum(t / 0.005, 1.0) * np.exp(-t / 0.30)
    sig = noise * env
    return _normalize(sig)


def tom():
    dur = 0.40
    env = _envelope(dur, 0.08)
    sig = _sweep(220, 110, dur) * env
    return _normalize(sig)


def ride():
    dur = 0.90
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    noise = _white(n)
    shimmer = np.sin(2 * np.pi * 6000 * t) * 0.3
    env = np.exp(-t / 0.15)
    sig = (noise + shimmer) * env
    return _normalize(sig)


GENERATORS = {
    "kick": kick,
    "snare": snare,
    "hihat_closed": hihat_closed,
    "hihat_open": hihat_open,
    "crash": crash,
    "tom": tom,
    "ride": ride,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, gen in GENERATORS.items():
        path = os.path.join(OUT, f"{name}.wav")
        if os.path.exists(path):
            print(f"skip  {name}.wav  (already exists)")
            continue
        sig = gen()
        sf.write(path, sig, SR, subtype="PCM_16")
        print(f"write {name}.wav")


if __name__ == "__main__":
    main()