import requests
import telebot
import time
from telebot import types

# Инициализируем бота токеном
bot = telebot.TeleBot("8930643502:AAH5pqodQTmRCx95n7IeLCIFb_lqj7DDqq4", threaded=True)
amount = 0

# Функция создания кнопок (вынесли в отдельный блок, чтобы не дублировать код)
def get_currency_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("USD -> EUR", callback_data="USD_EUR")
    btn2 = types.InlineKeyboardButton("EUR -> USD", callback_data="EUR_USD")
    btn3 = types.InlineKeyboardButton("USD -> AMD", callback_data="USD_AMD")
    btn4 = types.InlineKeyboardButton("AMD -> USD", callback_data="AMD_USD")
    markup.add(btn1, btn2, btn3, btn4)
    
    btn_custom = types.InlineKeyboardButton("Свой вариант ✏️", callback_data="CUSTOM_PAIR")
    markup.row(btn_custom)
    return markup


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id, "Добро пожаловать в универсальный конвертер валют! 🪙"
    )
    time.sleep(0.5)
    bot.send_message(message.chat.id, "Введите сумму для конвертации:")
    bot.register_next_step_handler(message, summa)


def summa(message):
    global amount

    if message.text.strip() == '/start':
        bot.clear_step_handler_by_chat_id(message.chat.id)
        start(message)
        return

    try:
        amount = float(message.text.strip())
    except ValueError:
        bot.send_message(
            message.chat.id, "❌ Ошибка! Введите сумму цифрами. Попробуйте еще раз."
        )
        bot.register_next_step_handler(message, summa)
        return

    if amount <= 0:
        bot.send_message(
            message.chat.id, "❌ Ошибка! Введите положительную сумму. Попробуйте еще раз."
        )
        bot.register_next_step_handler(message, summa)
        return

    bot.clear_step_handler_by_chat_id(message.chat.id)
    
    # ИСПРАВЛЕНО: Вместо длинного текста отправляем короткое уведомление с кнопками
    bot.send_message(
        message.chat.id,
        "Сумма принята 👇",
        reply_markup=get_currency_markup()
    )


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global amount
    bot.answer_callback_query(call.id)
    bot.clear_step_handler_by_chat_id(call.message.chat.id)

    # Убираем старые кнопки, чтобы избежать двойных нажатий
    try:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    except Exception:
        pass

    # 1. ОБРАБОТКА НАЖАТИЯ НА «Свой вариант»
    if call.data == "CUSTOM_PAIR":
        sent_msg = bot.send_message(
            call.message.chat.id,
            f"💵 Сумма ({amount}) сохранена!\n"
            "Теперь напишите коды двух валют через пробел.\n"
            "Например: `USD RUB` или `GEL AMD`",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(sent_msg, process_custom_currencies)
        return

    # 2. ОБРАБОТКА СТАНДАРТНЫХ КНОПОК ВАЛЮТ
    values = call.data.upper().split('_')
    from_currency = values[0]
    to_currency = values[1]

    try:
        response = requests.get(f"https://open.er-api.com/v6/latest/{from_currency}")
        data = response.json()

        if data.get("result") == "error":
            err_msg = bot.send_message(call.message.chat.id, f"❌ Ошибка! Валюта `{from_currency}` не найдена.")
            bot.register_next_step_handler(err_msg, summa)
            return

        if to_currency not in data.get("rates", {}):
            err_msg = bot.send_message(call.message.chat.id, f"❌ Ошибка! Валюта `{to_currency}` не найдена в базе.")
            bot.register_next_step_handler(err_msg, summa)
            return

        rate = data["rates"][to_currency]
        res = round(amount * rate, 2)

        # ИСПРАВЛЕНО: К результату сразу прикрепляем новые кнопки для следующего круга!
        sent_msg = bot.send_message(
            call.message.chat.id,
            f'💰 **Результат:**\n{amount} {from_currency} = {res} {to_currency}.\n\n'
            f'Вы можете сразу вписать новую сумму 👇:',
            reply_markup=get_currency_markup()
        )
        bot.register_next_step_handler(sent_msg, summa)

    except Exception as e:
        print(f"Ошибка API (Кнопки): {e}")
        err_msg = bot.send_message(call.message.chat.id, "⚠️ Ошибка при получении курса валют.")
        bot.register_next_step_handler(err_msg, summa)


# 3. ФУНКЦИЯ ДЛЯ ОБРАБОТКИ РУЧНОГО ВВОДА КУРСОВ
def process_custom_currencies(message):
    if message.text.strip() == '/start':
        bot.clear_step_handler_by_chat_id(message.chat.id)
        start(message)
        return

    try:
        raw_text = message.text.strip().upper()
        values = raw_text.split()

        if len(values) != 2:
            bot.send_message(
                message.chat.id,
                "❌ Неверный формат! Введите ровно две валюты через пробел (например: `GEL AMD`)."
            )
            bot.register_next_step_handler(message, process_custom_currencies)
            return

        from_currency = values[0]
        to_currency = values[1]

        response = requests.get(f"https://open.er-api.com/v6/latest/{from_currency}")
        data = response.json()

        if data.get("result") == "error" or from_currency not in data.get("rates", {}):
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка! Валюта `{from_currency}` не найдена. Проверьте правильность кодов."
            )
            bot.register_next_step_handler(message, process_custom_currencies)
            return

        if to_currency not in data["rates"]:
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка! Валюта `{to_currency}` не найдена в базе."
            )
            bot.register_next_step_handler(message, process_custom_currencies)
            return

        rate = data["rates"][to_currency]
        res = round(amount * rate, 2)

        # ИСПРАВЛЕНО: К ручному вводу тоже прикрепляем новые кнопки!
        sent_msg = bot.send_message(
            message.chat.id,
            f'💰 **Результат:**\n{amount} {from_currency} = {res} {to_currency}\n\n'
            f'Вы можете сразу ввести новую сумму для следующей конвертации 👇:',
            reply_markup=get_currency_markup()
        )
        bot.register_next_step_handler(sent_msg, summa)

    except Exception as e:
        print(f"Ошибка API (Ручной ввод): {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте еще раз.")
        bot.register_next_step_handler(message, summa)


if __name__ == "__main__":
    bot.polling(none_stop=True)
