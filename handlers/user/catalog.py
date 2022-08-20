
import logging
from aiogram.types import Message, CallbackQuery
from keyboards.inline.categories import categories_markup, category_cb
from keyboards.inline.products_from_catalog import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from aiogram.types.chat import ChatActions
from loader import dp, db, bot
from .menu import catalog
from filters import IsUser


@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    await message.answer('Вот что у нас для тебя есть🙃',
                         reply_markup=categories_markup())


@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):

    products = db.  fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))

    await query.answer('Вот что у нас для тебя есть😎')
    await show_products(query.message, products)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery, callback_data: dict):

    #callback_data['title'] =
    #print(db.fetchall('SELECT title FROM products WHERE idx=?', callback_data['id']))
    products = db.fetchall('''SELECT * FROM products product''')
    for idx, title, body, image, price, _ in products:
        print('idx = ' + str(idx))
        if idx == callback_data['id']:
            print(title)
            callback_data['title'] = title
    print(callback_data['id'])
    print(callback_data)
    db.query('INSERT INTO cart VALUES (?, ?, 1, ?)',
             (query.message.chat.id, callback_data['id'], callback_data['title']))

    await query.answer('Товар добавлен в корзину!')
    await query.message.delete()


async def show_products(m, products):

    if len(products) == 0:

        await m.answer('Здесь ничего нет 😢')

    else:

        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        for idx, title, body, image, price, _ in products:

            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{body}'

            await m.answer_photo(photo=image,
                                 caption=text,
                                 reply_markup=markup)
        await m.answer('Если не знаешь что выбрать, напиши @vape_brest_manager о своих вкусах, он подберет то, что тебе понравится😎')