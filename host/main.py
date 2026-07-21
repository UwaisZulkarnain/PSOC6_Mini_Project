import sys
import time
import logging
import threading
import serial
import serial.tools.list_ports

from config import SERIAL_PORT, BAUD, SAMPLE_DIR, PADS
from audio import AudioEngine
from server import run_server, broadcast_hit

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
logger = logging.getLogger("main")


def find_serial_port(hint):
    if hint and hint != "COM15":
        return hint
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "USB" in p.description or "UART" in p.description or "CP210" in p.description:
            return p.device
    return hint


def main():
    audio = AudioEngine(SAMPLE_DIR, PADS)

    httpd = threading.Thread(target=run_server, daemon=True)
    httpd.start()

    port = find_serial_port(SERIAL_PORT)
    logger.info("starting — sample rate %d Hz  dashboard http://localhost:5000", audio.samplerate)

    while True:
        try:
            ser = serial.Serial(port, BAUD, timeout=1)
            logger.info("connected to %s", port)
        except Exception as e:
            logger.warning("cannot open %s: %s — retry in 2s", port, e)
            time.sleep(2)
            continue

        try:
            while True:
                line = ser.readline()
                if not line:
                    continue
                line = line.decode("utf-8", errors="replace").strip()
                if not line.startswith("D,"):
                    continue
                parts = line.split(",")
                if len(parts) < 3:
                    continue
                try:
                    idx = int(parts[1])
                    name = parts[2]
                except (ValueError, IndexError):
                    continue
                if idx < 0 or idx >= len(PADS):
                    continue
                audio.play(name)
                broadcast_hit(idx, name)
        except serial.SerialException:
            logger.warning("serial disconnected — retry in 2s")
        except Exception:
            logger.exception("serial read error")
        finally:
            try:
                ser.close()
            except:
                pass
            time.sleep(2)


if __name__ == "__main__":
    main()