import logging
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.products_from_cart import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from aiogram.types.chat import ChatActions
from states import CheckoutState
from loader import dp, db, bot
from filters import IsUser
from .menu import cart

catalog = '🛍️ Каталог'
balance = '💰 Баланс'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'
rewiews = '😎 Отзывы'
@dp.message_handler(text=rewiews)
async def show_rewiews(message: Message):
    rewiews = db.fetchall('SELECT * FROM rewiews')
    for photo in rewiews:
        await message.answer_photo(photo=photo[0])
    await message.answer('Отзывы о нашей работе 😎👆')


@dp.message_handler(IsUser(), text=cart)
async def process_cart(message: Message, state: FSMContext):

    cart_data = db.fetchall(
        'SELECT * FROM cart WHERE cid=?', (message.chat.id,))

    if len(cart_data) == 0:

        await message.answer('В корзине пока пусто😶‍🌫️\nЖми на Каталог и выбирай то, что тебе интересно👀')

    else:

        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        async with state.proxy() as data:
            data['products'] = {}

        order_cost = 0

        for _, idx, count_in_cart, title in cart_data:

            product = db.fetchone('SELECT * FROM products WHERE idx=?', (idx,))

            if product == None:

                db.query('DELETE FROM cart WHERE idx=?', (idx,))

            else:
                _, title, body, image, price, _ = product
                order_cost += price

                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart]

                markup = product_markup(idx, count_in_cart)
                text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price}Руб.'

                await message.answer_photo(photo=image,
                                           caption=text,
                                           reply_markup=markup)

        if order_cost != 0:
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('📦 Оформить заказ')
            markup.add('Вернуться в меню')

            await message.answer('Перейти к оформлению?',
                                 reply_markup=markup)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='count'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='increase'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='decrease'))
async def product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):

    idx = callback_data['id']
    action = callback_data['action']

    if 'count' == action:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                await query.answer('Количество - ' + data['products'][idx][2])

    else:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                data['products'][idx][2] += 1 if 'increase' == action else -1
                count_in_cart = data['products'][idx][2]

                if count_in_cart == 0:

                    db.query('''DELETE FROM cart
                    WHERE cid = ? AND idx = ?''', (query.message.chat.id, idx))

                    await query.message.delete()
                else:

                    db.query('''UPDATE cart 
                    SET quantity = ? 
                    WHERE cid = ? AND idx = ?''', (count_in_cart, query.message.chat.id, idx))

                    await query.message.edit_reply_markup(product_markup(idx, count_in_cart))


@dp.message_handler(IsUser(), text='📦 Оформить заказ')
async def process_checkout(message: Message, state: FSMContext):

    await CheckoutState.check_cart.set()
    await checkout(message, state)
    await CheckoutState.next()
    #await CheckoutState.next()
    async with state.proxy() as data:
        data['name'] = message.from_user.first_name
        data['address'] = message.from_user.last_name



async def checkout(message, state):
    answer = ''
    total_price = 0

    async with state.proxy() as data:

        for title, price, count_in_cart in data['products'].values():

            tp = count_in_cart * price
            answer += f'<b>{title}</b> * {count_in_cart}шт. = {tp}Руб.\n'
            total_price += tp
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(all_right_message)
    markup.add(cancel_message)
    await message.answer(f'{answer}\nОбщая сумма заказа: {total_price}Руб.',
                         reply_markup=markup)

