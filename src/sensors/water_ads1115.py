from __future__ import annotations
import logging
from typing import Optional, Tuple

logger = logging.getLogger("sensors.water_ads")

class WaterAnalogADS1115:
    def __init__(
        self,
        channel: str = "A3",
        i2c_addr: int = 0x48,
        gain: int = 1,
        min_adc: int = 0,
        max_adc: int = 65535,
        mock: bool = False,
    ) -> None:
        self.mock = mock
        self.min_adc = int(min_adc)
        self.max_adc = int(max_adc)
        self._chan = None
        if not mock:
            try:
                import board  # type: ignore
                from adafruit_ads1x15.ads1115 import ADS1115  # type: ignore
                from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore
                from adafruit_ads1x15 import ads1x15  # type: ignore
                i2c = board.I2C()
                ads = ADS1115(i2c, address=i2c_addr)
                ads.gain = gain
                pin = getattr(ads1x15.Pin, channel.upper())
                self._chan = AnalogIn(ads, pin)
                logger.info("ADS1115 water sensor on %s addr=0x%02X gain=%s", channel, i2c_addr, gain)
            except Exception as e:
                logger.warning("ADS1115 init failed: %s; switching to mock.", e)
                self.mock = True

    def read_raw(self) -> Tuple[Optional[int], Optional[float]]:
        if self.mock:
            return 32768, 2.048
        try:
            v = int(self._chan.value)     # 0..65535
            volt = float(self._chan.voltage)
            return v, volt
        except Exception as e:
            logger.warning("ADS1115 read error: %s", e)
            return None, None

    def read_pct(self) -> dict:
        raw, volt = self.read_raw()
        if raw is None:
            return {"raw": None, "voltage": volt, "level_pct": None}
        span = max(1, self.max_adc - self.min_adc)
        pct = (raw - self.min_adc) / span * 100.0
        pct = 0.0 if pct < 0 else 100.0 if pct > 100 else pct
        return {"raw": raw, "voltage": volt, "level_pct": round(pct, 1)}
