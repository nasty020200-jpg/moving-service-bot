# -*- coding: utf-8 -*-
from flask import Flask, request
import telebot
import os
import json

# Токен бота
BOT_TOKEN = '8367829067:AAFCZZji7PUZPCUmNcFRi-1E958bnjxVNpk'

# Файл для хранения Admin Chat ID
ADMIN_FILE = '/tmp/admin_chat_id.txt'

# Chat ID менеджера
ADMIN_CHAT_ID = None

# Загружаем Admin Chat ID из файла при запуске
if os.path.exists(ADMIN_FILE):
    try:
        with open(ADMIN_FILE, 'r') as f:
            ADMIN_CHAT_ID = int(f.read().strip())
            print(f"✅ Загружен Admin Chat ID: {ADMIN_CHAT_ID}")
    except:
        pass

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Словарь для хранения состояний пользователей
user_states = {}
user_data = {}

# Состояния диалога для переездов
STATE_WAITING_ADDRESS = 'waiting_address'
STATE_WAITING_CARGO = 'waiting_cargo'
STATE_WAITING_CONTACT = 'waiting_contact'

# Состояния диалога для вывоза мусора
STATE_WASTE_WHAT = 'waste_what'
STATE_WASTE_CONTACT = 'waste_contact'

# Состояния диалога для услуг грузчиков
STATE_LOADER_TASK = 'loader_task'
STATE_LOADER_CONTACT = 'loader_contact'

# Состояния диалога для доставки/такси
STATE_DELIVERY_INFO = 'delivery_info'
STATE_DELIVERY_CONTACT = 'delivery_contact'

def get_main_keyboard():
    """Создает основную клавиатуру"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Первый ряд - две кнопки
    btn1 = telebot.types.KeyboardButton('🏠 Переезды')
    btn2 = telebot.types.KeyboardButton('💪 Услуги грузчиков (без машины)')
    markup.row(btn1, btn2)
    
    # Второй ряд - две кнопки
    btn3 = telebot.types.KeyboardButton('🗑 Вывоз мусора')
    btn4 = telebot.types.KeyboardButton('🚛 Доставка / Такси')
    markup.row(btn3, btn4)
    
    # Третий ряд - одна кнопка по центру
    btn5 = telebot.types.KeyboardButton('📞 Контакты / Связь')
    markup.row(btn5)
    
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    # Сбрасываем состояние пользователя
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_data:
        del user_data[user_id]
    
    welcome_text = """Добро пожаловать в сервис грузоперевозок! 👋

Выберите интересующую вас услугу:"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['setadmin'])
def set_admin(message):
    """Команда для установки администратора"""
    global ADMIN_CHAT_ID
    ADMIN_CHAT_ID = message.chat.id
    
    # Сохраняем в файл
    with open(ADMIN_FILE, 'w') as f:
        f.write(str(ADMIN_CHAT_ID))
    
    bot.send_message(message.chat.id, f"✅ Вы установлены как администратор!\nВаш Chat ID: {ADMIN_CHAT_ID}\n\nТеперь все заявки будут приходить вам.")

@bot.message_handler(func=lambda message: message.forward_from_chat is not None)
def handle_forwarded_from_channel(message):
    """Обработчик для пересланных сообщений из канала"""
    if message.forward_from_chat.type == 'channel':
        global ADMIN_CHAT_ID
        ADMIN_CHAT_ID = message.forward_from_chat.id
        
        # Сохраняем в файл
        with open(ADMIN_FILE, 'w') as f:
            f.write(str(ADMIN_CHAT_ID))
        
        channel_title = message.forward_from_chat.title
        bot.send_message(message.chat.id, f"✅ Канал настроен!\n\n📢 Название: {channel_title}\n🆔 Chat ID: {ADMIN_CHAT_ID}\n\nТеперь все заявки будут приходить в этот канал.")