@dp.message_handler(IsUser(), text=cancel_message, state=CheckoutState.name)
async def stop_order(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    # markup.row(user_message, admin_message)
    # markup.row('/Меню')
    markup.add(catalog)
    # markup.add(balance, cart)
    markup.add(cart)
    markup.add(delivery_status)
    # markup.add(rewiews)
    await message.answer('Оформление заказа приостановлено', reply_markup=markup)
    await state.finish()



@dp.message_handler(IsUser(), lambda message: message.text not in [all_right_message, back_message], state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message):
    markup = ReplyKeyboardMarkup()
    markup.add('Вернуться в меню')
    await message.reply('Такого варианта не было.', reply_markup=markup)


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.finish()
    await process_cart(message, state)


@dp.message_handler(IsUser(), text=all_right_message, state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    await CheckoutState.next()
    await message.answer('Напиши когда и где удобно встретиться.',
                         reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    await CheckoutState.check_cart.set()
    await checkout(message, state)


@dp.message_handler(IsUser(), state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):

    async with state.proxy() as data:

        data['name'] = message.from_user.first_name

        if 'address' in data.keys():

            await confirm(message)
            await CheckoutState.confirm.set()

        else:

            await CheckoutState.next()
            await message.answer('Укажите свой адрес места жительства.',
                                 reply_markup=back_markup())


'''@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):

    async with state.proxy() as data:

        await message.answer('Изменить имя с <b>' + data['name'] + '</b>?',
                             reply_markup=back_markup())

    await CheckoutState.name.set()
'''

@dp.message_handler(IsUser(), state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['address'] = message.text

    await confirm(message)
    await CheckoutState.next()


async def confirm(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(confirm_message)
    markup.add(cancel_message)
    await message.answer('Убедитесь, что все правильно оформлено и подтвердите заказ.',
                         reply_markup=markup)

@dp.message_handler(IsUser(), text=cancel_message, state=CheckoutState.confirm)
async def stop_order(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    # markup.row(user_message, admin_message)
    # markup.row('/Меню')
    markup.add(catalog)
    # markup.add(balance, cart)
    markup.add(cart)
    markup.add(delivery_status)
    # markup.add(rewiews)
    await message.answer('Оформление заказа приостановлено', reply_markup=markup)
    await state.finish()


@dp.message_handler(IsUser(), lambda message: message.text not in [confirm_message, back_message], state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message):
    await message.reply('Такого варианта не было.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    await CheckoutState.address.set()

    async with state.proxy() as data:
        await message.answer('Изменить адрес с <b>' + data['address'] + '</b>?',
                             reply_markup=back_markup())

import time
@dp.message_handler(IsUser(), text=confirm_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    enough_money = True  # enough money on the balance sheet
    markup = ReplyKeyboardRemove()


    if enough_money and not db.user_blocked(message.chat.id):

        logging.info('Deal was made.')

        async with state.proxy() as data:

            cid = message.chat.id
            products = [idx + ' = ' + str(quantity) + 'шт.\n'
                        for idx, quantity in db.fetchall('''SELECT title, quantity FROM cart
            WHERE cid=?''', (cid,))]  # idx=quantity

            db.query('INSERT INTO orders VALUES (?, ?, ?, ?)',
                     (cid, data['name'], data['address'], ''.join(products)))
            rrr = db.fetchall('SELECT * FROM open_orders WHERE cid=?', (cid,) )
            if len(rrr) == 0:
                db.query('INSERT INTO open_orders VALUES (?, ?, ?)',
                            (cid, message.from_user.username, time.time()))

            db.query('DELETE FROM cart WHERE cid=?', (cid,))
            markup = ReplyKeyboardMarkup(resize_keyboard=True)

            # markup.row(user_message, admin_message)
            # markup.row('/Меню')
            markup.add(catalog)
            # markup.add(balance, cart)
            markup.add(cart)
            markup.add(delivery_status)
            #markup.add(rewiews)
            if message.from_user.username != 'None':
                await message.answer('Заказ создан, скоро вам напишет менеджер @vape_brest_manager 🚀\n',
                                     reply_markup=markup)
            else:
                await message.answer('Заказ создан🚀\nПожалуйста напишите менеджеру @vape_brest_manager',
                                     reply_markup=markup)
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)

        # markup.row(user_message, admin_message)
        # markup.row('/Меню')
        markup.add(catalog)
        # markup.add(balance, cart)
        markup.add(cart)
        markup.add(delivery_status)
        #markup.add(rewiews)
        await message.answer('Похоже вы были заблокированы. Если вы считаете что это ошибка, напишите менеджеру @vape_brest_manager',
                             reply_markup=markup)

    await state.finish()
