#!/usr/bin/env bash
# mjpg_streamer_pi5.sh
# All-in-one setup & runner for MJPG-Streamer on Raspberry Pi OS Bookworm (Pi 5).
# Uses Arducam's fork with input_libcamera.so (compatible with rpicam-*).

set -euo pipefail

# ----- Defaults (override via env) -----
RES="${RES:-1280x720}"
FPS="${FPS:-30}"
Q="${Q:-85}"
PORT="${PORT:-8080}"
REPO="${REPO:-https://github.com/ArduCAM/mjpg-streamer.git}"
SRC_DIR="/opt/mjpg-streamer-arducam"
LOG_DIR="/var/log/mjpg-streamer"
WWW_DIR="/usr/local/share/mjpg-streamer/www"
PLUG_DIR="/usr/local/lib/mjpg-streamer"
BIN="/usr/local/bin/mjpg_streamer"
# --------------------------------------

ensure_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "Please run as root: sudo $0 $*"
    exit 1
  fi
}

install_deps() {
  echo "[+] Installing deps..."
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git cmake build-essential libjpeg62-turbo-dev libcamera-apps libcamera-dev
  mkdir -p "$LOG_DIR"
}

build_install() {
  echo "[+] Building Arducam mjpg-streamer (with input_libcamera)"
  rm -rf "$SRC_DIR"
  git clone "$REPO" "$SRC_DIR"
  pushd "$SRC_DIR/mjpg-streamer-experimental" >/dev/null
  make -j"$(nproc)"
  make install
  popd >/devnull || popd >/dev/null || true
}

ensure_install() {
  local need=0
  if [[ ! -x "$BIN" ]]; then need=1; fi
  if [[ ! -f "$PLUG_DIR/input_libcamera.so" ]]; then need=1; fi
  if [[ $need -eq 1 ]]; then
    build_install
  fi
  if [[ ! -x "$BIN" ]] || [[ ! -f "$PLUG_DIR/input_libcamera.so" ]]; then
    echo "[!] Installation check failed (missing mjpg_streamer or input_libcamera.so)"
    exit 1
  fi
}

start() {
  ensure_root
  install_deps
  ensure_install

  if [[ ! -d "$WWW_DIR" ]]; then
    echo "[!] Web root missing, reinstalling..."
    build_install
  fi
  if [[ ! -d "$WWW_DIR" ]]; then
    echo "[!] Web root still missing; aborting."
    exit 1
  fi

  pkill -f "mjpg_streamer .* -p ${PORT}" 2>/dev/null || true

  export LD_LIBRARY_PATH="${PLUG_DIR}:/usr/local/lib:${LD_LIBRARY_PATH-}"

  echo "[+] Launching mjpg_streamer on port ${PORT} with RES=${RES} FPS=${FPS} Q=${Q}"
  nohup "$BIN" \
    -i "input_libcamera.so --resolution ${RES} --fps ${FPS} --quality ${Q}" \
    -o "output_http.so -p ${PORT} -w ${WWW_DIR}" \
    > "${LOG_DIR}/mjpg-streamer.log" 2>&1 &

  sleep 1
  if ! pgrep -f "mjpg_streamer .* -p ${PORT}" >/dev/null; then
    echo "[!] mjpg_streamer failed to start; see ${LOG_DIR}/mjpg-streamer.log"
    tail -n 60 "${LOG_DIR}/mjpg-streamer.log" || true
    exit 1
  fi

  echo "[+] mjpg_streamer running. Open:"
  local ip
  ip=$(ip -o -4 addr show | awk '!/ lo /{print $4}' | cut -d/ -f1 | head -n1)
  echo "  http://${ip:-<PI-IP>}:${PORT}/?action=stream"
}

stop() { ensure_root; echo "[+] Stopping mjpg_streamer..."; pkill -f mjpg_streamer 2>/dev/null || true; }
status() {
  if pgrep -f "mjpg_streamer .* -p ${PORT}" >/dev/null; then
    echo "mjpg_streamer: RUNNING (port ${PORT})"
  else
    echo "mjpg_streamer: STOPPED"
  fi
}
restart() { stop; start; }

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  *)
cat <<'EOF'
Usage:
  sudo ./mjpg_streamer_pi5.sh start|stop|restart|status

Env overrides example:
  RES=640x480 FPS=15 Q=80 PORT=8081 sudo ./mjpg_streamer_pi5.sh start
EOF
    exit 1
    ;;
esac
