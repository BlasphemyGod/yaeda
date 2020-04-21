import re
import aiovk
import random
import asyncio
from datetime import datetime

from .db.models import *
from .db import db_session
from .helpers import get_available_restaurants, get_toponym, toponyms_distance


TOKEN = '1bdf4d1369c07996b7a2a5db2653bb789d0aa9420e1df2e57e657dbddc302a78da2ce9844d9e04180323a'
sessions = dict()


help_str = '/basket - посмотреть корзину\n' + \
           '/place - задать адрес для доставки и поиска ближайших ресторанов\n' + \
           '/find - вывести список доступных ресторанов\n' + \
           '/select <число> - выбрать ресторан по его номеру\n' + \
           '/menu - посмотреть меню\n' + \
           '/add <номер товара> <кол-во> - добавить товар в корзину\n' + \
           '/del <номер товара> - удалить товар из корзины\n' + \
           '/order <номер телефона> - сделать заказ'


class States:
    no_state = 0
    input_address_city = 1
    input_address_street = 2
    input_address_house = 3
    input_address_apartment = 4


class LastIDict(dict):
    def __init__(self, *args, **kwargs):
        self.last_interaction = datetime.now()
        
        super().__init__(*args, **kwargs)
    
    def __getitem__(self, item):
        self.last_interaction = datetime.now()
        
        return super().__getitem__(item)
    
    def __setitem__(self, item, value):
        self.last_interaction = datetime.now()
        
        super().__setitem__(item, value)
        
        
async def garbage_collector():
    while True:
        for session_key, session in sessions.items():
            if (datetime.now() - session.last_interaction).total_seconds() > 600:
                sessions.pop(session_key)
        
        await asyncio.sleep(30)
        
        
async def on_help(api, user_id):
    await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                            message=help_str)
    
    
