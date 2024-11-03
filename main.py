import telebot
from telebot import types
import sqlite3
import json

# Загрузка данных о товарах из JSON-файла
with open("products.json", "r", encoding="utf-8") as file:
    data = json.load(file)
    categories = {category['name']: category['products'] for category in data['categories']}

bot = telebot.TeleBot("8126590226:AAEbDpzt7KZj8QHtj8tECgAonAQP3bKjVRA")

# Файл для хранения информации о пользователях
USER_DATA_FILE = "user_data.json"

# Функция для сохранения данных пользователя в JSON
def save_user_data(user_id, language, first_name, last_name, contact):
    try:
        user_data = {}
        # Проверка на существование файла
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as file:
                user_data = json.load(file)
        except FileNotFoundError:
            user_data = {}

        # Сохранение данных
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

# Главное меню /start
@bot.message_handler(commands=["start", "main", "hello"])
def main(message):
    ask_language(message)

# Запрос языка общения
def ask_language(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_ru = types.KeyboardButton("Русский")
    btn_en = types.KeyboardButton("English")
    markup.add(btn_ru, btn_en)

    bot.send_message(message.chat.id, "На каком языке вам будет удобно общаться?", reply_markup=markup)

# Обработка выбора языка
@bot.message_handler(func=lambda message: message.text in ["Русский", "English"])
def handle_language(message):
    language = message.text
    bot.send_message(message.chat.id, "Пожалуйста, отправьте свой контактный номер.", 
                     reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                         types.KeyboardButton("Отправить контакт", request_contact=True)))
    bot.register_next_step_handler(message, handle_contact, language)

# Обработка отправки контакта
def handle_contact(message, language):
    if message.contact:
        contact = message.contact.phone_number
        bot.send_message(message.chat.id, "Пожалуйста, укажите ваше имя и фамилию.")
        bot.register_next_step_handler(message, handle_name, contact, language)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте свой контактный номер.", 
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                             types.KeyboardButton("Отправить контакт", request_contact=True)))
        bot.register_next_step_handler(message, handle_contact, language)

# Обработка имени и фамилии
def handle_name(message, contact, language):
    full_name = message.text
    first_name, last_name = full_name.split(maxsplit=1) if ' ' in full_name else (full_name, "")
    save_user_data(message.chat.id, language, first_name, last_name, contact)

    bot.send_message(message.chat.id, "Спасибо! Ваши данные сохранены.")
    send_main_menu(message)

# Функция для отправки главного меню
def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Создаем кнопки статично, как указано
    btn1 = types.KeyboardButton("🎸 Гитары")
    btn2 = types.KeyboardButton("🥁 Ударные")
    btn3 = types.KeyboardButton("🎹 Клавишные")
    btn4 = types.KeyboardButton("🎺 Духовые")
    btn5 = types.KeyboardButton("🛒 Корзина")
    btn6 = types.KeyboardButton("📦 Мои заказы")
    
    # Добавляем кнопки на клавиатуру
    markup.add(btn1, btn2, btn3, btn4)
    markup.add(btn5, btn6)
    
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в интернет-магазин музыкальных инструментов! Выберите категорию или действие:",
        reply_markup=markup
    )

# Функция для отправки информации о категории с товарами и пагинацией
def send_category_page(message, category, page):
    items_per_page = 2
    products_list = categories.get(category, [])
    total_pages = (len(products_list) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    page_items = products_list[start:end]

    text = f"{category} - страница {page}/{total_pages}\n\n"
    for item in page_items:
        text += f"🎶 {item['name']}\nЦена: {item['price']} руб\nОписание: {item['description']}\n\n"

    markup = types.InlineKeyboardMarkup(row_width=3)
    if page > 1:
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"{category}_{page - 1}"))
    markup.add(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))
    if page < total_pages:
        markup.add(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"{category}_{page + 1}"))
    home_button = types.InlineKeyboardButton("🏠 Домой", callback_data="home")
    markup.add(home_button)

    bot.send_message(message.chat.id, text, reply_markup=markup)

# Обработка кнопки добавления в корзину
@bot.callback_query_handler(func=lambda call: call.data.startswith("add_to_cart_"))
def add_to_cart(call):
    item_id = int(call.data.split("_")[2])
    user_id = call.from_user.id

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT cart_id FROM cart WHERE user_id = ? AND status = 0", (user_id,))
    cart = cursor.fetchone()

    if not cart:
        cursor.execute("INSERT INTO cart (user_id, status) VALUES (?, 0)", (user_id,))
        conn.commit()
        cart_id = cursor.lastrowid
    else:
        cart_id = cart[0]

    cursor.execute("""
        INSERT INTO cart_item (cart_id, item_id, price, active) 
        VALUES (?, ?, (SELECT price FROM item WHERE item_id = ?), 1)
    """, (cart_id, item_id, item_id))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "Товар добавлен в корзину!")

# Обработка выбора категории и отображение товаров с пагинацией
@bot.message_handler(func=lambda message: message.text.startswith("🎶"))
def category_handler(message):
    category = message.text[2:]
    send_category_page(message, category, page=1)

# Обработка нажатий на кнопки пагинации и кнопки "Домой"
@bot.callback_query_handler(func=lambda call: True)
def callback_page(call):
    if call.data == "home":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_main_menu(call.message)
    elif call.data == "current_page":
        bot.answer_callback_query(call.id, text="Это текущая страница")
    else:
        category, page = call.data.rsplit("_", 1)
        page = int(page)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_category_page(call.message, category, page)

# Запуск бота
bot.polling(none_stop=True)
