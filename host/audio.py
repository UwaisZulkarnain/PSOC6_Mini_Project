import os
import logging
import traceback
from pathlib import Path
import numpy as np
import sounddevice as sd
import soundfile as sf

logger = logging.getLogger(__name__)

_cb_count = 0
_cb_crashed = False


def _make_click(duration=0.05, samplerate=44100, freq=800):
    t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
    envelope = np.exp(-t * 40)
    return (envelope * np.sin(2 * np.pi * freq * t) * 0.3).astype(np.float32)


def _to_mono_1d(data):
    if data.ndim == 2:
        if data.shape[1] > 1:
            data = data.mean(axis=1)
        else:
            data = data[:, 0]
    return data.astype(np.float32)


class AudioEngine:
    def __init__(self, sample_dir, pad_names):
        self.sample_dir = str(Path(__file__).parent / sample_dir)
        logger.info("sample directory: %s", self.sample_dir)
        self.samplerate = 44100
        self.samples = {}
        self._load_samples(pad_names)

        self.voices = []
        info = sd.query_devices(None, "output")
        logger.info("output device: %s", info["name"] if info else "default")

        try:
            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=2,
                callback=self._callback,
                blocksize=256,
            )
            self.stream.start()
            logger.info(
                "stream opened  device=%s  samplerate=%d  channels=2  blocksize=256",
                info["name"] if info else "default",
                self.samplerate,
            )
        except Exception:
            logger.error("failed to open audio stream\n%s", traceback.format_exc())
            self.stream = None

    def _load_samples(self, pad_names):
        any_loaded = False
        for name in pad_names:
            path = os.path.join(self.sample_dir, f"{name}.wav")
            try:
                data, sr = sf.read(path, always_2d=False)
                data = _to_mono_1d(data)
                if not any_loaded:
                    self.samplerate = sr
                    any_loaded = True
                elif sr != self.samplerate:
                    logger.warning("sample rate mismatch in %s: %d != %d", name, sr, self.samplerate)
                self.samples[name] = data
                logger.info("loaded %s.wav  %d samples  %d Hz", name, len(data), sr)
            except Exception as e:
                logger.warning("could not load %s.wav: %s — using synthetic click", name, e)
                click = _make_click(samplerate=self.samplerate)
                self.samples[name] = _to_mono_1d(click)

    def play(self, pad_name):
        data = self.samples.get(pad_name)
        if data is None:
            logger.warning("play(%s) — no sample loaded", pad_name)
            return
        self.voices.append({"data": data.copy(), "pos": 0})
        logger.info("play(%s)  voices=%d", pad_name, len(self.voices))

    def _callback(self, outdata, frames, time_info, status):
        global _cb_count, _cb_crashed
        try:
            if _cb_count < 3:
                logger.info("audio callback #%d  frames=%d", _cb_count + 1, frames)
                _cb_count += 1
            if status:
                logger.warning("audio callback status: %s", status)
            outdata.fill(0)
            finished = []
            for i, v in enumerate(self.voices):
                chunk = v["data"][v["pos"]: v["pos"] + frames]
                n = len(chunk)
                if n > 0:
                    outdata[:n, 0] += chunk[:n]
                    outdata[:n, 1] += chunk[:n]
                    v["pos"] += n
                if v["pos"] >= len(v["data"]):
                    finished.append(i)
            for i in reversed(finished):
                self.voices.pop(i)
        except Exception:
            if not _cb_crashed:
                _cb_crashed = True
                logger.error("audio callback crashed\n%s", traceback.format_exc())
            outdata.fill(0)

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()