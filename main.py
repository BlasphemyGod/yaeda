from yaeda import app
from yaeda.bot import listener as bot_listener
from hypercorn.asyncio import serve
from hypercorn.config import Config

import os
import asyncio
import multiprocessing


if __name__ == '__main__':
    config = Config()
    config.bind = ['0.0.0.0:' + os.environ.get('PORT', '8080')]
    asyncio.run(asyncio.wait([serve(app, config), bot_listener()]))
