# CapSense Drum Kit and Guitar — Two-Board PSoC 6 Instrument

## Overview

This project turns two CY8CPROTO-062-4343W boards into a pair of musical
instruments — a 7-pad drum kit and a guitar — using Infineon's CapSense
touch-sensing technology. Each board detects touches on its capacitive
sensors, transmits hit events over USB serial at 115200 baud to a
laptop-hosted Python process, which synthesises audio in real time and
serves a live web dashboard. The two boards and their laptops run
independently; there is no wireless synchronisation between them.

## Architecture

The data path for each board is:

```
CapSense touch → PSoC 6 firmware (edge detection)
    → UART (115200 baud, USB serial)
    → Python host (serial read, audio engine, Flask server)
    → sounddevice OutputStream (local audio)
    → WebSocket push → browser dashboard
```

The drum board maps the 5-segment linear slider and two buttons to seven
discrete drum pads:

| Index | CapSense sensor               | Drum pad        |
|-------|-------------------------------|-----------------|
| 0     | LinearSlider0 SNS0            | kick            |
| 1     | LinearSlider0 SNS1            | snare           |
| 2     | LinearSlider0 SNS2            | hihat_closed    |
| 3     | LinearSlider0 SNS3            | hihat_open      |
| 4     | LinearSlider0 SNS4            | crash           |
| 5     | Button0 SNS0                  | tom             |
| 6     | Button1 SNS0                  | ride            |

The guitar board uses a separate firmware variant (not covered in this
repository's drum source) that reads the slider centroid position and maps
it to pitch or effect parameters.

## Design Decisions

### Individual sensor reads instead of the slider centroid API

The drum application needs seven independent binary touch states, not a
continuous position. Using `Cy_CapSense_IsSensorActive()` on each sensor
individually is the correct API for this: it returns whether a specific
sensor is touched, without computing a centroid across the slider elements.
The existing slider centroid code (`Cy_CapSense_GetTouchInfo`) is kept for
the original LED brightness demo but is not used for drum hit detection.

### Edge detection instead of polling every loop

The firmware prints one serial line per new touch, not a continuous stream
of touch-state snapshots. A rising-edge detector (`pad_now[i] &&
!pad_prev[i]`) ensures each physical touch produces exactly one serial
message. This avoids flooding the 115200 baud link and makes hits feel
discrete and responsive. The hold state is still tracked internally so the
same sensor cannot retrigger until it is released and touched again.

### Two independent boards instead of wireless sync

A wireless metronome or tempo-sync mechanism over BLE or UDP was discussed
early in the project but was cut to keep the scope manageable for a
two-developer, two-week timeline. Each player hears their own audio from
their own laptop. Playing together requires a shared sense of tempo or an
external metronome. See Limitations.

### Audio before network in the serial loop

In `main.py`, `audio.play(name)` is called before
`broadcast_hit(idx, name)`. This ordering is deliberate: percussion is
latency-sensitive, and the audio callback runs in a real-time audio thread
while the WebSocket broadcast may block briefly on socket writes. Audio
must never wait for the network.

## Serial Protocol

Each hit produces one line of the form:

```
D,<index>,<name>
```

Example:

```
D,0,kick
D,3,hihat_open
```

- `D` is a literal one-character marker.
- `<index>` is an integer 0–6 corresponding to the pad mapping table above.
- `<name>` is the pad name string.
- Lines are terminated with `\r\n` (CRLF).
- Any line that does not start with `D,` is ignored by the host.

## Setup and Run

### Firmware (PSoC 6)

1. Open ModusToolbox and import the project.
2. Build with the `CY8CPROTO-062-4343W` BSP target.
3. Program the board via KitProg3 USB.
4. The board will print the startup banner on the UART at 115200 baud.

### Host (Python)

The host application lives in the `host/` directory and must be run from
that directory (the path resolution in `audio.py` anchors to its own
source file location, so the working directory does not matter in practice):

```
cd host
pip install -r requirements.txt
python make_samples.py     # optional: synthesises 7 drum WAV files
python main.py
```

`make_samples.py` generates mono 16-bit 44100 Hz WAV files for all seven
pads. If real recordings are preferred, replace the files in `host/samples/`
with the same filenames.

Edit `config.py` to set `SERIAL_PORT` to the board's COM port. The port can
also be auto-detected if a single USB-UART device is connected.

Open a browser to `http://localhost:5000` to see the dashboard. The audio
plays through the laptop's default audio output.

## Known Limitations

**No board-to-board communication.** The two boards are not synchronised.
A wireless metronome or tempo-sync mechanism over BLE or UDP was designed
but not implemented. Each player relies on their own sense of timing.

**Latency is unmeasured.** The audio buffer is 256 frames (~5.8 ms at 44100
Hz), and the serial baud rate is 115200, but the end-to-end latency from
touch to audible output has not been formally measured or optimised.

**Samples are synthesised.** The drum sounds are generated by
`make_samples.py` using simple sine sweeps, white noise, and exponential
envelopes. They are not recorded acoustic samples.

**CapSense thresholds are untuned.** The project uses the default
sensitivity and threshold parameters from the Infineon CapSense buttons
and slider example. No per-sensor tuning was performed, which may result
in inconsistent trigger sensitivity across pads.

**No velocity sensitivity.** Every touch produces the same volume.
CapSense can report signal strength, which could be mapped to velocity,
but this was not implemented. Velocity is a natural next step.

## What We Would Do Next

- **Velocity mapping.** Use the raw CapSense signal strength
  (`Cy_CapSense_IsSensorActive` returns a signal-delta value, not just a
  boolean) to modulate sample gain or select between velocity layers.
- **Multi-sensor chords.** Detect simultaneous touches across the slider
  to produce combination hits (e.g. kick + crash).
- **Wireless metronome.** A UDP broadcast from one laptop to the other
  carrying a periodic beat tick, so both boards play in sync.
- **BLE integration.** Use the CY8CPROTO-062-4343W's onboard Bluetooth to
  send hit events wirelessly instead of USB serial.
- **CapSense tuning.** Spend time with the CapSense Tuner tool to set
  consistent sensitivity and noise thresholds across all seven pads.
- **Guitar firmware.** Implement pitch-to-frequency mapping on the slider,
  fret-detection using the buttons, and a strum gesture.
- **Latency measurement.** Use an oscilloscope or a loopback test to
  measure and document the round-trip latency from touch to audio output.