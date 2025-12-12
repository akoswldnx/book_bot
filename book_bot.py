from email import message
import telebot
import requests
import random 
from telebot import types


API_TOKEN = "8534737189:AAFMk84-sOITE3ieW8RGuTyE7I5dHgzwkek"

bot = telebot.TeleBot(API_TOKEN)

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes?q="

user_favorites = {}
search_mode = {}


def search_books(query):
    url = GOOGLE_BOOKS_URL + query
    response = requests.get(url)
    data = response.json()

    books = []

    if "items" not in data:
        return books
    for item in data["items"][:5]:
        volume_info = item["volumeInfo"]
        title = volume_info.get("title", "нет название 🫣" )
        authors = ", ".join(volume_info.get("authors", ["aвтор неизвестен 🤔"]))
        description = volume_info.get("description", "нет описаний 🤷🏻‍♀️")
        link = volume_info.get("infoLink", "")

        books.append(f"<b>{title}</b>\n"
                     f" {authors}\n"
                     f" {description[:300]}...\n"
                     f" {link}\n")
        
    return books

@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🔍 Поиск книги")
    btn2 = types.KeyboardButton("⭐️ Избранные")
    btn3 = types.KeyboardButton("📩 Комплимент")
    btn4 = types.KeyboardButton("📚 Рекомендация дня")
    btn5 = types.KeyboardButton("📚 Рекомендуй")

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)

    bot.send_message(
        message.chat.id,
        "Привет!😙 Мой книгоман! \n"
        "Я помогу тебе найти любую книгу - по автору, описанию, названию. \n "
        "А так же дам рекомендацию дня или предложу книгу под твоё настроение))",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text == "🔍 Поиск книги")
def ask_search_type(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("По названию", callback_data="search_title"))
    markup.add(types.InlineKeyboardButton("По автору", callback_data="search_author"))
    markup.add(types.InlineKeyboardButton("По описанию", callback_data="search_desc"))

    bot.send_message(message.chat.id, "Введите название книги:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call:True)
def callback(call):
    chat_id = call.message.chat.id

    if call.data =="search_title":
        search_mode[chat_id] = "title"
        bot.send_message(chat_id, "Введите название книги:")
    elif call.data == "search_author":
        search_mode[chat_id] = "author"
        bot.send_message(chat_id, "Введите имя автора:")
    elif call.data == "search_desc":
        search_mode[chat_id] = "description"
        bot.send_message(chat_id, "Введите ключевые слова описания:")
    elif call.data.startswith("fav_"):
        fav_book = call.data[4:]
        user_favorites.setdefault(chat_id, [])
        user_favorites[chat_id].append(fav_book)
        bot.send_message(chat_id, "Добавлено в избранное!⭐️")
    elif call.data == "rec_mood":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("😢 Грустно", callback_data="m_sad"))
        markup.add(types.InlineKeyboardButton("😊 Весело", callback_data="m_happy"))
        markup.add(types.InlineKeyboardButton("💗 Романтика", callback_data="m_love"))
        markup.add(types.InlineKeyboardButton("😡 Злюсь", callback_data="m_angry"))
        markup.add(types.InlineKeyboardButton("😌 Спокойно", callback_data="m_calm"))
        bot.send_message(call.message.chat.id, "Какое сейчас настроение?", reply_markup=markup)

    elif call.data == "rec_genre":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🧙 Фэнтези", callback_data="g_fantasy"))
        markup.add(types.InlineKeyboardButton("💞 Роман", callback_data="g_romance"))
        markup.add(types.InlineKeyboardButton("🕵️ Детектив", callback_data="g_detective"))
        markup.add(types.InlineKeyboardButton("🧠 Психология", callback_data="g_psychology"))
        markup.add(types.InlineKeyboardButton("📜 Классика", callback_data="g_classic"))
        bot.send_message(call.message.chat.id, "Выбери жанр:", reply_markup=markup)

   
    elif call.data.startswith("m_"):
        mood = call.data[2:]
        bot.send_message(call.message.chat.id, mood_recs[mood], parse_mode="Markdown")

   
    elif call.data.startswith("g_"):
        genre = call.data[2:]
        bot.send_message(call.message.chat.id, genre_recs[genre], parse_mode="Markdown")

        
