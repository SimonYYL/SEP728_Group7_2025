from __future__ import annotations
import logging, random, time
from typing import Optional, Tuple
logger = logging.getLogger("sensors.dht22")

class DHT22Sensor:
    def __init__(self, bcm_pin: int, mock: bool = False):
        self.pin=bcm_pin; self.mock=mock; self._drv=None
        if not mock:
            try:
                import adafruit_dht  # type: ignore
                import board  # type: ignore
                pin_attr = f"D{self.pin}"
                if hasattr(board, pin_attr):
                    self._drv = adafruit_dht.DHT22(getattr(board, pin_attr), use_pulseio=False)
                else:
                    logger.warning("Board pin not found; using mock.")
                    self.mock=True
            except Exception as e:
                logger.warning("DHT init failed (%s); using mock.", e)
                self.mock=True

    def read(self) -> Tuple[Optional[float], Optional[float]]:
        if self.mock:
            return round(random.uniform(20.0, 28.0),1), round(random.uniform(35.0, 60.0),1)
        try:
            t = self._drv.temperature  # type: ignore
            h = self._drv.humidity     # type: ignore
            if t is None or h is None: raise RuntimeError("Invalid DHT22 reading")
            return float(t), float(h)
        except Exception as e:
            logger.warning("DHT read error: %s", e); time.sleep(0.5); return None, None
