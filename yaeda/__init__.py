from quart import Quart


app = Quart(__name__)
app.secret_key = b'\x08c4\x12\xd9\x00\x86g\x8f;\xbcvJ\x10\xb1K\x05\xb1\xa6Z}\xbe\xdc\xa3\xf0L\x8a \x83\x04\x7f\xd1'

import yaeda.routes
from yaeda.blueprints import *

app.register_blueprint(menu_blueprint)
app.register_blueprint(basket_blueprint)
app.register_blueprint(order_blueprint)
