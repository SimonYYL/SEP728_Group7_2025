from __future__ import annotations
import asyncio, logging
from typing import Dict, Any
from core.bus import Bus
from core.settings import Settings
from utils.time import now_iso
from sensors.dht22_sensor import DHT22Sensor
logger = logging.getLogger("services.telemetry")

class TelemetryService:
    def __init__(self, settings: Settings, bus: Bus):
        self.settings=settings; self.bus=bus
        self.dht=DHT22Sensor(bcm_pin=int(settings.pins.get("dht22_data",4)),
                             mock=bool(settings.device.get("mock_mode", False)))

    async def run(self)->None:
        interval=int(self.settings.device.get("poll_interval_ms",3000))/1000.0
        device_id=self.settings.device.get("id","pi-feeder-01")
        while True:
            t,h=self.dht.read()
            sensors={"environment":{}}
            if t is not None: sensors["environment"]["temperature_c"]=t
            if h is not None: sensors["environment"]["humidity_pct"]=h
            payload: Dict[str, Any]={"type":"telemetry","ts":now_iso(),"device_id":device_id,"sensors":sensors}
            await self.bus.publish(payload)
            await asyncio.sleep(interval)