@bot.message_handler(func=lambda msg: msg.chat.id in search_mode)
def real_search(message):
    mode = search_mode[message.chat.id]
    query = message.text

    bot.send_message(message.chat.id, "ищу книги...😴")

    if mode == "title":
        books = search_books("intitle:" + query)
    elif mode == "author":
        books = search_books("inauthor:" + query)
    else :
        books = search_books(query)

    if not books:
        bot.send_message(message.chat.id, "ничего не нашел(( попробуй другое слово🙃")
        del search_mode[message.chat.id]
        return
    
    for book in books:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Добавить в избранное" , callback_data="fav_" + book[:30]))
        bot.send_message(message.chat.id, book, parse_mode="HTML", reply_markup=markup)

    del search_mode[message.chat.id]



@bot.message_handler(func=lambda msg: msg.text == "⭐️ Избранные")
def show_favorites(message):
    user_id = message.chat.id

    if user_id not in user_favorites or len(user_favorites[user_id]) == 0:
        bot.send_message(user_id, "У тебя пока нет избранных 🤷🏻‍♀️")
        return 
    
    bot.send_message(user_id, "Твои избранные книги :")

    for book in user_favorites[user_id]:
        bot.send_message(user_id, book)


@bot.message_handler(func=lambda msg: msg.text in ["спасибоо", "рахмет", "от души", "спасибо"])
def reply_thanks(message):
    bot.send_message(
        message.chat.id, "Пожалуйста, всегда обращайся  😘"
    )

compliments = [
    "Ты сегодня молодец!🤩",
    "У тебя все получится)😄",
    "Хорошего дня!☺️",
    "Ты просто супер💗"
]
@bot.message_handler(func=lambda msg: msg.text == "📩 Комплимент" )
def compliment(message):
    bot.send_message(message.chat.id, random.choice(compliments))

daily_recommendations = [
    "📘 *1984* — Джордж Оруэлл. Классика антиутопий.",
    "📙 *Тихий Дон* — Михаил Шолохов. Мощный роман о любви и войне.",
    "📗 *Гарри Поттер* — Дж. Роулинг. Теплая сказка, которая лечит душу.",
    "📕 *Мастер и Маргарита* — Михаил Булгаков. Мистика, философия и любовь.",
    "📔 *Атлант расправил плечи* — Айн Рэнд. Книга, которая переворачивает мышление."
]

@bot.message_handler(func=lambda msg: msg.text == "📚 Рекомендация дня")
def rec_of_day(message):
    bot.send_message(
        message.chat.id,
        random.choice(daily_recommendations),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: msg.text == "📚 Рекомендуй")
def choose_recommend_type(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💗 По настроению", callback_data="rec_mood"))
    markup.add(types.InlineKeyboardButton("📚 По жанрам", callback_data="rec_genre"))
    bot.send_message(message.chat.id, "Выбери тип рекомендации:", reply_markup=markup)

mood_recs = {
    "sad": "🩵 Когда грустно: *Цветы для Элджернона* — Дэниел Киз.",
    "happy": "💛 Когда хорошее настроение: *Дневник Бриджит Джонс*.",
    "love": "💗 Хочется романтики: *Виноваты звезды*.",
    "angry": "❤️‍🔥 Когда злишься: *Анна Каренина* — драму драмой перебивает.",
    "calm": "🤍 Для спокойствия: *451 градус по Фаренгейту*."
}

genre_recs = {
    "fantasy": "🧙 *Ведьмак* — Сапковский.",
    "romance": "💞 *После* — Анна Тодд.",
    "detective": "🕵️ *Шерлок Холмс* — Артур Конан Дойл.",
    "psychology": "🧠 *Думай медленно, решай быстро*.",
    "classic": "📜 *Преступление и наказание*."
}

bot.polling(none_stop=True)