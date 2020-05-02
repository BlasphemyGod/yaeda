from wtforms import Form, StringField, IntegerField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired
from wtforms import ValidationError

from .db import Session
from .db.models import Restaurant

import re


class PhoneNumberValidator:
    def __init__(self, message='Номер телефона не подходит под шаблон +7**********'):
        self.message = message
    
    def __call__(self, form, field):
        if not re.match(r'\+7\d{10}', field.data) and not re.match(r'8\d{10}', field.data):
            raise ValidationError(self.message)
        
        
class UniqueRestaurantName:
    def __init__(self, message='Название ресторана должно быть уникальным'):
        self.message = message
        
    def __call__(self, form, field):
        if Session().query(Restaurant).filter(Restaurant.name == field.data).first():
            raise ValidationError(self.message)


class RestaurantRegisterForm(Form):
    name = StringField('Название ресторана', [DataRequired(), UniqueRestaurantName()])
    phone_number = StringField('Контактный телефон', [DataRequired(), PhoneNumberValidator()])
    address = StringField('Адрес', [DataRequired()])
    serve_area = IntegerField('Область доставки(в метрах)', [DataRequired()])
    login = StringField('Логин', [DataRequired()])
    password = PasswordField('Пароль', [DataRequired()])


class RestaurantLoginForm(Form):
    login = StringField('Логин', [DataRequired()])
    password = PasswordField('Пароль', [DataRequired()])
    
    
class ProductForm(Form):
    name = StringField('Название продукта', [DataRequired()])
    price = IntegerField('Цена в руб.', [DataRequired()])
    description = TextAreaField('Описание', [DataRequired()])
    
    def validate_price(self, field):
        if field.data < 0:
            raise ValidationError('Цена должна быть целым неотрицательным числом')
    
    
class OrderForm(Form):
    phone_number = StringField('Номер телефона', [DataRequired(), PhoneNumberValidator()])
    address_city = StringField('Город', [DataRequired()])
    address_street = StringField('Улица', [DataRequired()])
    address_house = StringField('Дом', [DataRequired()])
    address_apartment = IntegerField('Номер квартиры', [DataRequired()])
    description = StringField('Примечание к заказу')


class RestaurantEditForm(Form):
    name = StringField('Название ресторана', [UniqueRestaurantName()])
    phone_number = StringField('Контактный телефон', [PhoneNumberValidator()])
    address = StringField('Адрес')
    serve_area = IntegerField('Область доставки(в метрах)')


class OrdersReceiveForm(Form):
    phone_number = StringField('Номер телефона', [PhoneNumberValidator()])


class RestaurantSelectionForm(Form):
    address = StringField('Адрес', [DataRequired()])


class CourierRegisterForm(Form):
    vk_id = IntegerField('Идентификатор вконтакте', [DataRequired()])
