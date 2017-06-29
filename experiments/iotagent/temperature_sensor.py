"""
This script simulates a temperature sensor generating random temperature values.

Data will be sent to an specified IoTAgent using the UL2.0 protocol over HTTP.
"""
from __future__ import print_function
import time
import random
import requests
import json
import socket
import sys

# Seconds to wait before each new notification
SLEEP = 4

DEVICE_ID = socket.gethostname()
API_KEY = "4jggokgpepnvsb2uv4s40d59ov"

ORION_HOST = "169.254.148.212"
# ORION_HOST = "0.0.0.0"
# ORION_HOST = "orion"
ORION_URL = "http://{}:1026".format(ORION_HOST)

AGENT_HOST = "169.254.148.212"
# AGENT_HOST = "0.0.0.0"

AGENT_CONFIG_URL = "http://{}:4041".format(AGENT_HOST)
CONFIG_HEADERS = {
    'Fiware-Service': 'default',
    'Fiware-ServicePath': '/',
    'Content-Type': 'application/json',
}

AGENT_NOTIFY_URL = "http://{}:7896".format(AGENT_HOST)
NOTIFY_HEADERS = {
    'Content-Type': 'text/plain',
}


def register():
    # Register Service
    data = {
         "services": [
           {
             "apikey":      API_KEY,
             "cbroker":     ORION_URL,
             "entity_type": "thing",
             "resource":    "/iot/d"
           }
         ]
    }
    r = requests.post('{}/iot/services'.format(AGENT_CONFIG_URL, API_KEY, DEVICE_ID), data=json.dumps(data), headers=CONFIG_HEADERS)
    assert r.ok, r.text

    # Register Sensor
    data = {
         "devices": [
           {
             "device_id":   DEVICE_ID,
             "x": "my_entity_01",
             "entity_type": "thing",
             "protocol":    "PDI-IoTA-UltraLight",
             "timezone":    "Europe/Madrid",
             "attributes": [
               {
                 "object_id": "t",
                 "name":      "temperature",
                 "type":      "float"
               }
             ]
           }
         ]
    }
    r = requests.post('{}/iot/devices'.format(AGENT_CONFIG_URL, API_KEY, DEVICE_ID), data=json.dumps(data), headers=CONFIG_HEADERS)
    assert r.ok, r.text


def send():
    temperature = random.random() * 40
    data = 't|{}'.format(temperature)
    print("sending {}".format(data))
    r = requests.post('{}/iot/d?k={}&i={}'.format(AGENT_NOTIFY_URL, API_KEY, DEVICE_ID), data=data, headers=NOTIFY_HEADERS)
    return r


if __name__ == '__main__':
    # Add any argument to avoid registration. Useful when restarting the sensor.
    if len(sys.argv) == 1:
        register()
        print("Configuration OK")

    while 1:
        r = send()
        assert r.ok, r.text
        time.sleep(SLEEP)
