import telebot
from telebot import types
import sqlite3
import json
import os
import re
import threading

# Путь к JSON с товарами
DATA_FOLDER = "data"
PRODUCTS_FILE = os.path.join(DATA_FOLDER, "products.json")

# Загрузка данных о товарах из JSON-файла
with open(PRODUCTS_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)
    categories = {category['name']: category['products'] for category in data['categories']}

# Настройка токена бота
bot_token = "8126590226:AAEbDpzt7KZj8QHtj8tECgAonAQP3bKjVRA"
bot = telebot.TeleBot(bot_token)

# Файл для хранения информации о пользователях
USER_DATA_FILE = "user_data.json"
# Флаг для управления запуском и остановкой бота
is_bot_running = True

# Названия категорий и кнопок для разных языков
LANGUAGE_LABELS = {
    "Русский": {
        "guitars": "🎸 Гитары",
        "drums": "🥁 Ударные",
        "keyboards": "🎹 Клавишные",
        "winds": "🎺 Духовые",
        "cart": "🛒 Корзина",
        "orders": "📦 Мои заказы",
        "welcome": "Добро пожаловать в интернет-магазин музыкальных инструментов! Выберите категорию или действие:",
        "invalid_name": "Имя и фамилия должны содержать только буквы и не должны содержать цифр или специальных символов.",
        "stop_message": "Бот остановлен. До новых встреч!"
    },
    "Українська": {
        "guitars": "🎸 Гітари",
        "drums": "🥁 Ударні",
        "keyboards": "🎹 Клавішні",
        "winds": "🎺 Духові",
        "cart": "🛒 Кошик",
        "orders": "📦 Мої замовлення",
        "welcome": "Ласкаво просимо до інтернет-магазину музичних інструментів! Виберіть категорію або дію:",
        "invalid_name": "Ім'я та прізвище повинні містити тільки літери і не повинні містити цифр або спеціальних символів.",
        "stop_message": "Бот зупинено. До нових зустрічей!"
    },
    "English": {
        "guitars": "🎸 Guitars",
        "drums": "🥁 Drums",
        "keyboards": "🎹 Keyboards",
        "winds": "🎺 Wind Instruments",
        "cart": "🛒 Cart",
        "orders": "📦 My Orders",
        "welcome": "Welcome to the online musical instrument store! Choose a category or action:",
        "invalid_name": "First and last name should only contain letters and should not contain numbers or special characters.",
        "stop_message": "Bot stopped. See you next time!"
    }
}

# Функция для сохранения данных пользователя в JSON
def save_user_data(user_id, language, first_name, last_name, contact):
    try:
        user_data = {}
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as file:
                user_data = json.load(file)
        except FileNotFoundError:
            user_data = {}

        user_data[user_id] = {
            "language": language,
            "first_name": first_name,
            "last_name": last_name,
            "contact": contact
        }

        with open(USER_DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(user_data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователя: {e}")

# Подключение к базе данных
def connect_db():
    return sqlite3.connect("your_database.db")

# Функция для запуска бота
def polling():
    global is_bot_running
    while is_bot_running:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка при работе бота: {e}")
            bot.stop_polling()

# Команда /start для запуска и перезапуска бота
@bot.message_handler(commands=["start"])
def start_command(message):
    global is_bot_running
    if not is_bot_running:
        is_bot_running = True
        threading.Thread(target=polling).start()
        bot.send_message(message.chat.id, "Бот снова запущен!")
    else:
        bot.send_message(message.chat.id, "Бот уже работает.")
    ask_language(message)

# Команда /stop для остановки бота
@bot.message_handler(commands=["stop"])
def stop_command(message):
    global is_bot_running
    if is_bot_running:
        is_bot_running = False
        bot.stop_polling()
        bot.send_message(message.chat.id, "Бот остановлен. Используйте /start для перезапуска.")

# Получение языка пользователя
def get_user_language(user_id):
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as file:
            user_data = json.load(file)
            return user_data.get(str(user_id), {}).get("language", "Русский")
    except FileNotFoundError:
        return "Русский"

# Запрос языка общения
def ask_language(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_ru = types.KeyboardButton("Русский")
    btn_ua = types.KeyboardButton("Українська")
    btn_en = types.KeyboardButton("English")
    markup.add(btn_ru, btn_ua, btn_en)
    bot.send_message(message.chat.id, "На каком языке вам будет удобно общаться?", reply_markup=markup)

# Обработка выбора языка
@bot.message_handler(func=lambda message: message.text in LANGUAGE_LABELS)
def handle_language(message):
    language = message.text
    bot.send_message(message.chat.id, "Пожалуйста, отправьте свой контактный номер.",
                     reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                         types.KeyboardButton("Отправить контакт", request_contact=True)))
    bot.register_next_step_handler(message, handle_contact, language)

# Проверка имени и фамилии на наличие только букв
def is_valid_name(full_name):
    return bool(re.match(r'^[a-zA-Zа-яА-ЯёЁіІїЇєЄ\s-]+$', full_name))

# Обработка имени и фамилии
def handle_name(message, contact, language):
    labels = LANGUAGE_LABELS[language]
    full_name = message.text
    if not is_valid_name(full_name):
        bot.send_message(message.chat.id, labels["invalid_name"])
        bot.register_next_step_handler(message, handle_name, contact, language)
        return

    first_name, last_name = full_name.split(maxsplit=1) if ' ' in full_name else (full_name, "")
    save_user_data(message.chat.id, language, first_name, last_name, contact)
    bot.send_message(message.chat.id, "Спасибо! Ваши данные сохранены.")
    send_main_menu(message, language)

# Отправка главного меню
def send_main_menu(message, language):
    labels = LANGUAGE_LABELS[language]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton(labels["guitars"])
    btn2 = types.KeyboardButton(labels["drums"])
    btn3 = types.KeyboardButton(labels["keyboards"])
    btn4 = types.KeyboardButton(labels["winds"])
    btn5 = types.KeyboardButton(labels["cart"])
    btn6 = types.KeyboardButton(labels["orders"])
    markup.add(btn1, btn2, btn3, btn4)
    markup.add(btn5, btn6)
    bot.send_message(message.chat.id, labels["welcome"], reply_markup=markup)

# Запуск бота
if __name__ == "__main__":
    polling()