import asks
import math

from quart import session, redirect, url_for

from .db import db_session
from .db.models import Restaurant


def logged_in():
    return session.get('restaurant_id', 0)


def get_current_restaurant():
    return db_session.query(Restaurant).filter(Restaurant.id == session['restaurant_id']).first()


def basket_len():
    return len(session.get('basket', []))


async def get_toponym(address):
    response = await asks.get('http://geocode-maps.yandex.ru/1.x/' + 
                              '?format=json&apikey={}&geocode={}'.format(
                                  '40d1649f-0493-4b70-98ba-98533de7710b',
                                  address
                              ))
    
    if response.status_code != 200:
        return 
    
    data = response.json()
    
    if not data['response']['GeoObjectCollection']['featureMember']:
        return 
    
    return data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']


def toponyms_distance(toponym_1, toponym_2):
    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = map(float, toponym_1['Point']['pos'].split())
    b_lon, b_lat = map(float, toponym_2['Point']['pos'].split())

    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)

    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor

    distance = math.sqrt(dx * dx + dy * dy)

    return distance