async def on_find(api, user_id, session):
    if session['address']['apartment']:
        customer_address = ' '.join((session['address']['city'],
                                     session['address']['street'],
                                     session['address']['house']))
        available_restaurants = await get_available_restaurants(customer_address, db_session)
        
        if not available_restaurants:
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Доступных ресторанов нет')
            return
        
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='\n'.join('{} - - "{}"'.format(restaurant.id, restaurant.name)
                                                  for restaurant in available_restaurants))
    else:
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='Сначала нужно задать адрес командой /place. /help для помощи')
        
        
async def on_select(api, user_id, session, restaurant_id):
    if session['address']['apartment']:
        customer_address = ' '.join((session['address']['city'],
                                     session['address']['street'],
                                     session['address']['house']))
        
        restaurant = db_session.query(Restaurant).get(restaurant_id)
        
        customer_toponym, restaurant_toponym = await asyncio.gather(get_toponym(customer_address),
                                                                    get_toponym(restaurant.address))
        
        if toponyms_distance(customer_toponym, restaurant_toponym) <= restaurant.serve_area:
            session['restaurant'] = restaurant_id
            
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Выбран ресторан "{}"'.format(restaurant.name))
        else:
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Ресторан находится вне зоны досягаемости')
    else:
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='Сначала нужно задать адрес командой /place. /help для помощи')
        
        
async def on_menu(api, user_id, session):
    if session['restaurant']:
        restaurant = db_session.query(Restaurant).get(session['restaurant'])
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='\n'.join(('{} - - "{}" {} р.').format(
                                    product.id, product.name, product.price
                                ) for product in restaurant.menu))
    else:
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='Сначала нужно выбрать ресторана командой /select. /help для помощи')
        
        
async def on_add(api, user_id, session, product_id, count):
    if session['restaurant']:
        restaurant = db_session.query(Restaurant).get(session['restaurant'])
        product = db_session.query(Product).get(product_id)
        
        if product.restaurant.id != restaurant.id:
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Этот продукт не относится к выбранному ресторану')
            return
        
        session['basket'][product_id] = count
    else:
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='Сначала нужно выбрать ресторан командой /select. /help для помощи')
        
        
async def on_del(api, user_id, session, product_id):
    if product_id in session['basket']:
        session['basket'].pop(product_id)
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='Товар {} удалён из корзины'.format(product_id))
    else:
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='Такого товара нет в корзине')
        
        
async def on_order(api, user_id, session, phone_number):
    if session['basket']:
        if session['address']['apartment']:
            destination = '{} {} {}, кв. {}'.format(session['address']['city'],
                                                    session['address']['street'],
                                                    session['address']['house'],
                                                    session['address']['apartment'])
            
            restaurant = db_session.query(Restaurant).get(session['restaurant'])
            
            if phone_number.startswith('8'):
                phone_number = phone_number.replace('8', '+7', 1)

            customer = db_session.query(Customer).filter(
                Customer.phone_number == phone_number
            ).first()
            
            if not customer:
                customer = Customer(phone_number=phone_number)
                
            order = Order(destination=destination, restaurant=restaurant,
                          customer=customer)

            products = db_session.query(Product).filter(Product.id.in_(list(map(int, session['basket'])))).all()
            
            if not all(product.restaurant.id == products[0].restaurant.id
                       for product in products):
                await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                        message='Все товары должны быть из одного ресторана!')
                return
            
            for product_id, count in session['basket'].items():
                order_item = OrderItem(product_id=product_id, count=count)
                order.order_items.append(order_item)

            db_session.add(order)
            db_session.commit()
            
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Заказ отправлен на обработку. ' +
                                            'Скоро с вами свяжется оператор для подтверждения заказа')
        else:
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Сначала нужно указать адрес командой /place. /help для помощи')
    else:
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='Корзина пуста!')
        
        
async def on_message(api, message):
    user_id = message['from_id']
    content = message['text']
    
    if user_id in sessions:
        session = sessions[user_id]
    else:
        sessions[user_id] = LastIDict({
            'basket': dict(), 
            'state': States.no_state,
            'restaurant': -1,
            'address': {
                'city': '',
                'steet': '',
                'house': '',
                'apartment': ''
            },
            'phone_number': ''
        })
        session = sessions[user_id]
        
    if not content.startswith('/') and session['state'] == States.no_state:
        await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                message='Для получения помощи по командам, напишите /help')
        return
    if content.startswith('/'):
        if content == '/help':
            await on_help(api, user_id)
            
        elif content == '/basket':
            if not session['basket']:
                await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                        message='Корзина пуста!')
                return
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='\n'.join(
                                        '{} - - "{}" {} шт'.format(
                                            product_id, 
                                            db_session.query(Product).get(product_id).name,
                                            count    
                                        ) for product_id, count in session['basket'].items()
                                    ))
            
        elif content == '/place':
            session['state'] = States.input_address_city
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Введите город')
            
        elif content == '/find':
            await on_find(api, user_id, session)
            
        elif re.match(r'/select \d+', content):
            await on_select(api, user_id, session, content.split()[1])
            
        elif content == '/menu':
            await on_menu(api, user_id, session)
            
        elif re.match(r'/add \d+ \d+', content):
            await on_add(api, user_id, session, *content.split()[1:])
            
        elif re.match(r'/del \d+', content):
            await on_del(api, user_id, session, content.split()[1])
            
        elif re.match(r'/order +7\d{10}', content) or re.match(r'/order 8\d{10}', content):
            await on_order(api, user_id, session, content.split()[1])
    else:
        if session['state'] == States.input_address_city:
            session['address']['city'] = content
            session['state'] = States.input_address_street
            
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Введите улицу')
            
        elif session['state'] == States.input_address_street:
            session['address']['street'] = content
            session['state'] = States.input_address_house
            
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Введите номер дома')

        elif session['state'] == States.input_address_house:
            session['address']['house'] = content
            session['state'] = States.input_address_apartment
            
            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Введите номер квартиры')
        
        elif session['state'] == States.input_address_apartment:
            customer_address = '{} {} {}'.format(session['address']['city'],
                                                 session['address']['street'],
                                                 session['address']['house'])
            customer_toponym = await get_toponym(customer_address)
            
            session['state'] = States.no_state

            if not customer_toponym:
                session['address']['city'] = ''
                session['address']['street'] = ''
                session['address']['house'] = ''

                await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                        message='Не удалось определить адрес. Попробуйте заново')
                return
            
            session['address']['apartment'] = content

            await api.messages.send(user_id=user_id, random_id=random.randint(0, 2 ** 64),
                                    message='Адрес успешно выбран')

async def listen():
    asyncio.create_task(garbage_collector())
    async with aiovk.TokenSession(TOKEN) as vk_session:
        vk_session.API_VERSION = '5.100'
        api = aiovk.API(vk_session)
        long_poll = aiovk.longpoll.BotsLongPoll(vk_session, 2, 194445144)
        while True:
            updates = (await long_poll.wait())['updates']
            for event in updates:
                if event['type'] == 'message_new':
                    asyncio.create_task(on_message(api, event['object']))
