
import os
import handlers
from aiogram import executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from data import config
from loader import dp, db, bot
import filters
import logging

filters.setup(dp)

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 5000))
user_message = 'Пользователь'
admin_message = 'Админ'
catalog = '🛍️ Каталог'
balance = '💰 Баланс'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'
rewiews = '😎 Отзывы'


settings = '⚙️ Настройка каталога'
orders = '🚚 Заказы'
questions = '❓ Вопросы'
closed_orders_button = 'Завершенные заказы'
count_of_users = 'Количество пользователей'



@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    if not db.user_exists(message.from_user.id):
        db.query(f'INSERT OR IGNORE INTO all_users(cid) VALUES({message.from_user.id})')

    #markup.row(user_message, admin_message)
    #markup.row('/Меню')
    markup.add(catalog)
    # markup.add(balance, cart)
    markup.add(cart)
    markup.add(delivery_status)
    #markup.add(rewiews)

    await message.answer('''Рады тебя видеть 😎

🛍️ В Каталоге ты можешь найти все доступные товары. Не стесняйся добавлять в корзину😎
    
🛒 В Корзине ты можешь оформить заказ.

🚚 Ну а в графе Статус заказа ты можешь проверить свой заказ и связаться с менеджером😎

📦 Для оптовых заказов, просто выбери нужный товар и его количество в корзине, и оформи заказ. Менеджер быстро пересчитает стоимость и отпишется. 

❓ Если есть какие-то вопросы, смело пиши менеджеру😏 \n@vape_brest_manager.
    ''', reply_markup=markup)


@dp.message_handler(text=user_message)
async def user_mode(message: types.Message):

    cid = message.chat.id
    if cid in config.ADMINS:
        config.ADMINS.remove(cid)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    # markup.row(user_message, admin_message)
    # markup.row('/Меню')
    markup.add(catalog)
    # markup.add(balance, cart)
    markup.add(cart)
    markup.add(delivery_status)
    #markup.add(rewiews)

    await message.answer('Включен пользовательский режим.', reply_markup=markup)
    await message.delete()



@dp.message_handler(text=admin_message)
async def admin_mode(message: types.Message):

    cid = message.chat.id
    if cid not in config.ADMINS:
        config.ADMINS.append(cid)

    add_rew = 'Добавить отзыв'
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    open_orders_button = 'Активные заказы'
    markup.add(questions, open_orders_button)
    markup.add(closed_orders_button, 'Сделать рассылку')
    #markup.add(open_orders_button)
    markup.add(count_of_users)
    markup.add(add_rew)

    await message.answer('Включен админский режим.', reply_markup=markup)
    await message.delete()


async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)
    db.create_tables()

    await bot.delete_webhook()
    await bot.set_webhook(config.WEBHOOK_URL)


async def on_shutdown():
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")


if __name__ == '__main__':

    if "HEROKU" in list(os.environ.keys()):

        executor.start_webhook(
            dispatcher=dp,
            webhook_path=config.WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )

    else:

        executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
