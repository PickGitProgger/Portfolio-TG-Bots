import telebot
from telebot import types
import time
import requests
import threading

TOKEN = ("token")
bot = telebot.TeleBot(TOKEN)

def fetch_crypto_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data[coin_id]['usd']
    except Exception as e:
        print(f"Ошибка API Крипты: {e}")
        return None

def fetch_usd_exchange():
    try:
        url = "https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5"
        res = requests.get(url, timeout=10).json()
        usd = next(item for item in res if item['ccy'] == 'USD')
        return usd['buy'], usd['sale']
    except Exception as e:
        print(f"Ошибка API Банка: {e}")
        return None, None

def MainMenu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("Напоминание"), types.KeyboardButton("Узнать Цену 'BTC'"))
    markup.row(types.KeyboardButton("Узнать Цену TON"), types.KeyboardButton("Узнать Цену USD в Вашем Регионе"))
    return markup

def get_cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Отмена"))
    return markup

def send_reminder(chat_id, minutes, text):
    time.sleep(minutes * 60)
    bot.send_message(chat_id, f"⏰ **НАПОМИНАНИЕ:**\n\n{text}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Напоминание")
def ask_time(message):
    msg = bot.send_message(message.chat.id, "Через сколько минут напомнить?", reply_markup=get_cancel_menu())
    bot.register_next_step_handler(msg, process_time_step)

def process_time_step(message):
    if message.text == "❌ Отмена": 
        bot.send_message(message.chat.id, "Отменено", reply_markup=MainMenu())
        return 
    try:
        minutes = float(message.text)
        msg = bot.send_message(message.chat.id, "О чем напомнить?", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_text_step, minutes)
    except:
        msg = bot.send_message(message.chat.id, "Введите число!")
        bot.register_next_step_handler(msg, process_time_step)

def process_text_step(message, minutes):
    if message.text == "❌ Отмена": 
        bot.send_message(message.chat.id, "Отменено", reply_markup=MainMenu())
        return
    bot.send_message(message.chat.id, f"Ок! Напомню через {minutes} мин.", reply_markup=MainMenu())
    threading.Thread(target=send_reminder, args=(message.chat.id, minutes, message.text), daemon=True).start()

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Здравствуйте, чем могу помочь?", reply_markup=MainMenu())

@bot.message_handler(func=lambda m: m.text == "Узнать Цену 'BTC'")
def btc_handler(message):
    price = fetch_crypto_price('bitcoin')
    if price:
        bot.send_message(message.chat.id, f"💰 Bitcoin: **${price:,}**", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "Ошибка биржи.")

@bot.message_handler(func=lambda m: m.text == "Узнать Цену TON")
def ton_handler(message):
    price = fetch_crypto_price('the-open-network')
    if price:
        bot.send_message(message.chat.id, f"💎 TON: **${price}**", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "Ошибка биржи.")

@bot.message_handler(func=lambda m: m.text == "Узнать Цену USD в Вашем Регионе")
def usd_handler(message):
    buy, sale = fetch_usd_exchange()
    if buy:
        text = f"💵 **Курс USD (UA):**\nПокупка: {buy} грн\nПродажа: {sale} грн"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "Не удалось получить курс валют.")

@bot.message_handler(func=lambda m: m.text == "❌ Отмена")
def global_cancel(message):
    bot.send_message(message.chat.id, "Возврат в меню", reply_markup=MainMenu())

if __name__ == '__main__':
    print("Бот успешно запущен для портфолио!")
    bot.infinity_polling()
