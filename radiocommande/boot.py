# boot.py -- run on boot-up
import neopixel
import network
import time
from machine import Pin

# LED status
led = neopixel.NeoPixel(Pin(2), 1)
brightness = 0.5

# Configuration WiFi
WIFI_SSID = "domo"
WIFI_PASSWORD = "th1Sp4((!"

def set_led(status, brightness=0.1):
    colors = {
        "connecting wifi": (255, 255, 0),    # jaune
        "connecting mqtt": (0, 255, 255),    # cyan
        "ready": (0, 255, 0),                # vert
        "sending msg": (0, 0, 255),          # bleu
        "error": (255, 0, 0),                # rouge
        "none":(0,0,0)
    }
    r, g, b = colors.get(status, (255, 255, 255))
    led[0] = (int(r * brightness), int(g * brightness), int(b * brightness))
    led.write()
    

def connect_wifi():
    set_led("connecting wifi")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connexion au WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        # Attendre la connexion (timeout 10s)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            set_led("none")
            time.sleep(1)
            timeout -= 1
            set_led("connecting wifi")
            print(".", end="")

        print()

    if wlan.isconnected():
        print("WiFi connecté!")
        print("IP:", wlan.ifconfig()[0])
    else:
        print("Échec connexion WiFi")
        set_led("error")

connect_wifi()

