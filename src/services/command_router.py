from __future__ import annotations
import logging, uuid
from typing import Any, Dict
from core.bus import Bus
from core.scheduler import Scheduler, Job
from core.settings import Settings
from actuators.feeder import Feeder
logger = logging.getLogger("services.command")

class CommandRouter:
    def __init__(self, settings: Settings, bus: Bus, scheduler: Scheduler, feeder: Feeder):
        self.settings=settings; self.bus=bus; self.scheduler=scheduler; self.feeder=feeder

    async def _ack(self, command: str, status: str='ok', **extra: Any)->None:
        await self.bus.publish({'type':'ack','command':command,'status':status, **extra})

    async def _event(self, code: str, msg: str, **extra: Any)->None:
        await self.bus.publish({'type':'event','level':'info','code':code,'msg':msg, **extra})

    async def _on_fire(self, job: Job)->None:
        try:
            self.feeder.dispense_small()
            await self._event('FEED_DISPENSED', f'Job {job.id} dispensed food.')
        except Exception as e:
            await self._event('FEED_ERROR', f'Job {job.id} failed: {e}', level='error')

    async def run(self)->None:
        self.scheduler.load()
        while True:
            msg=await self.bus.next_command()
            if not msg: continue
            cmd=msg.get('command'); args=msg.get('args',{})
            try:
                if cmd=='feedNow':
                    self.feeder.dispense_small(); await self._ack(cmd,'ok')
                elif cmd=='scheduleFeed':
                    mode=args.get('mode','once')
                    if mode=='once':
                        job=Job(id=str(uuid.uuid4()), type='once', at=args.get('at'))
                    else:
                        job=Job(id=str(uuid.uuid4()), type='daily', time_local=args.get('time_local'), days=args.get('days'))
                    self.scheduler.add_job(job); await self._ack(cmd,'ok', job=job.__dict__)
                elif cmd=='cancelSchedule':
                    jid=args.get('id'); 
                    await self._ack(cmd, 'ok' if (jid and self.scheduler.remove_job(jid)) else 'error', id=jid)
                elif cmd=='listSchedules':
                    await self._ack(cmd, 'ok', jobs=[j.__dict__ for j in self.scheduler.jobs])
                else:
                    await self._ack(cmd or 'unknown', 'error', error='unknown command')
            except Exception as e:
                logger.exception('Command handling error')
                await self._ack(cmd or 'unknown', 'error', error=str(e))