@bot.message_handler(func=lambda message: message.text == '🏠 Переезды')
def moving_start(message):
    user_id = message.from_user.id
    
    # Инициализируем данные пользователя
    user_data[user_id] = {
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'user_id': user_id
    }
    
    # Устанавливаем состояние ожидания адреса
    user_states[user_id] = STATE_WAITING_ADDRESS
    
    text = """📍 Напишите адреса: Откуда ➡️ Куда. 
🏢 Напишите этажи и наличие лифтов по двум адресам."""
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == '💪 Услуги грузчиков (без машины)')
def loaders_start(message):
    user_id = message.from_user.id
    
    user_data[user_id] = {
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'user_id': user_id,
        'service_type': 'Услуги грузчиков'
    }
    
    user_states[user_id] = STATE_LOADER_TASK
    
    text = """💪 Заказ грузчиков

Чтобы я быстро посчитал цену, напишите одним сообщением ответы на 4 вопроса:

1️⃣ Что делать? (Спустить диван / Поднять 50 мешков / Разгрузить фуру). 
2️⃣ Этаж и Лифт? (Есть ли лифт, какой этаж). 
3️⃣ Адрес? (Улица или район). 
4️⃣ Нужна ли машина? (Или только грузчики).

👇 Просто напишите всё это в одном сообщении ниже:"""
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == '🗑 Вывоз мусора')
def waste_removal_start(message):
    user_id = message.from_user.id
    
    user_data[user_id] = {
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'user_id': user_id,
        'service_type': 'Вывоз мусора'
    }
    
    user_states[user_id] = STATE_WASTE_WHAT
    
    text = """🗑 1️⃣ Что вывозим? (Мешки, мебель,) 
Напишите приблизительно количество
🗑 2️⃣ Откуда? (Улица, номер дома)
🗑 3️⃣ Какой этаж? (Есть ли лифт, можно ли на нем спускать мусор?)"""
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == '🚛 Доставка / Такси')
def delivery_start(message):
    user_id = message.from_user.id
    
    user_data[user_id] = {
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'user_id': user_id,
        'service_type': 'Доставка/Такси'
    }
    
    user_states[user_id] = STATE_DELIVERY_INFO
    
    text = """🚛 Чтобы вызвать машину, напишите одним сообщением:

1️⃣ Откуда забрать? (Название магазина или адрес). 
2️⃣ Куда везти? (Улица/Район). 
3️⃣ Что именно везем? (Например: «Стиралку и 2 коробки»). 
4️⃣ Нужны ли грузчики? (Или вы погрузите сами?).

👇 Жду ваш ответ ниже:"""
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == '📞 Контакты / Связь')
def contacts(message):
    text = """📞 КОНТАКТЫ

📲 Telegram/WhatsApp: @PereezdBatumiGE
📱 Телефон: +995597048630

🕐 Работаем 24/7 по Батуми и всей Аджарии

Пишите или звоните - ответим быстро!"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    
    # ПЕРЕЕЗДЫ
    if state == STATE_WAITING_ADDRESS:
        user_data[user_id]['address'] = message.text
        user_states[user_id] = STATE_WAITING_CARGO
        
        text = """📦 Что именно перевозим? Опишите груз.

Пример: 
— Холодильник (высокий), стиральная машина."""
        
        bot.send_message(message.chat.id, text)
    
    elif state == STATE_WAITING_CARGO:
        user_data[user_id]['cargo'] = message.text
        user_states[user_id] = STATE_WAITING_CONTACT
        
        text = """📱 Спасибо за ответы!

Пожалуйста, оставьте контакт (номер телефона или ваш телеграм)"""
        
        bot.send_message(message.chat.id, text)
    
    elif state == STATE_WAITING_CONTACT:
        user_data[user_id]['contact'] = message.text
        data = user_data[user_id]
        
        manager_message = f"""🚀 НОВАЯ ЗАЯВКА НА ПЕРЕЕЗД

👤 Клиент: {data.get('first_name', 'Не указано')}
🆔 Username: @{data.get('username', 'нет username')}
🆔 ID: {data['user_id']}

📍 Адреса и этажи:
{data['address']}

📦 Груз:
{data['cargo']}

📞 Контакт клиента:
{data['contact']}"""
        
        if ADMIN_CHAT_ID:
            try:
                bot.send_message(ADMIN_CHAT_ID, manager_message)
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
        
        confirmation_text = """✅ Спасибо! Ваша заявка принята.

