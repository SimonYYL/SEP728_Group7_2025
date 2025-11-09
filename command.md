# feed:
{ "type": "command", "command": "feedNow", "args": {} }

# schedule (todo: i need check this later):
{ "type": "command", "command": "scheduleFeed", "args": { "mode": "once", "at": "2025-11-07T18:30:00Z" } }
{ "type": "command", "command": "scheduleFeed", "args": { "mode": "daily", "time_local": "08:30", "days": ["Mon","Tue","Wed","Thu","Fri"] } }

# show the list? wotking on this one:
{ "type": "command", "command": "listSchedules", "args": {} }
{ "type": "command", "command": "cancelSchedule", "args": { "id": "<job-id>" } }

{ "type": "command", "command": "cancelSchedule", "args": { "id": "73d58572-5a62-4e77-9cad-487b1aea39f3" } }


data format:
<smart-feeder-main> { "type": "telemetry", "ts": "2025-11-08T20:38:42.867254+00:00", "device_id": "pi-feeder-01", "sensors": { "water": { "raw": 0, "voltage": 0, "level_pct": 0 } } }
<smart-feeder-main> { "type": "telemetry", "ts": "2025-11-08T20:38:42.862645+00:00", "device_id": "pi-feeder-01", "sensors": { "environment": { "temperature_c": 28.7, "humidity_pct": 25.8 } } }


camera command:
Turn camera on:
{ "type":"command", "command":"cameraOn", "args": { "request_id":"uuid-v4" } }

Turn camera off:
{ "type":"command", "command":"cameraOff", "args": { "request_id":"uuid-v4" } }


Live video (i need test on this, leave it low pro) -- still working on it
{ "type":"ack", "command":"cameraOn", "status":"ok", ......