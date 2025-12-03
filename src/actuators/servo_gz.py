from __future__ import annotations
import logging, os, time
from gpiozero import AngularServo
logger = logging.getLogger("actuators.servo_gz")

class GpioZeroServo:
    def __init__(self, pin: int, min_us: int = 500, max_us: int = 2500):
        os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")
        self.servo = AngularServo(pin, min_angle=0, max_angle=180,
                                  min_pulse_width=min_us/1_000_000,
                                  max_pulse_width=max_us/1_000_000)
        logger.info("AngularServo initialized on GPIO %s", pin)

    def move_to(self, angle: float, sleep: float | None = 0.4) -> None:
        angle = max(0.0, min(180.0, float(angle)))
        self.servo.angle = angle
        if sleep and sleep > 0: time.sleep(sleep)

    def stop(self)->None:
        self.servo.detach()
