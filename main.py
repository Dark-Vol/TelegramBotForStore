import telebot
from telebot import types
import sqlite3  # Используется для работы с базой данных

bot = telebot.TeleBot("8126590226:AAEbDpzt7KZj8QHtj8tECgAonAQP3bKjVRA")

# Пример данных о товарах для каждой категории (замените на свои данные в реальной базе данных)
products = {
    "Гитары": [
        {"name": "Акустическая гитара Fender", "price": "12000 руб", "description": "Отличный звук и качество"},
        {"name": "Электрогитара Gibson", "price": "55000 руб", "description": "Для настоящих рокеров"},
        {"name": "Бас-гитара Yamaha", "price": "30000 руб", "description": "Глубокий басовый звук"},
        {"name": "Классическая гитара Cort", "price": "8000 руб", "description": "Подходит для начинающих"},
    ],
    "Ударные": [
        {"name": "Барабанная установка Tama", "price": "70000 руб", "description": "Полный комплект для профессионалов"},
        {"name": "Тарелки Zildjian", "price": "12000 руб", "description": "Отличное дополнение к установке"},
        {"name": "Электронные барабаны Roland", "price": "45000 руб", "description": "Компактные и универсальные"},
    ],
    "Клавишные": [
        {"name": "Синтезатор Yamaha", "price": "20000 руб", "description": "Для создания музыки"},
        {"name": "Миди-клавиатура Novation", "price": "15000 руб", "description": "Идеально для студии"},
        {"name": "Электропианино Casio", "price": "25000 руб", "description": "Звучание настоящего пианино"},
    ],
    "Духовые": [
        {"name": "Флейта Yamaha", "price": "10000 руб", "description": "Прекрасный выбор для начинающих"},
        {"name": "Саксофон Selmer", "price": "85000 руб", "description": "Профессиональный инструмент с богатым звуком"},
        {"name": "Кларнет Buffet", "price": "40000 руб", "description": "Высококачественный кларнет для оркестра"},
    ],
}

# Подключение к базе данных
def connect_db():
    return sqlite3.connect("your_database.db")

# Главное меню /start
@bot.message_handler(commands=["start", "main", "hello"])
def main(message):
    send_main_menu(message)

# Функция для отправки главного меню
def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🎸 Гитары")
    btn2 = types.KeyboardButton("🥁 Ударные")
    btn3 = types.KeyboardButton("🎹 Клавишные")
    btn4 = types.KeyboardButton("🎺 Духовые")
    btn5 = types.KeyboardButton("🛒 Корзина")
    btn6 = types.KeyboardButton("📦 Мои заказы")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в интернет-магазин музыкальных инструментов! Выберите категорию или действие:",
        reply_markup=markup
    )

# Функция для отправки информации о категории с товарами и пагинацией
def send_category_page(message, category, page):
    items_per_page = 2
    products_list = products.get(category, [])
    total_pages = (len(products_list) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    page_items = products_list[start:end]

    text = f"{category} - страница {page}/{total_pages}\n\n"
    for item in page_items:
        text += f"🎶 {item['name']}\nЦена: {item['price']}\nОписание: {item['description']}\n\n"

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
@bot.message_handler(func=lambda message: message.text in ["🎸 Гитары", "🥁 Ударные", "🎹 Клавишные", "🎺 Духовые"])
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
        # Нажата кнопка с текущей страницей — просто игнорируем ее
        bot.answer_callback_query(call.id, text="Это текущая страница")
    else:
        category, page = call.data.rsplit("_", 1)
        page = int(page)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_category_page(call.message, category, page)


# Запуск бота
bot.polling(none_stop=True)