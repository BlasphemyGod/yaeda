from quart import blueprints, session, url_for, redirect, render_template, request

import asyncio

from yaeda.db import Session
from yaeda.db.models import Customer, Order, OrderItem, Restaurant, Product
from yaeda.helpers import logged_in, basket_len, get_toponym, toponyms_distance
from yaeda.forms import OrdersReceiveForm, OrderForm


blueprint = blueprints.Blueprint('order', __name__)


async def make_order_template(**context):
    return await render_template('order_make.html', logged_in=logged_in(), 
                                 basket_len=basket_len(), title='Оформление заказа',
                                 **context)
    
    
async def orders_template(**context):
    return await render_template('orders.html', logged_in=logged_in(),
                                 basket_len=basket_len(), title='Заказы',
                                 **context)


@blueprint.route('/orders', methods=['GET', 'POST'])
async def orders():
    if request.method == 'POST':
        form = OrdersReceiveForm(await request.form)

        if form.validate():
            db_session = Session()
            
            customer = db_session.query(Customer).filter(
                Customer.phone_number == form.phone_number.data
            ).first()
            
            if not customer:
                return await orders_template(message='По этому номеру не было сделано ни одного заказа',
                                             form=form)

            orders = customer.orders
            
            ready_orders = [order for order in orders if order.state == 'Готово']
            not_ready_orders = [order for order in orders if order.state != 'Готово']
            
            return await orders_template(form=form, ready_orders=ready_orders, 
                                         not_ready_orders=not_ready_orders)

    form = OrdersReceiveForm()
    
    return await orders_template(form=form)


@blueprint.route('/order/make', methods=['GET', 'POST'])
async def order_make():
    if 'basket' not in session or not session['basket']:
        return redirect(url_for('home'))

    if request.method == 'POST':
        form = OrderForm(await request.form)

        if form.validate():
            db_session = Session()
            
            first_product = db_session.query(Product).get(
                int(list(session['basket'].keys())[0])
            )
            
            restaurant = first_product.restaurant
            
            customer_future = asyncio.ensure_future(get_toponym(form.address.data))
            restaurant_future = asyncio.ensure_future(get_toponym(restaurant.address))
            
            await asyncio.wait([customer_future, restaurant_future])
            
            customer_toponym = customer_future.result()
            restaurant_toponym = restaurant_future.result()
            
            if not customer_toponym or not restaurant_toponym:
                return await make_order_template(form=form, message='Не удалось определить адрес заказчика или ресторана')
            
            if restaurant.serve_area < toponyms_distance(customer_toponym, restaurant_toponym):
                return await make_order_template(form=form, message='Вы находитесь вне зоны обслуживания ресторана')
            
            customer = db_session.query(Customer).filter(
                Customer.phone_number == form.phone_number.data
            ).first()
            
            if not customer:
                customer = Customer(phone_number=form.phone_number.data)
                
            order = Order(customer=customer, destination=customer_toponym['metaDataProperty']['GeocoderMetaData']['text'])
            
            for product_id in session['basket']:
                order_item = OrderItem(count=session['basket'][product_id],
                                       product_id=product_id, order=order)
                db_session.add(order_item)

            db_session.commit()
            
            session['basket'].clear()
            session.modified = True
            
            return await make_order_template(form=form, success=True, message='Заказ отправлен на обработку')
        
        return await make_order_template(form=form)
        
    form = OrderForm()
    
    return await make_order_template(form=form)
