
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from states import ProductState, CategoryState
from states.product_state import AddRewiewState
from states.product_state import MailingState
from aiogram.types.chat import ChatActions
from handlers.user.menu import settings
from loader import dp, db, bot
from filters import IsAdmin
from hashlib import md5
from aiogram.dispatcher.filters import Text
from aiogram import types


category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')
red_product_cb = CallbackData('product', 'id', 'price', 'action')

add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'

@dp.message_handler(IsAdmin(), text='Количество пользователей')
async def process_count_of_users(message : Message):
    all_users = db.fetchall('SELECT * FROM all_users')
    await message.answer(f'Ботом пользуется столько людей: {len(all_users)}')


@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):

    markup = InlineKeyboardMarkup()

    for idx, title in db.fetchall('SELECT * FROM categories'):

        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton(
        '+ Добавить категорию', callback_data='add_category'))

    await message.answer('Настройка категорий:', reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):

    category_idx = callback_data['id']

    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))

    await query.message.delete()
    await query.answer('Все добавленные товары в эту категорию.')
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products, category_idx)


# category


@dp.callback_query_handler(IsAdmin(), text='add_category')
async def add_category_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Название категории?')
    await CategoryState.title.set()


@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):

    category = message.text
    idx = md5(category.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))

    await state.finish()
    await process_settings(message)


@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):

    async with state.proxy() as data:

        if 'category_index' in data.keys():

            idx = data['category_index']

            db.query(
                'DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)', (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))
            markup = ReplyKeyboardMarkup()
            markup.add(add_product)
            markup.add(delete_category)
            markup.add('/Меню')
            await message.answer('Готово!', reply_markup=markup)
            await process_settings(message)
add_rew = 'Добавить отзыв'

@dp.message_handler(IsAdmin(), text='Сделать рассылку')
async def process_start_mailing(message : Message):
    await MailingState.message_text.set()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)
    await message.answer('Введите сообщение для рассылки', reply_markup=markup)
settings = '⚙️ Настройка каталога'
orders = '🚚 Заказы'
questions = '❓ Вопросы'
open_orders_button = 'Активные заказы'
closed_orders_button = 'Завершенные заказы'
count_of_users = 'Количество пользователей'

@dp.message_handler(IsAdmin(), text=add_rew)
async def add_rewiew(message: Message):
    await AddRewiewState.photo_rewiew.set()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)
    await message.answer('Отправь фото отзыва', reply_markup=markup)

@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO, state=AddRewiewState.photo_rewiew)
async def final_add_rewiew(message: Message, state: FSMContext):
    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()
    db.query('INSERT INTO rewiews VALUES (?)',
             (downloaded_file,))
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, open_orders_button)
    markup.add(closed_orders_button, 'Сделать рассылку')
    # markup.add(open_orders_button)
    markup.add(count_of_users)
    markup.add(add_rew)
    await message.answer('Отзыв был добавлен', reply_markup=markup)
    await state.finish()

@dp.message_handler(IsAdmin(), text=cancel_message, state=AddRewiewState.photo_rewiew)
async def cancel_add_rewiew(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, open_orders_button)
    markup.add(closed_orders_button, 'Сделать рассылку')
    # markup.add(open_orders_button)
    markup.add(count_of_users)
    markup.add(add_rew)
    await message.answer('Ок, отменено!', reply_markup=markup)
    await state.finish()

@dp.message_handler(IsAdmin(), text=cancel_message, state=MailingState.message_text)
async def mailing_cancel(message : Message, state : FSMContext):
    #Тута
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, open_orders_button)
    markup.add(closed_orders_button, 'Сделать рассылку')
    # markup.add(open_orders_button)
    markup.add(count_of_users)
    markup.add(add_rew)
    await message.answer('Ок, отменено!', reply_markup=markup)
    await state.finish()
# add product
@dp.message_handler(IsAdmin(), state=MailingState.message_text)
async def process_message_text(message : Message, state : FSMContext):
    async with state.proxy() as data:
        data['message_text'] = message.text
    await MailingState.next()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)
    await message.answer('Теперь отправь фотку для рассылки', reply_markup=markup)

@dp.message_handler(IsAdmin(), text=cancel_message, state=MailingState.image)
async def process_mestxt_cancel(message : Message, state : FSMContext):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, open_orders_button)
    markup.add(closed_orders_button, 'Сделать рассылку')
    # markup.add(open_orders_button)
    markup.add(count_of_users)
    await message.answer('Ок, отменено!', reply_markup=markup)
    await state.finish()

@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO,state=MailingState.image)
async def mailing_get_image(message : Message, state : FSMContext):
    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()
    markup = ReplyKeyboardMarkup()
    markup.add('Отправить всем')
    markup.add('Вернуться в меню')

    async with state.proxy() as data:
        data['image'] = downloaded_file
        await MailingState.next()
        await message.answer_photo(photo=data['image'],
                             caption=data['message_text'],
                                   reply_markup=markup)

@dp.message_handler(IsAdmin(), text='Вернуться в меню',state=MailingState.confirm)
async def mailing_final_cancel(message: Message, state : FSMContext):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, open_orders_button)
    markup.add(closed_orders_button, 'Сделать рассылку')
    # markup.add(open_orders_button)
    markup.add(count_of_users)
    await message.answer('Ок, отменено!', reply_markup=markup)
    await state.finish()

