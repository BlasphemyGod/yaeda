import asks
import math
import asyncio

from quart import session, redirect, url_for

from .db import db_session
from .db.models import Restaurant


def logged_in():
    return session.get('restaurant_id', 0)


def get_current_restaurant():
    return db_session.query(Restaurant).filter(Restaurant.id == session['restaurant_id']).first()


def basket_len():
    return len(session.get('basket', []))


async def get_available_restaurants(address, db_session):
    restaurants = db_session.query(Restaurant).all()
            
    address_future = asyncio.ensure_future(get_toponym(address))
    restaurants_futures = [asyncio.ensure_future(get_toponym(restaurant.address))
                            for restaurant in restaurants]
    address_toponym, *restaurants_toponyms = await asyncio.gather(address_future, *restaurants_futures)
    
    if not address_toponym:
        return 
    
    available_restaurants = list()
    
    for count, restaurant_toponym in enumerate(restaurants_toponyms):
        if restaurant_toponym:
            if restaurants[count].serve_area >= toponyms_distance(address_toponym, restaurant_toponym):
                available_restaurants.append(restaurants[count])
    
    return available_restaurants


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
