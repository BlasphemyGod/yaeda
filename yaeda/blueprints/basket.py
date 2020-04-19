from quart import blueprints, abort, url_for, session, render_template, redirect, request
from collections import Counter

from yaeda.db.models import Product
from yaeda.db import Session
from yaeda.helpers import logged_in, basket_len


blueprint = blueprints.Blueprint('basket', __name__)


@blueprint.route('/basket/clear')
async def basket_clear():
    if 'basket' in session:
        session['basket'].clear()
    
    return redirect(url_for('basket'))


@blueprint.route('/basket/add/<int:product_id>')
async def basket_add(product_id):
    db_session = Session()
    
    product = db_session.query(Product).get(product_id)
    
    if not product:
        abort(404)
        
    product_id = str(product_id)

    if 'basket' not in session:
        session['basket'] = {product_id: 1}
    else:
        if session['basket']:
            first_product = db_session.query(Product).get(int(list(session['basket'].keys())[0]))
            if product.restaurant.id != first_product.restaurant.id:
                return 'not ok'
        if product_id in session['basket']:
            session['basket'][product_id] += 1
        else:
            session['basket'][product_id] = 1
            
        session.modified = True

    return redirect(request.referrer or url_for('restaurant', restaurant_id=product.restaurant.id))


@blueprint.route('/basket/remove/<int:product_id>')
async def basket_remove(product_id):
    if 'basket' not in session:
        return 'not ok'
    
    product_id = str(product_id)
    
    session.modified = True
    
    if product_id in session['basket']:
        session['basket'][product_id] -= 1
        
        if session['basket'][product_id] <= 0:
            session['basket'].pop(product_id)
            
        return redirect(request.referrer or url_for('basket.basket'))

    abort(404)
    
    
@blueprint.route('/basket/remove/<int:product_id>/all')
async def basket_remove_all(product_id):
    if 'basket' not in session:
        return 'not ok'
    
    product_id = str(product_id)

    if product_id in session['basket']:
        session['basket'].pop(product_id)
        session.modified = True
        
        return redirect(request.referrer or url_for('basket.basket'))

    abort(404)
    
    
@blueprint.route('/basket')
async def basket():
    if 'basket' not in session:
        session['basket'] = dict()
        
    db_session = Session()
    
    products = list()
    
    for product_id, count in session['basket'].items():
        products.append((db_session.query(Product).get(product_id), count))
        
    return await render_template('basket.html', title='Корзина', products=products,
                                 basket_len=basket_len(), logged_in=logged_in())
    