Мы получили ваши данные. Менеджер свяжется с вами в ближайшее время."""
        
        bot.send_message(message.chat.id, confirmation_text, reply_markup=get_main_keyboard())
        
        del user_states[user_id]
        del user_data[user_id]
    
    # ВЫВОЗ МУСОРА
    elif state == STATE_WASTE_WHAT:
        user_data[user_id]['waste_info'] = message.text
        user_states[user_id] = STATE_WASTE_CONTACT
        
        text = """📱 Спасибо за ответы!

Пожалуйста, оставьте контакт (номер телефона или ваш телеграм)"""
        
        bot.send_message(message.chat.id, text)
    
    elif state == STATE_WASTE_CONTACT:
        user_data[user_id]['waste_contact'] = message.text
        data = user_data[user_id]
        
        manager_message = f"""🗑 НОВАЯ ЗАЯВКА НА ВЫВОЗ МУСОРА

👤 Клиент: {data.get('first_name', 'Не указано')}
🆔 Username: @{data.get('username', 'нет username')}
🆔 ID: {data['user_id']}

📋 Информация о заказе:
{data['waste_info']}

📞 Контакт клиента:
{data['waste_contact']}"""
        
        if ADMIN_CHAT_ID:
            try:
                bot.send_message(ADMIN_CHAT_ID, manager_message)
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        confirmation_text = """✅ Спасибо! Ваша заявка принята.

Мы получили ваши данные. Менеджер свяжется с вами в ближайшее время."""
        
        bot.send_message(message.chat.id, confirmation_text, reply_markup=get_main_keyboard())
        del user_states[user_id]
        del user_data[user_id]
    
    # УСЛУГИ ГРУЗЧИКОВ
    elif state == STATE_LOADER_TASK:
        user_data[user_id]['loader_info'] = message.text
        user_states[user_id] = STATE_LOADER_CONTACT
        bot.send_message(message.chat.id, "📱 Спасибо за ответы!\n\nПожалуйста, оставьте контакт (номер телефона или ваш телеграм)")
    
    elif state == STATE_LOADER_CONTACT:
        user_data[user_id]['loader_contact'] = message.text
        data = user_data[user_id]
        
        manager_message = f"""💪 НОВАЯ ЗАЯВКА НА УСЛУГИ ГРУЗЧИКОВ

👤 Клиент: {data.get('first_name', 'Не указано')}
🆔 Username: @{data.get('username', 'нет username')}
🆔 ID: {data['user_id']}

📋 Информация о заказе:
{data['loader_info']}

📞 Контакт клиента:
{data['loader_contact']}"""
        
        if ADMIN_CHAT_ID:
            try:
                bot.send_message(ADMIN_CHAT_ID, manager_message)
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        bot.send_message(message.chat.id, "✅ Спасибо! Ваша заявка принята.\n\nМы получили ваши данные. Менеджер свяжется с вами в ближайшее время.", reply_markup=get_main_keyboard())
        del user_states[user_id]
        del user_data[user_id]
    
    # ДОСТАВКА/ТАКСИ
    elif state == STATE_DELIVERY_INFO:
        user_data[user_id]['delivery_info'] = message.text
        user_states[user_id] = STATE_DELIVERY_CONTACT
        bot.send_message(message.chat.id, "📱 Спасибо за ответы!\n\nПожалуйста, оставьте контакт (номер телефона или ваш телеграм)")
    
    elif state == STATE_DELIVERY_CONTACT:
        user_data[user_id]['delivery_contact'] = message.text
        data = user_data[user_id]
        
        manager_message = f"""🚛 НОВАЯ ЗАЯВКА НА ДОСТАВКУ/ТАКСИ

👤 Клиент: {data.get('first_name', 'Не указано')}
🆔 Username: @{data.get('username', 'нет username')}
🆔 ID: {data['user_id']}

📋 Информация о заказе:
{data['delivery_info']}

📞 Контакт клиента:
{data['delivery_contact']}"""
        
        if ADMIN_CHAT_ID:
            try:
                bot.send_message(ADMIN_CHAT_ID, manager_message)
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        bot.send_message(message.chat.id, "✅ Спасибо! Ваша заявка принята.\n\nМы получили ваши данные. Менеджер свяжется с вами в ближайшее время.", reply_markup=get_main_keyboard())
        del user_states[user_id]
        del user_data[user_id]

# Webhook endpoint
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Bad Request', 400

# Health check endpoint
@app.route('/', methods=['GET'])
def index():
    return 'Bot is running!', 200
