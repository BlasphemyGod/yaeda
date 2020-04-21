from yaeda import app
from yaeda.bot import listen as bot_listen
from hypercorn.asyncio import serve
from hypercorn.config import Config

import os
import asyncio


if __name__ == '__main__':
    config = Config()
    config.bind = ['0.0.0.0:' + os.environ.get('PORT', '8080')]
    asyncio.run(asyncio.wait([serve(app, config), bot_listen()]))
