from __future__ import annotations
import asyncio, logging, signal
from core.log import setup_logging
from core.settings import load_settings
from core.bus import Bus
from core.scheduler import Scheduler
from services.telemetry import TelemetryService
from services.water_level_service import WaterLevelService
from services.command_router import CommandRouter
from actuators.feeder import Feeder

async def amain()->None:
    setup_logging('INFO')
    log=logging.getLogger('main')
    settings=load_settings()
    log.info('Loaded settings for device %s', settings.device.get('id'))

    bus=Bus(publish_key=settings.pubnub['publish_key'],
            subscribe_key=settings.pubnub['subscribe_key'],
            uuid=settings.pubnub.get('uuid', settings.device.get('id','pi-feeder-01')),
            channel=settings.pubnub.get('channel','smart-feeder-main'))
    await bus.start()

    telemetry=TelemetryService(settings,bus)
    feeder=Feeder(pin=int(settings.pins.get('servo_feed',12)))
    sched=Scheduler(storage_path='data/schedules.json', on_fire=None)  # type: ignore
    router=CommandRouter(settings,bus,sched,feeder)
    sched.on_fire=router._on_fire

    stop=asyncio.Event()
    def _stop(*_): stop.set()

    loop=asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try: loop.add_signal_handler(sig,_stop)
        except NotImplementedError: pass

    tasks=[
        asyncio.create_task(telemetry.run(), name='telemetry'),
        asyncio.create_task(WaterLevelService(settings,bus).run(), name='water_level'),
        asyncio.create_task(sched.run(), name='scheduler'),
        asyncio.create_task(router.run(), name='commands'),
    ]
    await stop.wait()
    for t in tasks: t.cancel()
    await bus.stop()

if __name__=='__main__':
    try: asyncio.run(amain())
    except KeyboardInterrupt: pass
