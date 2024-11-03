import telebot
from telebot import types

bot = telebot.TeleBot("8126590226:AAEbDpzt7KZj8QHtj8tECgAonAQP3bKjVRA")

# Пример данных о товарах для каждой категории (замените на свои данные)
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
}

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
    btn4 = types.KeyboardButton("🆘 Помощь")
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, "Добро пожаловать в интернет-магазин музыкальных инструментов! Выберите категорию:", reply_markup=markup)

# Справка
@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id, 
        "<b>Help</b>: Выберите интересующую вас категорию или используйте команды для получения помощи.", 
        parse_mode="html"
    )

# Обработка выбора категории и отображение товаров с пагинацией
@bot.message_handler(func=lambda message: message.text in ["🎸 Гитары", "🥁 Ударные", "🎹 Клавишные"])
def category_handler(message):
    category = message.text[2:]  # Убираем иконку из текста для получения категории
    send_category_page(message, category, page=1)

# Функция для отправки информации о категории с товарами и пагинацией
def send_category_page(message, category, page):
    items_per_page = 2
    products_list = products.get(category, [])
    total_pages = (len(products_list) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    page_items = products_list[start:end]

    # Формируем текст с товарами на текущей странице
    text = f"{category} - страница {page}/{total_pages}\n\n"
    for item in page_items:
        text += f"🎶 {item['name']}\nЦена: {item['price']}\nОписание: {item['description']}\n\n"

    # Инлайн-кнопки для пагинации
    markup = types.InlineKeyboardMarkup(row_width=3)
    if page > 1:
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"{category}_{page - 1}"))
    markup.add(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))
    if page < total_pages:
        markup.add(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"{category}_{page + 1}"))
    home_button = types.InlineKeyboardButton("🏠 Домой", callback_data="home")
    markup.add(home_button)

    bot.send_message(message.chat.id, text, reply_markup=markup)

# Обработка нажатий на кнопки пагинации и кнопки "Домой"
@bot.callback_query_handler(func=lambda call: True)
def callback_page(call):
    if call.data == "home":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_main_menu(call.message)
    else:
        category, page = call.data.rsplit("_", 1)
        page = int(page)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_category_page(call.message, category, page)

# Запуск бота
bot.polling(none_stop=True)
