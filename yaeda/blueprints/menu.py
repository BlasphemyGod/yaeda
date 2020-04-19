from quart import blueprints, redirect, url_for, request, render_template, abort, session

from yaeda.forms import ProductForm
from yaeda.helpers import logged_in, get_current_restaurant, basket_len
from yaeda.db import db_session
from yaeda.db.models import Product


blueprint = blueprints.Blueprint('menu', __name__)


@blueprint.route('/menu/remove/<int:product_id>')
async def menu_remove(product_id):
    if not logged_in():
        return redirect(url_for('login'))
    
    product = db_session.query(Product).get(product_id)
    
    if not product:
        abort(404)
    
    if product.restaurant.id != get_current_restaurant().id:
        abort(403)
        
    db_session.delete(product)
    db_session.commit()

    return redirect(url_for('restaurant', restaurant_id=product.restaurant.id))
    
    
@blueprint.route('/menu/add/', methods=['GET', 'POST'])
async def menu_add():
    if not logged_in():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        form = ProductForm(await request.form)
        
        if form.validate():
            restaurant = get_current_restaurant()
            
            product = Product(name=form.name.data,
                              price=form.price.data,
                              description=form.description.data)
            
            restaurant.menu.append(product)
            db_session.commit()

            return redirect(url_for('restaurant'))
        
        return await render_template('menu_add.html', title='Дополнить меню',
                                     form=form, logged_in=True,
                                     basket_len=basket_len())
        
    form = ProductForm()
    
    return await render_template('menu_add.html', title='Дополнить меню',
                                 form=form, logged_in=True,
                                 basket_len=basket_len())
