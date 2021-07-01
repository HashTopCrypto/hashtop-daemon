from asyncio import sleep

from dotenv import load_dotenv
import os
import asyncio
import socketio
import logging
from base_logger import logger


logger = logger.getLogger(__name__)


load_dotenv()
if logger.level == logging.DEBUG or logger.level == logging.INFO:
    sio = socketio.AsyncClient(logger=True, engineio_logger=True)
else:
    sio = socketio.AsyncClient()

MINER_UUID = os.getenv('MINER_UUID')
USERNAME = os.getenv('USERNAME')
API_URL = os.getenv('API_URL')
namespace = '/miner'


@sio.event
async def send_share_update(data):
    logger.info('sending share update')
    response = await sio.emit('share_update',
                              (os.getenv('MINER_UUID'),
                               data)
                              )
  #  logger.info('send_share_update' + response)
    logger.debug(response)


@sio.event
async def send_health_update(data):
    logger.info('sending health update')
    response = await sio.emit('health_update',
                              (os.getenv('MINER_UUID'),
                               data)
                              )

   # logger.info("send_health_update" + response)
    logger.debug(response)
    return response


@sio.event
async def disconnect():
    logger.warning("disconnected from server")


@sio.event
async def connect():
    logger.info("connection established")
    await sio.emit('connect')


async def connect_server():
    connected = False
    while not connected:
        try:
            logger.info("connecting to server")
            await sio.connect(API_URL)
            await sio.wait()
        except:
            logger.warning("connection error")
        else:
            connected = True
            logger.info(sio.sid)


async def run():
    await sio.wait()
