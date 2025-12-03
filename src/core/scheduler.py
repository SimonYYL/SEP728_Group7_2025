from __future__ import annotations
import asyncio, json, logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Awaitable, Optional, List
logger = logging.getLogger("core.scheduler")
DAYS=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

@dataclass
class Job:
    id: str
    type: str
    at: Optional[str]=None
    time_local: Optional[str]=None
    days: Optional[List[str]]=None

class Scheduler:
    def __init__(self, storage_path: str, on_fire: Callable[[Job], Awaitable[None]]):
        self.storage=Path(storage_path); self.on_fire=on_fire
        self.jobs:list[Job]=[]; self._stop=asyncio.Event()

    def load(self)->None:
        if self.storage.exists():
            self.jobs=[Job(**j) for j in json.loads(self.storage.read_text('utf-8'))]
        else:
            self.jobs=[]
        logger.info('Scheduler: loaded %d job(s)', len(self.jobs))

    def save(self)->None:
        self.storage.parent.mkdir(parents=True, exist_ok=True)
        self.storage.write_text(json.dumps([asdict(j) for j in self.jobs], indent=2), 'utf-8')

    def add_job(self, job: Job)->Job:
        self.jobs.append(job); self.save(); return job

    def remove_job(self, job_id: str)->bool:
        n0=len(self.jobs); self.jobs=[j for j in self.jobs if j.id!=job_id]; self.save(); return len(self.jobs)<n0

    @staticmethod
    def _next_for_daily(job: Job, now: datetime)->datetime:
        hh,mm=[int(x) for x in job.time_local.split(':')]  # type: ignore
        candidate=now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        days=job.days or DAYS
        while candidate<now or DAYS[candidate.weekday()] not in days:
            candidate += timedelta(days=1)
            candidate=candidate.replace(hour=hh, minute=mm, second=0, microsecond=0)
        return candidate

    @staticmethod
    def _next_run(job: Job, now: datetime)->Optional[datetime]:
        if job.type=='once':
            if not job.at: return None
            try:
                t=datetime.fromisoformat(job.at.replace('Z','+00:00')).astimezone(tz=None).replace(tzinfo=None)
            except Exception:
                return None
            return t if t>now else None
        elif job.type=='daily':
            try: return Scheduler._next_for_daily(job, now)
            except Exception: return None
        return None

    async def run(self)->None:
        self._stop.clear()
        while not self._stop.is_set():
            now=datetime.now(); nexts=[]
            for j in list(self.jobs):
                nxt=self._next_run(j, now)
                if nxt is not None: nexts.append((j,nxt))
            if not nexts:
                await asyncio.sleep(1.0); continue
            job,when=min(nexts, key=lambda p:p[1])
            delay=max(0.0,(when-datetime.now()).total_seconds())
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=delay); break
            except asyncio.TimeoutError:
                pass
            await self.on_fire(job)
            if job.type=='once': self.remove_job(job.id)

    async def stop(self)->None:
        self._stop.set()
