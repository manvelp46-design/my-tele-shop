import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

# 1. Инициализируем бота
bot = Bot(token='8845923537:AAFl70cyFRqe6UEIhukVsihA3JP-uQOQkco')

# 2. Создаем пустой Диспетчер под aiogram 3.x
dp = Dispatcher()


# 3. Ловим команду /start и выдаем кнопку с ТВОИМ сайтом
@dp.message(Command('start'))
async def start(message: types.Message):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            # Здесь указана именно твоя ссылка, куда ты перетащил свой index.html!
            [KeyboardButton(text='Открыть мой сайт', web_app=WebAppInfo(url='https://telegramhtml.netlify.app/'))]
        ],
        resize_keyboard=True  # чтобы кнопка была аккуратной
    )
    await message.answer("Привет! Нажми на кнопку ниже, чтобы открыть твой собственный HTML-сайт.", reply_markup=markup)


async def main():
    # Запускаем постоянный опрос сервера
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
