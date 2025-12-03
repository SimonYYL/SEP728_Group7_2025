# src/services/water_level_service.py
from __future__ import annotations
import asyncio, logging, os
from gpiozero import DigitalOutputDevice

from core.settings import Settings
from core.bus import Bus
from utils.time import now_iso
from sensors.water_ads1115 import WaterAnalogADS1115  # ✅ fixed import

logger = logging.getLogger("services.water")

class WaterLevelService:
    """
    Periodically reads water level and publishes telemetry.
    Drives a buzzer+LED line when below threshold, with simple hysteresis to avoid chatter.
    """
    def __init__(self, settings: Settings, bus: Bus):
        self.settings = settings
        self.bus = bus

        cfg = settings.raw.get("sensors", {}).get("water_level", {})
        self.enabled = bool(cfg.get("enabled", False))
        self.interval = int(cfg.get("poll_interval_ms", 3000)) / 1000.0
        self.threshold_low = float(settings.raw.get("thresholds", {}).get("min_water_level_pct", 30.0))
        # hysteresis: turn alarm off when rising above this (low + 5% by default)
        self.threshold_clear = float(cfg.get("threshold_clear_pct", self.threshold_low + 5.0))

        self.sensor = WaterAnalogADS1115(
            channel=str(cfg.get("channel", "A3")),
            i2c_addr=int(cfg.get("i2c_addr", 72)),
            gain=int(cfg.get("gain", 1)),
            min_adc=int(cfg.get("min_adc", 0)),
            max_adc=int(cfg.get("max_adc", 65535)),
            mock=bool(settings.device.get("mock_mode", False)),
        )

        # Buzzer + LED (shared line)
        os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")
        pin = int(settings.pins.get("buzzer_led", 26))
        # Active-high output; change active_high=False if your circuit is inverted
        self.alarm = DigitalOutputDevice(pin=pin, active_high=True, initial_value=False)
        self._alarm_on = False

    def _set_alarm(self, on: bool):
        if on and not self._alarm_on:
            self.alarm.on(); self._alarm_on = True
            logger.info("WATER ALERT: buzzer/LED ON")
        elif (not on) and self._alarm_on:
            self.alarm.off(); self._alarm_on = False
            logger.info("WATER ALERT: buzzer/LED OFF")

    async def run(self):
        if not self.enabled:
            logger.info("WaterLevelService disabled; not starting.")
            return
        device_id = self.settings.device.get("id", "pi-feeder-01")
        while True:
            reading = self.sensor.read_pct()
            lvl = reading.get("level_pct")
            # Hysteresis
            if lvl is not None:
                if not self._alarm_on and lvl < self.threshold_low:
                    self._set_alarm(True)
                    await self.bus.publish({
                        "type": "event", "level": "warn", "code": "WATER_LOW",
                        "ts": now_iso(), "device_id": device_id,
                        "reading": reading, "threshold_low": self.threshold_low
                    })
                elif self._alarm_on and lvl >= self.threshold_clear:
                    self._set_alarm(False)
                    await self.bus.publish({
                        "type": "event", "level": "info", "code": "WATER_OK",
                        "ts": now_iso(), "device_id": device_id,
                        "reading": reading, "threshold_clear": self.threshold_clear
                    })

            await self.bus.publish({
                "type": "telemetry",
                "ts": now_iso(),
                "device_id": device_id,
                "sensors": {"water": reading}
            })
            await asyncio.sleep(self.interval)
