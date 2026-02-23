# main.py -- put your code here!
from machine import Pin
from umqttsimple import MQTTClient
import time

# Configuration MQTT
MQTT_BROKER = "192.168.1.102"  # Adresse IP du broker MQTT
MQTT_TOPIC = b"instants/rc"
CLIENT_ID = "esp32_rc"

# Configuration bouton
BUTTON_PIN = 1

# Initialisation du bouton avec pull-up interne
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# État précédent du bouton (pour détecter le front descendant)
last_state = 1
playing = 0

def connect_mqtt():
    set_led("connecting mqtt")
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.connect()
    print("MQTT connecté au broker", MQTT_BROKER)
    return client

def main():
    global last_state, playing

    print("Connexion MQTT...")
    client = connect_mqtt()
    set_led("ready")

    print("En attente d'appui sur le bouton (GPIO {})...".format(BUTTON_PIN))

    while True:
        current_state = button.value()

        # Détection front descendant (bouton pressé, pull-up donc 1->0)
        if last_state == 1 and current_state == 0:
            set_led("sending msg")
            print("Bouton pressé! Envoi 'play'...")
            if playing==0:
                client.publish(MQTT_TOPIC, b"play")
                playing = 1
            elif playing==1:
                client.publish(MQTT_TOPIC, b"stop")
                playing=0
            print("Message envoyé!")

        last_state = current_state
        time.sleep_ms(200)  # Anti-rebond
        set_led("ready")
    time.sleep_ms(10)

main()

