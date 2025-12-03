from __future__ import annotations
import logging
from actuators.servo_gz import GpioZeroServo
logger = logging.getLogger("actuators.feeder")

class Feeder:
    def __init__(self, pin: int):
        self.servo = GpioZeroServo(pin)

    def dispense_small(self)->None:
        logger.info("Feeder: dispensing...")
        self.servo.move_to(0)
        self.servo.move_to(90)
        self.servo.move_to(0)
        logger.info("Feeder: done.")
