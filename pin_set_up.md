DHT22
Pi 3.3V  (Pin 1) ---->  VCC
Pi GPIO4 (Pin 7) ---->  DATA
Pi GND   (Pin 6) ---->  GND

Servo
Pi GPIO12 (Pin 32) ---->  signal
Pi 5V      (Pin 2 or 4) ->  VCC
Pi GND     (Pin 9 or 14) ->  GND


unzip smart-feeder-gpiozero.zip
cd smart-feeder-gpiozero
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# PubNub keys
export PUBNUB_PUB_KEY=pub-c-b920f8a4-2ea4-4035-91e9-a99fd4722310
export PUBNUB_SUB_KEY=sub-c-8f0c2347-c27e-4ce7-a4f8-38108ba59cb5

# Use the Pi-5 compatible pin factory
export GPIOZERO_PIN_FACTORY=lgpio

# (Optional) switch to real DHT22:
# nano config/settings.toml   -> set device.mock_mode=false
bash scripts/dev_run.sh
