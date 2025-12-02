# Smart Feeder (GPIOZero + LGPIO + ADS1115)
- DHT22 telemetry → PubNub
- Servo feed (manual `feedNow` + scheduled)
- ADS1115 analog water-level + buzzer/LED alarm with hysteresis
- PubNub command router (schedule/list/cancel)
- MJPG-Streamer Pi 5 control via PubNub (`cameraOn`/`cameraOff`/`cameraStatus`)

## Camera streaming

1. Ensure `scripts/mjpg_streamer_pi5.sh` is executable and run at least once manually with `sudo ./scripts/mjpg_streamer_pi5.sh start` to install dependencies.
2. Configure overrides in `config/settings.toml` under `[camera]` (port, resolution, fps, quality, `use_sudo`).
3. Send PubNub commands:
   - `cameraOn` → installs (if needed) and starts the service.
   - `cameraOff` → stops the streamer.
   - `cameraStatus` → returns current state plus stream URL. If `public_url` is set, only that URL is returned (no LAN IPs are exposed); otherwise LAN URLs are included.
4. Optional: fixed domain via Cloudflare Tunnel
   - Install `cloudflared` on the Pi (`sudo apt install cloudflared` or the official package).
   - Create a named tunnel in Cloudflare, bind it to your hostname (e.g., `pi-cam.simonoid.io`), and copy the tunnel token.
   - Export `CLOUDFLARE_TUNNEL_TOKEN=<token>` (or set `[camera].tunnel_token` in `config/settings.toml`) and keep `[camera].public_url` set to your hostname URL.
   - When `cameraOn` runs, the service will start the tunnel automatically and return only the public URL.

All camera acknowledgements are published as `{"type":"ack","command":"cameraOn","status":"ok","camera":{...}}`.