@dp.message_handler(IsAdmin(), text='Отправить всем',state=MailingState.confirm)
async def mailing_final_sendall(message: Message, state : FSMContext):
    users = db.fetchall('SELECT cid FROM all_users')
    counter = 0
    for user in users:
        try:
            async with state.proxy() as data:
                await bot.send_photo(chat_id=user[0],
                                     photo=data['image'],
                                     caption=data['message_text'])
                counter += 1
        except:
            pass
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, open_orders_button)
    markup.add(closed_orders_button, 'Сделать рассылку')
    # markup.add(open_orders_button)
    markup.add(count_of_users)
    await message.answer(f'Была совершена рассылка всем пользователям, успешно было отправлено {counter} сообщений', reply_markup=markup)
    await state.finish()



@dp.message_handler(IsAdmin(), text=add_product)
async def process_add_product(message: Message):
    await ProductState.title.set()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)
    await message.answer('Название?', reply_markup=markup)
@dp.message_handler(IsAdmin(), text=cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):

    await message.answer('Ок, отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()

    await process_settings(message)
@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await process_add_product(message)
@dp.message_handler(IsAdmin(), state=ProductState.title)
async def process_title(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['title'] = message.text

    await ProductState.next()
    await message.answer('Описание?', reply_markup=back_markup())
@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):

    await ProductState.title.set()

    async with state.proxy() as data:

        await message.answer(f"Изменить название с <b>{data['title']}</b>?", reply_markup=back_markup())
@dp.message_handler(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['body'] = message.text

    await ProductState.next()
    await message.answer('Фото?', reply_markup=back_markup())
@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO, state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):

    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    async with state.proxy() as data:
        data['image'] = downloaded_file

    await ProductState.next()
    await message.answer('Цена?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.TEXT, state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):

    if message.text == back_message:

        await ProductState.body.set()

        async with state.proxy() as data:

            await message.answer(f"Изменить описание с <b>{data['body']}</b>?", reply_markup=back_markup())

    else:

        await message.answer('Вам нужно прислать фото товара.')


@dp.message_handler(IsAdmin(), lambda message: not message.text.isdigit(), state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):

    if message.text == back_message:

        await ProductState.image.set()

        async with state.proxy() as data:

            await message.answer("Другое изображение?", reply_markup=back_markup())

    else:

        await message.answer('Укажите цену в виде числа!')


@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(), state=ProductState.price)
async def process_price(message: Message, state: FSMContext):

    async with state.proxy() as data:

        data['price'] = message.text

        title = data['title']
        body = data['body']
        price = data['price']

        await ProductState.next()
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        markup = check_markup()

        await message.answer_photo(photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)


@dp.message_handler(IsAdmin(), lambda message: message.text not in [back_message, all_right_message], state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await message.answer('Такого варианта не было.')


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):

    await ProductState.price.set()

    async with state.proxy() as data:

        await message.answer(f"Изменить цену с <b>{data['price']}</b>?", reply_markup=back_markup())


@dp.message_handler(IsAdmin(), text=all_right_message, state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    async with state.proxy() as data:

        title = data['title']
        body = data['body']
        image = data['image']
        price = data['price']

        tag = db.fetchone(
            'SELECT title FROM categories WHERE idx=?', (data['category_index'],))[0]
        idx = md5(' '.join([title, body, price, tag]
                           ).encode('utf-8')).hexdigest()

        db.query('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)',
                 (idx, title, body, image, int(price), tag))

    await state.finish()
    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)
    markup.add('/Меню')
    await message.answer('Готово!', reply_markup=markup)
    await process_settings(message)


# delete product


@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict):

    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Удалено!')
    await query.message.delete()



@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='up_price'))
async def redact_price_handler(query: CallbackQuery, callback_data: dict):
    product_idx = callback_data['id']
    current_price = db.fetchall('SELECT price FROM products WHERE idx=?', (product_idx,))[0][0]
    db.query('''UPDATE products
                        SET price = ?
                        WHERE idx = ?''', (current_price+1, product_idx))
    await query.message.answer('Цена поднята!')

@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='down_price'))
async def redact_price_handler(query: CallbackQuery, callback_data: dict):
    product_idx = callback_data['id']
    current_price = db.fetchall('SELECT price FROM products WHERE idx=?', (product_idx,))[0][0]
    db.query('''UPDATE products
                        SET price = ?
                        WHERE idx = ?''', (current_price-1, product_idx))
    await query.message.answer('Цена снижена!')

async def show_products(m, products, category_idx):

    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

    for idx, title, body, image, price, tag in products:

        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} руб.'

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            '🗑️ Удалить', callback_data=product_cb.new(id=idx, action='delete')))
        markup.add(InlineKeyboardButton(
            'Поднять цену на рубль', callback_data=product_cb.new(id=idx, action='up_price')))
        markup.add(InlineKeyboardButton(
            'Снизить цену на рубль', callback_data=product_cb.new(id=idx, action='down_price')))

        await m.answer_photo(photo=image,
                             caption=text,
                             reply_markup=markup)

    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)
    markup.add('/Меню')

    await m.answer('Хотите что-нибудь добавить или удалить?', reply_markup=markup)
