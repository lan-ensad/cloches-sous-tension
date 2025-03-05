import asyncio
import RPi.GPIO as GPIO

class BTN:
    def __init__(self, btn_pin, led_pin):
        self.btn_pin = btn_pin
        self.led_pin = led_pin
        self.led = GPIO.setup(led_pin, GPIO.OUT)
        self.btn = GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.state = 0
        self.prev_state = None

    async def read_state(self):
        while True:
            # print(self.state)
            self.state = GPIO.input(self.btn_pin)
            if self.state == True:
                # if self.prev_state != self.state:
                #     print(f"State has changed to Live mode")
                #     self.prev_state = self.state
                GPIO.output(self.led_pin, GPIO.HIGH)
            else:
                # if self.prev_state != self.state:
                #     print(f"State has changed to Play mode")
                #     self.prev_state = self.state
                GPIO.output(self.led_pin, GPIO.LOW)
            await asyncio.sleep(0.1)