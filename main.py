import asyncio
import ssl
import websockets
import json
import pprint
import wiringpi

from typing import Dict, List
import socket

from config import logging_format, server_uri
import os
import logging

RECV_TIMEOUT: float = 60.0

logging.basicConfig(level=logging.INFO, format=logging_format)

ssl_context = ssl.create_default_context()

wiringpi.wiringPiSetupGpio()
wiringpi.pinMode(22, wiringpi.OUTPUT)

async def recv_status():
    async with websockets.connect(server_uri + '/sign', ssl=ssl_context) as websocket:
        while True:
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=RECV_TIMEOUT)
                msg_json = json.loads(msg)
                logging.info(f'Received update {pprint.pformat(msg)}')
                wiringpi.digitalWrite(22, wiringpi.HIGH if msg_json['open'] else wiringpi.LOW)
                logging.info(f'Successfully drove relay to {'HIGH' if msg_json['open'] else 'LOW'}')
            except:
                logging.warn('Timed out while awaiting update, turning off relay')
                wiringpi.digitalWrite(22, wiringpi.LOW)
                continue

while True:
    try:
        asyncio.get_event_loop().run_until_complete(recv_status())
    except Exception as serr:
        logging.warning(f"Exception while receiving status, attempting to start again: {serr}")
