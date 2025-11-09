from __future__ import annotations
import asyncio, json, logging
logger = logging.getLogger("core.bus")
try:
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio, SubscribeListener  # type: ignore
except Exception:
    PNConfiguration = None; PubNubAsyncio = None; SubscribeListener = None
    logger.warning("PubNub SDK unavailable; NO-OP bus.")

class Bus:
    def __init__(self, publish_key: str, subscribe_key: str, uuid: str, channel: str):
        self.channel = channel
        self._pn = None; self._listener = None
        if PNConfiguration and PubNubAsyncio:
            cfg = PNConfiguration(); cfg.publish_key=publish_key; cfg.subscribe_key=subscribe_key; cfg.uuid=uuid
            self._pn = PubNubAsyncio(cfg)
        else:
            logger.warning("Running without PubNub connection.")

    async def start(self):
        if self._pn is None: return
        self._listener = SubscribeListener()
        self._pn.add_listener(self._listener)
        self._pn.subscribe().channels(self.channel).execute()

    async def stop(self):
        if self._pn is None: return
        self._pn.unsubscribe_all(); await asyncio.sleep(0.1)

    async def publish(self, payload: dict):
        if self._pn is None:
            logger.info("[NO-OP publish] %s", json.dumps(payload))
            return
        env = await self._pn.publish().channel(self.channel).message(payload).future()
        if env.status.is_error():
            logger.error("PubNub publish error: %s", env.status.error_data)

    async def next_command(self) -> dict | None:
        if self._pn is None or self._listener is None:
            await asyncio.sleep(1.0); return None
        msg = await self._listener.wait_for_message_on(self.channel)
        try:
            payload = msg.message
            if isinstance(payload, dict) and payload.get("type") == "command":
                return payload
        except Exception:
            logger.exception("Incoming message parse failed")
        return None
