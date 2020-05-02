from quart import blueprints, url_for, redirect, request, render_template

from yaeda.db import db_session
from yaeda.db.models import Courier, Restaurant

from yaeda.helpers import logged_in, basket_len
from yaeda.forms import CourierRegisterForm


blueprint = blueprints.Blueprint('courier', __name__)


@blueprint.route('/courier/new', methods=['GET', 'POST'])
async def courier_new():
    restaurant_id = request.args.get('restaurant')

    if not restaurant_id:
        return redirect('home')

    restaurant = db_session.query(Restaurant).get(restaurant_id)

    if request.method == 'POST':
        form = CourierRegisterForm(await request.form)

        if form.validate():
            courier = Courier(vk_id=form.vk_id.data)

            db_session.add(courier)

            return redirect('courier.courier_finish')

        return await render_template('courier_new.html', title='Стать курьером',
                                     logged_in=logged_in(), basket_len=basket_len(),
                                     form=form, restaurant=restaurant)

    form = CourierRegisterForm()

    return await render_template('courier_new.html', title='Стать курьером',
                                 logged_in=logged_in(), basket_len=basket_len(),
                                 form=form, restaurant=restaurant)


@blueprint.route('/courier/finish')
async def courier_finish():
    return await render_template('courier_finish.html', title='Почти курьер',
                                 logged_in=logged_in(), basket_len=basket_len())
