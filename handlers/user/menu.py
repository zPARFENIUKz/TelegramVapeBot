
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from loader import dp
from filters import IsAdmin, IsUser

catalog = '🛍️ Каталог'
balance = '💰 Баланс'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'
rewiews = '😎 Отзывы'

settings = '⚙️ Настройка каталога'
orders = '🚚 Заказы'
questions = '❓ Вопросы'
open_orders_button = 'Активные заказы'
closed_orders_button = 'Завершенные заказы'


@dp.message_handler(IsAdmin(), commands='Меню')
async def admin_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, open_orders_button)
    markup.add(closed_orders_button, 'Сделать рассылку')
    count_of_users = 'Количество пользователей'
    #markup.add(open_orders_button)
    markup.add(count_of_users)
    markup.add('Добавить отзыв')

    await message.answer('Меню', reply_markup=markup)

@dp.message_handler(IsUser(), text='Вернуться в меню')
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    #markup.add(balance, cart)
    markup.add(cart)
    markup.add(delivery_status)
    #markup.add(rewiews)

    await message.answer('Меню', reply_markup=markup)

@dp.message_handler(IsUser(), commands='Меню')
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    #markup.add(balance, cart)
    markup.add(cart)
    markup.add(delivery_status)
    #markup.add(rewiews)

    await message.answer('Меню', reply_markup=markup)
