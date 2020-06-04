## Установка
Сначала склонируйте репозиторий:

    git clone https://github.com/BurnQuid/yaeda
    
После этого установите необходимые зависимости:

    pip install -r requirements.txt
    
## Настройка
По-умолчанию сервер запускается на порте 8080,
если иного не указано в переменной окружения 'PORT':
```python
#./main.py:12

config.bind = ['0.0.0.0:' + os.environ.get('PORT', '8080')]
```

В проекте используется бот вконтакте, поэтому для запуска 
необходимо его создать или использовать существующий. Если 
такого нет, то создайте сообщество вк. Далее в 
управление->сообщения включите сообщения сообщества.
В настройки->Работа С API создайте ключ доступа с правами
доступа к управлению сообществом и сообщений сообщества. 
Включите Long Poll API. Измените константы в файле 
`./yaeda/bot.py`:
```python
#./yaeda/bot.py:12-13

TOKEN = ''  # Сюда ключ
GROUP_ID = 0  # Сюда id сообщества
```

Для тестирования используется sqlite бд в памяти, если иное
не указано в переменной окружения 'DATABASE_URL':
```python
#./yaeda/db/__init__.py:8

engine = sqlalchemy.create_engine(os.environ.get('DATABASE_URL', 'sqlite:///:memory:'))
```

## Описание
Yaeda - это сервис как для клиентов, 
заказывающих еду на дом, так и для 
компаний, которым сразу же предоставляется интерфейс для 
отслеживания заказов и их выполнения.

### Клиент
Для того, чтобы сделать заказ, необходимо ввести свой адрес 
на главной странице сайта. На основе адреса yaeda подберёт
все доступные для доставки рестораны. После перехода на страницу
ресторана, клиент выбирает нужные товары, добавляя их в корзину.
На странице корзины покупатель перепроверяет всё, что заказал и
продолжает покупку. После перехода на страницу оплаты нужно
ввести свой номер телефона и адрес. Больше ничего не нужно! 
Заказ автоматически отправляется в выбранный ресторан, а курьер
уже готов к доставке. Свои заказы клиент всегда может проверить
на странице заказов

### Ресторан
Сначала ресторан регистрируется на сайте, вводя свой адрес, 
область доставки, название и т.д. Далее создаёт меню на своей 
странице. Чтобы увидеть все заказы, ресторан переходит на 
страницу заказов и видит всё, что нужно. Ресторан также изменяет
состояние заказа от "обработки" до "доставляется". Как только 
заказ готов, курьер может его забрать и отправиться в путь

### Курьер
Будущий курьер заходит на страницу желанного ресторана и 
регистрируется на роль курьера, вводя свой id вк. Далее он
должен подтвердить свою страницу, написав боту нужную команду.
Когда курьеру приходит заказ, то бот его оповещает, давая адрес 
и номер телефона заказчика. Курьер ещё до готовности заказа 
отправляется в ресторан. Доставив заказ, курьер пишет боту о
завершении заказа. Рабочий день курьер начинает командой, как
заканчивает его тоже командой