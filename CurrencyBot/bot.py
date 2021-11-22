import requests as re
import telebot
from telebot import types
import time
from datetime import datetime, timedelta
import pymysql
from pymysql.cursors import DictCursor

#Токен бота (подробнее в тг @BotFather)
_TOKEN = '' #Вставить свой токен токен, полученный в @BotFather!!!

#Ссылка для получения курса валют в ЦБ
_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'

bot = telebot.TeleBot(_TOKEN)

#Функция для подключения к БД
def connect_db():
    try:
        sql = pymysql.connect(
            host="mysql",
            user="root",
            password="pass",
            db="main",
            port=3306,
            charset='utf8mb4',
            autocommit=True, #(!!!)
            cursorclass=DictCursor
        )
        return sql
    except Exception as e:
        print('Ошибка подключения к базе')
        print(e, flush=True)


#Запись в БД
def write_db(query):
    sql = connect_db()
    cursor = sql.cursor()
    cursor.execute(query)
    sql.close()

#Чтение из БД
def read_db(query):
    sql = connect_db()
    cursor = sql.cursor()
    cursor.execute(query)
    res = cursor.fetchall()
    sql.close()
    return res


#Функция для отправки http-запроса и его парсинга
def get_usd():
    resp = re.get(_URL)
    res = resp.json()['Valute']['USD']['Value']

    return res #Возвращает курс


#Инициализация БД
write_db(
    """
    CREATE TABLE IF NOT EXISTS `requests` (
    `id` integer PRIMARY KEY AUTO_INCREMENT,
    `date` datetime,
    `result` float
    );
    """
)

#Обработка запуска бота (первое использование либо /start)
@bot.message_handler(commands=['start'])
def text_handler_cmd(message):
    global apps
    chat = message.chat.id

    #Поздороваться и показать кнопки для управления ботом
    markup = types.ReplyKeyboardMarkup(selective=False, resize_keyboard=True)
    markup.row(types.KeyboardButton('Получить курс доллара'))
    markup.row(types.KeyboardButton('Показать историю запросов'))
    bot.send_message(chat, 'Привет', reply_markup=markup)


#Обработка нажатия на кнопку
@bot.message_handler(content_types=['text'])
def text_handler_text(message):
    msg = message.text
    chat = message.chat.id

    # Оставить кнопки при ответе
    markup = types.ReplyKeyboardMarkup(selective=False, resize_keyboard=True)
    markup.row(types.KeyboardButton('Получить курс доллара'))
    markup.row(types.KeyboardButton('Показать историю запросов'))

    # Проверка кнопки
    if msg == 'Получить курс доллара':

        #Получить курс и отправить его пользователю
        res = get_usd()

        #Текцщая дата в формате mysql
        dt = (datetime.now() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

        text = f"""
        Текущий курс доллара по ЦентроБанку: {res}
        """

        #Сохранить запрос в базу
        write_db(
            f"""
            INSERT INTO `requests` (
                date, 
                result
            ) VALUES (
                '{dt}', 
                {res}
            );
            """
        )

    elif msg == 'Показать историю запросов':

        res = read_db("SELECT `date`, `result` from `requests` ORDER BY id DESC LIMIT 20;")
        text = 'Последние 20 запросов:\n'
        for r in res:
            text += r['date'].strftime('%Y-%m-%d %H:%M:%S') + f"  --  курс: {r['result']}\n"

    else:

        text = 'Я вас не понимаю.'

    #Отправить результат
    bot.send_message(chat, text, reply_markup=markup)


#Не выключать бота
bot.polling(none_stop=True)
