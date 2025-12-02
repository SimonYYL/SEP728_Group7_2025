# Pinout (Pi 5)

- **DHT22 DATA**: BCM 4 → Physical Pin 7
- **DHT22 VCC**: 3.3V → Physical Pin 1
- **DHT22 GND**: GND → Physical Pin 6 (or any GND)
- **Feeder servo signal**: BCM 12 → Physical Pin 32
- **Servo power**: 5V (Pin 2 or 4) and GND (Pin 9/14/20/25); share GND with Pi
- **Buzzer/LED (shared)**: BCM 26 → Physical Pin 37
- **ADS1115 I²C**: SDA (Pin 3), SCL (Pin 5), 3.3V (Pin 1), GND (Pin 6)
- **ADS1115 Analog Input**: Sensor signal → A3 (per config), sensor GND → ADS GND, sensor V+ per module spec
