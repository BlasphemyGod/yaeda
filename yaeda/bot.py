import asyncio
import aiovk
import aiovk.longpoll
import asks
import random
import re

from .db import Session
from .db.models import Customer, Product, Order, OrderItem, Restaurant
from .helpers import get_available_restaurants, get_toponym

from datetime import datetime


sessions = dict()

TOKEN = '1bdf4d1369c07996b7a2a5db2653bb789d0aa9420e1df2e57e657dbddc302a78da2ce9844d9e04180323a'


help_str = 'Привет! Я бот сервиса ЯЕда.\n' + \
           'Чтобы выбрать место доставки, напиши /place <адрес>\n' + \
           'Чтобы получить список ближайших ресторанов, напиши /find\n' + \
           'Чтобы выбрать ресторан напиши /select <номер ресторана>\n' + \
           'Чтобы посмотреть меню выбранного ресторана напиши /menu\n' + \
           'Чтобы добавить товар в корзину напиши /add <номер товара> <кол-во>\n' +  \
           'Чтобы изменить количество товара в корзине напиши /amount <номер товара> <кол-во>\n' + \
           'Чтобы удалить товар из корзины напиши /del <номер товара>\n' + \
           'Чтобы посмотреть корзину напиши /basket\n' + \
           'Чтобы сделать заказ напиши /order <номер телефона>\n' + \
           'Чтобы получить помощь по командам напиши /help'
           
           
def random_id():
    return random.randint(0, 2 ** 64)


async def handle_session(api, content, session):
    db_session = Session()
    if not content.startswith('/'):
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='С ботом можно работать только командами, /help - помощь по командам')
        
        return
    
    if re.match(r'/place .+', content):
        address = content[7:]
        
        toponym = await get_toponym(address)
        
        if not toponym:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Не удалось определить ваш адрес. Попробуйте перефразировать')
            
            return
        
        session['last_interaction'] = datetime.now()
        session['address'] = toponym['metaDataProperty']['GeocoderMetaData']['text']
        
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='Место доставки установлено на {}'.format(address))

    elif content == '/find':
        if not session['address']:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Сначала нужно задать адрес с помощью /place <адрес>')
            
            return
        
        available_restaurants = await get_available_restaurants(session['address'], db_session)
        
        if not available_restaurants:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Нет доступных ресторанов')
            
            return
            
        session['last_interaction'] = datetime.now()
        session['available_restaurants'] = [restaurant.id for restaurant in available_restaurants]
        
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='\n'.join('{} -- {}'.format(restaurant.name, restaurant.id)
                                                  for restaurant in available_restaurants))
    
    elif re.match(r'/select \d+', content):
        if 'available_restaurants' not in session:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Сначала нужно выбрать адрес /place <адрес>')
            return
            
        if not session['available_restaurants']:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Нет доступных ресторанов')
            return
        
        restaurant_id = int(content.split()[1])
        
        if restaurant_id not in session['available_restaurants']:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Возможно, вы неверно указали номер ресторана: вы вне зоны его обслуживания')
            return

        session['last_interaction'] = datetime.now()
        session['current_restaurant'] = restaurant_id
        
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='Выбран ресторан под номером {}'.format(restaurant_id))
        
    elif content == '/menu':
        if 'current_restaurant' not in session:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Сначала нужно выбрать ресторан /select <номер ресторана>')
            return
        
        restaurant = db_session.query(Restaurant).get(session['current_restaurant'])

        session['last_interaction'] = datetime.now()
        
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='\n'.join('{} {} р. -- {}'.format(product.name, product.price,
                                                                          product.id)
                                                  for product in restaurant.menu))
    
    elif re.match(r'/add \d+ \d+', content):
        if 'current_restaurant' not in session:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Сначала нужно выбрать ресторан /select <номер ресторана>')
            return
        
        _, product_id, count =  content.split()

        restaurant = db_session.query(Restaurant).get(session['current_restaurant'])
        product = db_session.query(Product).get(product_id)
        
        if restaurant.id != product.restaurant.id:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Номер товара не относится к выбранному ресторану')
            return
            
        if session['basket']:
            if db_session.query(Product).get(list(session['basket'].keys())[0]).restaurant.id != product.restaurant.id:
                await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                        message='Все товары должны быть из одного ресторана')
                return

        session['last_interaction'] = datetime.now()
        session['basket'][product_id] = count
        
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='Товар {} добавлен в корзину'.format(product_id))

    elif re.match(r'/amount \d+ \d+', content):
        _, product_id, count = content.split()
        
        if product_id not in session['basket']:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Этого товара нет в корзине')
            return
        
        session['last_interaction'] = datetime.now()
        session['basket'][product_id] = count
        
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='Количество товара {} изменено на {}'.format(product_id, count))

    elif re.match(r'/del \d+', content):
        product_id = content.split()[1]

        if product_id not in session['basket']:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Этого товара нет в корзине')
            return
        
        session['basket'].pop(product_id)

        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='Товар {} удалён из корзины'.format(product_id))

    elif content == '/basket':
        if not session['basket']:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Корзина пуста')
            return
        
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='\n'.join('{} - {} шт.'.format(
                                    db_session.query(Product).get(product_id).name,
                                    count
                                ) for product_id, count in session['basket'].items()))
    elif re.match(r'/order \+7\d{10}', content):
        if not session['basket']:
            await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                    message='Корзина пуста!')
            return
        
        phone_number = content.split()[1]
        
        customer = db_session.query(Customer).filter(Customer.phone_number == phone_number).first()

        if not customer:
            customer = Customer(phone_number=phone_number)

        order = Order(customer=customer, destination=session['address'])
        
        for product_id, count in session['basket'].items():
            product = db_session.query(Product).get(product_id)
            order_item = OrderItem(product=product, count=count)
            order.restaurant = product.restaurant
            order.order_items.append(order_item)
        
        db_session.add(order)
        db_session.commit()

        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='Заказ отправлен на обработку!')
    
    else:
        await api.messages.send(user_id=session['user_id'], random_id=random_id(),
                                message='Неизвестная команда или неверные аругменты')



async def on_message(api, message):
    user_id = message['from_id']

    if user_id in sessions:
        await handle_session(api, message['text'], sessions[user_id])
    else:
        await api.messages.send(user_id=user_id, random_id=random_id(),
                                message=help_str)
        
        sessions[user_id] = {'user_id': user_id, 
                             'last_interaction': datetime.now(), 
                             'basket': dict(),
                             'current_restaurant': -1,
                             'address': ''}
        
        
async def garbage_collector():
    while True:
        for session in sessions:
            if (datetime.now() - sessions[session]['last_interaction']).total_seconds() > 600:
                sessions.pop(session)
        
        await asyncio.sleep(30)


async def listener():
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
