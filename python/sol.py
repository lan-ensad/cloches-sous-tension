from signal import signal, SIGINT
from adafruit_pca9685 import PCA9685
import time
import asyncio
import busio
import board
import yaml
import utils

## ====================================
##           LOAD CONFIG
config = utils.yaml_load_config('config.yaml')
travel_time = config["machine"]["travel_time"]

class Sol :
    """
    Solenoide Class
    """
    def __init__(self, chan, min_power=30):
        """
        Solenoide intialisation 
        """
        ## SHIT => https://github.com/adafruit/Adafruit_CircuitPython_PCA9685/blob/874545d908077baed0be8055cbbc63280a00c034/examples/pca9685_calibration.py#L4
        self.channel = chan
        self.min_power = min_power
        self.toggle_drony = None
        self.dronying = False
        self.freq = 0 ## drony() -> return the number of tape/second 
        self.start_time = time.time()
        self.timer = 0
        self.prevTimer = 1
        self.max_dronying = 10000 ## maximum second of effective drony -> prevent heat damages
        self.hit_length = None ## tape() -> define the time in millisecond to the selonoide to reach the bell
        self.delai_off = 500 ## drony() -> define the time in millisecond before another tape()
        self.travel_time_str = config["machine"]["travel_time"]
        self.travel_time = [int(i) for i in self.travel_time_str[0]]

    def get_timer(self):
        """
        Timer to prevent too much time dronying
        """
        if self.start_time is not None:
            self.timer = (time.time() - self.start_time) *1000
            return self.timer
        else:
            return None
    
    def stream_potar(self, potVal):
        """
        """
        self.delai_off = potVal
        return self.delai_off

    async def man_tape(self, p, travel):
        """
        Function that trigger one tape
        Test manualy travel time
        """
        utils.pwm_write(self.channel, p)
        await asyncio.sleep(travel/1000)
        utils.pwm_write(self.channel, 0)

    async def tape(self, power):
        """
        Function that trigger one tape
        power = pwm.duty -> pwm signal send to the mosfet
        hit_length = asyncio.sleep_ms -> let the solenoide time to reach point
        """
        if utils.map_val(power, 0, utils.OUTPUTMAX, 0, utils.INPUTMAX) < self.min_power:
            power = utils.map_val(self.min_power, 0, utils.INPUTMAX, 0, utils.OUTPUTMAX)
        self.hit_length = self.travel_time[int((utils.map_val(power, 0, utils.OUTPUTMAX, 0, utils.INPUTMAX)*len(self.travel_time)-1)/utils.INPUTMAX)]
        utils.pwm_write(self.channel, power)
        await asyncio.sleep(self.hit_length/1000)
        utils.pwm_write(self.channel, 0)

    async def toggle_drone(self, power=0, d_off=500):
        """Function that trigger the dronying asyncio.task"""
        ## -- FORMULA DECREASE TIME TO MECANIC RESET --
        # self.hit_length = int((1100*(pow(3.14,(-0.055*p))))+23) ## => best formula but to slow ?
        ## --------------------------------------------
        self.hit_length = self.travel_time[int((utils.map_val(power, 0, utils.OUTPUTMAX, 0, utils.INPUTMAX)*len(self.travel_time)-1)/utils.INPUTMAX)]
        ## --------------------------------------------
        ##      floor to trigger the solenoide
        if utils.map_val(power, 0, utils.OUTPUTMAX, 0, utils.INPUTMAX) < self.min_power:
            power = utils.map_val(self.min_power, 0, utils.INPUTMAX, 0, utils.OUTPUTMAX)
        ## --------------------------------------------
        if self.dronying == False:
            self.dronying = True
            self.start_time = time.time()
            self.delai_off = d_off
            self.toggle_drony = asyncio.create_task(self.drony(power))
        else:
            self.toggle_drony.cancel()
            utils.pwm_write(self.channel, 0)
            self.dronying = False
            self.toggle_drony=None
            self.start_time = None

    def stop_dronying(self):
        """ - """
        if self.dronying == True:
            self.dronying = False
            self.toggle_drony.cancel()
            utils.pwm_write(self.channel, 0)
            self.toggle_drony=None
            self.start_time = None

    async def drony(self, power):
        """
        USE ONLY CROSS go_drony()
        -------------------------
        Function that defines the dronying
        """
        while True:
            ## --- DEV ---
            # if self.timer != self.prevTimer:
            #     self.prevTimer = self.timer
            #     print(self.freq)
            #     self.freq = 0
            # self.freq += 1 ## count hits per second
            ## -----------
            ## --- SECURITY SETING ---
            # if self.get_timer()>=self.max_dronying:
            #     print(f"maximum time dronying reach ({self.max_dronying} ms). Need to rest a bit !")
            #     self.dronying = False
            #     self.toggle_drony.cancel()
            #     utils.pwm_write(self.channel, 0)
            #     self.toggle_drony=None
            #     self.start_time = None
            ## ----------------------
            utils.pwm_write(self.channel, power)
            await asyncio.sleep(self.hit_length/1000)
            utils.pwm_write(self.channel, 0)
            await asyncio.sleep(self.delai_off/1000)
