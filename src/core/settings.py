from __future__ import annotations
import os, re
from dataclasses import dataclass
from typing import Any, Dict
try:
    import tomllib  # py3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

ENV_PATTERN = re.compile(r"^env:(?P<name>[A-Z0-9_]+)$")

@dataclass
class Settings:
    raw: Dict[str, Any]
    device: Dict[str, Any]
    pubnub: Dict[str, Any]
    camera: Dict[str, Any]
    thresholds: Dict[str, Any]
    pins: Dict[str, Any]

def _load_toml(path: str) -> Dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)

def _resolve_env(value: Any) -> Any:
    if isinstance(value, str):
        m = ENV_PATTERN.match(value)
        if m:
            name = m.group("name")
            v = os.getenv(name)
            if v is None:
                raise RuntimeError(f"Missing required environment variable: {name}")
            return v
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value

def load_settings() -> Settings:
    cfg = "config/settings.local.toml" if os.path.exists("config/settings.local.toml") else "config/settings.toml"
    raw = _load_toml(cfg)
    resolved = _resolve_env(raw)
    return Settings(
        raw=resolved,
        device=resolved.get("device", {}),
        pubnub=resolved.get("pubnub", {}),
        camera=resolved.get("camera", {}),
        thresholds=resolved.get("thresholds", {}),
        pins=resolved.get("pins", {}),
    )
