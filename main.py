from app import app
from hypercorn.asyncio import serve
from hypercorn.config import Config

import asyncio


if __name__ == '__main__':
    asyncio.run(serve(app, Config()))
