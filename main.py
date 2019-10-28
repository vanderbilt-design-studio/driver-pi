import asyncio
import ssl
import json
import pprint
from typing import Dict, List
import socket
import platform
import logging

import websockets
import gpiozero
from gpiozero.pins.mock import MockFactory

from config import logging_format, server_uri

# This has to be slightly higher than the Heroku timeout
RECV_TIMEOUT: float = 60.0

# Mock values on non-GPIO computers
if platform.machine() in ['x86', 'x86_64', 'i386', 'i686']:
  gpiozero.Device.pin_factory = MockFactory()

logging.basicConfig(level=logging.INFO, format=logging_format)
ssl_context = ssl.create_default_context()
transistor_gate_pin = gpiozero.LEDBoard('GPIO22', 'GPIO23')

async def recv_status():
    async with websockets.connect(server_uri + '/sign', ssl=ssl_context) as websocket:
        while True:
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=RECV_TIMEOUT)
                msg_json = json.loads(msg)
                logging.info(f'Received update {pprint.pformat(msg)}')
                if msg_json['open']:
                    transistor_gate_pin.on()
                else:
                    transistor_gate_pin.off()
                logging.info('Successfully drove relay to {}'.format('HIGH' if msg_json['open'] else 'LOW'))
            except e:
                logging.warning('Timed out while awaiting update, turning off relay')
                transistor_gate_pin.off()
                raise e

while True:
    try:
        asyncio.get_event_loop().run_until_complete(recv_status())
    except Exception as serr:
        logging.warning(f"Exception while receiving status, attempting to start again: {serr}")
