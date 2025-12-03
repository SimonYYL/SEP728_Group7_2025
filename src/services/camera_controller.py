from __future__ import annotations
import logging, os, socket, subprocess
from pathlib import Path
from typing import Any, Dict, List
from core.settings import Settings

logger = logging.getLogger("services.camera")

class CameraController:
    """
    Thin wrapper around mjpg_streamer_pi5.sh so commands can toggle the camera
    through PubNub the same way the feeder is controlled.
    """
    def __init__(self, settings: Settings):
        cfg = settings.camera or {}
        self.enabled = bool(cfg.get("enabled", False))
        self.base_dir = settings.base_dir
        script_cfg = Path(cfg.get("script_path", "scripts/mjpg_streamer_pi5.sh")).expanduser()
        self.script_path = script_cfg if script_cfg.is_absolute() else self.base_dir / script_cfg
        self.use_sudo = bool(cfg.get("use_sudo", True))
        self.tunnel_token = (cfg.get("tunnel_token") or os.getenv("CLOUDFLARE_TUNNEL_TOKEN") or "").strip()
        self.tunnel_bin = cfg.get("tunnel_bin", "cloudflared")
        self.tunnel_extra_args = cfg.get("tunnel_extra_args", [])
        self.tunnel_pid = self.base_dir / "data" / "cloudflared.pid"
        self.tunnel_log = self.base_dir / "logs" / "cloudflared.log"
        self.env_overrides = {
            "RES": str(cfg.get("resolution", "1280x720")),
            "FPS": str(cfg.get("fps", 30)),
            "Q": str(cfg.get("quality", 85)),
            "PORT": str(cfg.get("port", 8080)),
        }
        self.stream_suffix = cfg.get("stream_suffix", "?action=stream")
        # Allow an explicit public URL to override the derived one.
        self.public_url = cfg.get("public_url") or cfg.get("url")

    def is_enabled(self) -> bool:
        return self.enabled

    def _ensure_ready(self) -> None:
        if not self.enabled:
            raise RuntimeError("Camera disabled via settings.camera.enabled")
        if not self.script_path.exists():
            raise RuntimeError(f"Camera script missing: {self.script_path}")
        if not os.access(self.script_path, os.X_OK):
            raise RuntimeError(f"Camera script not executable: {self.script_path}")

    def _run(self, action: str, capture: bool = True) -> subprocess.CompletedProcess[str]:
        self._ensure_ready()
        cmd = [str(self.script_path), action]
        if self.use_sudo and os.geteuid() != 0:
            cmd.insert(0, "sudo")
        env = os.environ.copy()
        env.update({k: v for k, v in self.env_overrides.items() if v})
        logger.info("CameraController invoking: %s", " ".join(cmd))
        stdout = subprocess.PIPE if capture else None
        stderr = subprocess.PIPE if capture else None
        return subprocess.run(cmd, check=True, stdout=stdout, stderr=stderr, text=True, env=env)

    def start(self) -> Dict[str, Any]:
        self._run("start", capture=False)
        self._start_tunnel()
        return self.status()

    def stop(self) -> Dict[str, Any]:
        self._run("stop", capture=False)
        self._stop_tunnel()
        return self.status()

    def status(self) -> Dict[str, Any]:
        proc = self._run("status", capture=True)
        output = (proc.stdout or "").strip()
        running = "RUNNING" in output.upper()
        return self._build_payload("running" if running else "stopped", output)

    def _is_pid_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _is_tunnel_running(self) -> bool:
        if not self.tunnel_pid.exists():
            return False
        try:
            pid = int(self.tunnel_pid.read_text().strip())
        except (ValueError, OSError):
            return False
        return self._is_pid_running(pid)

    def _start_tunnel(self) -> None:
        if not self.tunnel_token:
            return
        if self._is_tunnel_running():
            return
        self.tunnel_pid.parent.mkdir(parents=True, exist_ok=True)
        self.tunnel_log.parent.mkdir(parents=True, exist_ok=True)
        log_f = open(self.tunnel_log, "a", encoding="utf-8")
        cmd = [self.tunnel_bin, "tunnel", "run", "--token", self.tunnel_token]
        if isinstance(self.tunnel_extra_args, list):
            cmd.extend([str(x) for x in self.tunnel_extra_args])
        logger.info("Starting Cloudflare tunnel: %s", " ".join(cmd))
        try:
            proc = subprocess.Popen(cmd, stdout=log_f, stderr=log_f, text=True, start_new_session=True)
        except FileNotFoundError as exc:
            logger.error("cloudflared binary not found (%s): %s", self.tunnel_bin, exc)
            log_f.close()
            return
        self.tunnel_pid.write_text(str(proc.pid), encoding="utf-8")
        log_f.close()

    def _stop_tunnel(self) -> None:
        if not self.tunnel_token:
            return
        if not self._is_tunnel_running():
            self.tunnel_pid.unlink(missing_ok=True)
            return
        try:
            pid = int(self.tunnel_pid.read_text().strip())
        except (ValueError, OSError):
            self.tunnel_pid.unlink(missing_ok=True)
            return
        try:
            os.kill(pid, 15)
        except OSError:
            pass
        self.tunnel_pid.unlink(missing_ok=True)

    def _local_hosts(self) -> List[str]:
        hosts: List[str] = []
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                if ip and ip not in hosts:
                    hosts.append(ip)
        except OSError:
            pass
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET):
                ip = info[4][0]
                if not ip or ip.startswith("127."):
                    continue
                if ip not in hosts:
                    hosts.append(ip)
        except OSError:
            pass
        return hosts

    def _build_payload(self, state: str, output: str) -> Dict[str, Any]:
        port = self.env_overrides["PORT"]
        hosts = self._local_hosts()
        suffix = self.stream_suffix.lstrip("/")
        if self.public_url:
            url = self.public_url
            lan_urls: List[str] = []
        elif hosts:
            url = f"http://{hosts[0]}:{port}/{suffix}" if suffix else f"http://{hosts[0]}:{port}"
            lan_urls = [f"http://{h}:{port}/{suffix}".rstrip("/") for h in hosts]
        else:
            url = f"http://<PI-IP>:{port}/{suffix}"
            lan_urls = []
        return {
            "state": state,
            "port": port,
            "resolution": self.env_overrides["RES"],
            "fps": self.env_overrides["FPS"],
            "quality": self.env_overrides["Q"],
            "url": url.rstrip("/"),
            "lan_urls": lan_urls,
            "tunnel_running": bool(self.tunnel_token) and self._is_tunnel_running(),
            "message": output or state,
        }
