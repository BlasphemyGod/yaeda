from quart import render_template, request, session, url_for, redirect, abort
from werkzeug.security import generate_password_hash, check_password_hash

from . import app
from .db import db_session
from .db.models import Customer, Restaurant, Order
from .forms import RestaurantRegisterForm, RestaurantLoginForm, RestaurantEditForm
from .helpers import get_current_restaurant, logged_in, basket_len


@app.route('/register', methods=['GET', 'POST'])
async def register():
    if logged_in():
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        form = RestaurantRegisterForm(await request.form)
        
        if form.validate():
            restaurant = Restaurant(name=form.name.data,
                                    phone_number=form.phone_number.data,
                                    address=form.address.data,
                                    serve_area=form.serve_area.data,
                                    login=form.login.data,
                                    password=generate_password_hash(form.password.data))
            
            db_session.add(restaurant)
            db_session.commit()
            
            return redirect(url_for('login'))
        
        return await render_template('restaurant_register.html', title='Регистрация', form=form,
                                     basket_len=basket_len())
    
    form = RestaurantRegisterForm()
    
    return await render_template('restaurant_register.html', title='Регистрация', form=form,
                                 basket_len=basket_len())


@app.route('/login', methods=['GET', 'POST'])
async def login():
    if logged_in():
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        form = RestaurantLoginForm(await request.form)
        
        if form.validate():
            restaurant = db_session.query(Restaurant).filter(Restaurant.login == form.login.data).first()
            
            if not restaurant:
                return await render_template('restaurant_login.html', title='Авторизация', form=form,
                                             message='Неверный логин или пароль',
                                             basket_len=basket_len())
            
            if check_password_hash(restaurant.password, form.password.data):
                session['restaurant_id'] = restaurant.id
                
                return redirect(url_for('home'))

            return await render_template('restaurant_login.html', title='Авторизация', form=form,
                                         message='Неверный логин или пароль',
                                         basket_len=basket_len())
        
        return await render_template('restaurant_login.html', title='Авторизация', form=form,
                                     basket_len=basket_len())
    
    form = RestaurantLoginForm()
    
    return await render_template('restaurant_login.html', title='Авторизация', form=form,
                                 basket_len=basket_len())


@app.route('/logout')
async def logout():
    if logged_in():
        session.pop('restaurant_id')
        
    return redirect(url_for('login'))


@app.route('/')
@app.route('/home')
async def home():
    return await render_template('home.html', title='Главная страница', logged_in=logged_in(),
                                 restaurant=(get_current_restaurant() if 'restaurant' in session else None),
                                 basket_len=basket_len())


@app.route('/restaurant')
@app.route('/restaurant/<int:restaurant_id>')
async def restaurant(restaurant_id=0):
    if not restaurant_id:
        if 'restaurant_id' not in session:
            return redirect(url_for('login'))
        restaurant = get_current_restaurant()
    else:
        restaurant = db_session.query(Restaurant).get(restaurant_id)

        if not restaurant:
            abort(404)

    return await render_template('restaurant_profile.html', title='Ресторан {}'.format(restaurant.name),
                                 logged_in=logged_in(), restaurant=restaurant, 
                                 owner=(restaurant.id == get_current_restaurant().id
                                        if 'restaurant_id' in session else ''),
                                 basket_len=basket_len())


@app.route('/restaurant/edit', methods=['GET', 'POST'])
async def restaurant_edit():
    if not logged_in():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        form = RestaurantEditForm(await request.form)
        
        if form.validate():
            restaurant = get_current_restaurant()

            restaurant.name = form.name.data or restaurant.name
            restaurant.phone_number = form.phone_number.data or restaurant.phone_number
            restaurant.address = form.address.data or restaurant.address
            restaurant.serve_area = form.serve_area.data or restaurant.serve_area
            
            db_session.merge(restaurant)
            db_session.commit()
            
            return redirect(url_for('restaurant'))
        
        return await render_template('restaurant_edit.html', title='Редактировать данные',
                                     logged_in=True, form=form,
                                     basket_len=basket_len())
    
    form = RestaurantEditForm()

    return await render_template('restaurant_edit.html', title='Редактирование данных',
                                 logged_in=True, form=form,
                                 basket_len=basket_len())
