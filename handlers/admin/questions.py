
from handlers.user.menu import questions
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.types.chat import ChatActions
from states import AnswerState
from loader import dp, db, bot
from filters import IsAdmin
import datetime

@dp.message_handler(IsAdmin(), text='Активные заказы')
async def process_orders(message : Message):
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    #messages = db.fetchall('SELECT * FROM messages ORDER BY message_time ASC')
    open_orders = db.fetchall('SELECT * FROM open_orders')

    if len(open_orders) == 0:
        await message.answer('Нет активных заказов.')
    else:
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        for cid, username, order_time in open_orders:
            time = datetime.datetime.fromtimestamp(order_time)
            text = f'Заказ от @{username}\nБыл оформлен {time.strftime("%d-%m-%Y %H:%M:%S")}'
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text='Подробнее', callback_data=f'order_{cid}_{order_time}_{username}'))
            await message.answer(text, reply_markup=markup)

@dp.message_handler(IsAdmin(), text='Завершенные заказы')
async def process_orders(message : Message):
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    #messages = db.fetchall('SELECT * FROM messages ORDER BY message_time ASC')
    open_orders = db.fetchall('SELECT * FROM closed_orders')

    if len(open_orders) == 0:
        await message.answer('Нет завершенных заказов.')
    else:
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        for cid, username, order_time in open_orders:
            time = datetime.datetime.fromtimestamp(order_time)
            text = f'Заказ от @{username}\nБыл оформлен {time.strftime("%d-%m-%Y %H:%M:%S")}'
            #markup = InlineKeyboardMarkup()
            #markup.add(InlineKeyboardButton(text='Подробнее', callback_data=f'order_{cid}_{order_time}_{username}'))
            await message.answer(text)


from aiogram.dispatcher.filters import Text
from aiogram import types
@dp.callback_query_handler(IsAdmin(), Text(startswith='order_'))
async def admin_orders_call(callback : types.CallbackQuery):
    cid = callback.data.split('_')[1]
    order_time = callback.data.split('_')[2]
    time = datetime.datetime.fromtimestamp(float(order_time))
    username = callback.data.split('_')[3]

    orders = db.fetchall('SELECT * FROM orders WHERE cid=?', (int(cid),))
    res = f'Заказ от {username}\n'
    res += f'Оформлен: {time.strftime("%d-%m-%Y %H:%M:%S")}\n'
    res += 'Товары:\n'
    for order in orders:
        #items = '\n'.join(ord.strip() + 'шт.' for ord in order[3].split('*'))
        items = order[3]
        res += f'<b>{items}</b>\n'
    markup = InlineKeyboardMarkup()
    open_chat_url = f'tg://openmessage?user_id={cid}'
    open_chat_button = InlineKeyboardButton(text='Открыть переписку', url=open_chat_url)
    finish_order_button = InlineKeyboardButton(text='Завершить заказ', callback_data=f"close_{cid}")
    block_this_user = InlineKeyboardButton(text='Заблокировать пользователя', callback_data=f'block_{cid}')
    send_wrme_to_user = InlineKeyboardButton(text='Отправить сообщение чтобы пользователь сам написал', callback_data=f'wrme_{cid}')
    markup.add(open_chat_button)
    markup.add(finish_order_button)
    markup.add(block_this_user)
    markup.add(send_wrme_to_user)
    await callback.message.answer(res, reply_markup=markup)
    await callback.answer()

@dp.callback_query_handler(IsAdmin(), Text(startswith='wrme_'))
async def wrme_to_user(callback : types.CallbackQuery):
    try:
        await bot.send_message(int(callback.data.split('_')[1]), text='❗️❗️❗️Из-за политики телеграма менеджер не может написать вам первым чтобы передать вам ваш заказ, пожалуйста напишите ему: @vape_brest_manager')
        await callback.message.answer(text='Сообщение было отправлено заказчику')
        await callback.answer()
    except:
        await callback.message.answer(text='Ошибка при отправке сообщения заказчику')

@dp.callback_query_handler(IsAdmin(), Text(startswith='block_'))
async def admin_preblock_user(callback : types.CallbackQuery):
    cid = callback.data.split('_')[1]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text='Да', callback_data=f"fblock_{cid}"))
    await callback.message.answer('Точно Заблокировать пользователя?', reply_markup=markup)

@dp.callback_query_handler(IsAdmin(), Text(startswith='fblock_'))
async def admin_block_user(callback : types.CallbackQuery):
    cid = callback.data.split('_')[1]
    cid_open_orders = db.fetchall('SELECT * FROM open_orders WHERE cid=?', (int(cid),))
    if len(cid_open_orders):
        #for cid, username, order_time in cid_open_orders:
            # Сосиска
            #db.query("INSERT INTO closed_orders VALUES (?, ?, ?)", (int(cid), username, order_time))
        db.query("DELETE FROM orders WHERE cid=?", (int(cid),))
        db.query("DELETE FROM open_orders WHERE cid=?", (int(cid),))
        await callback.message.answer('Заказ был успешно завершен.')
    else:
        await callback.message.answer('Заказ был завершен ранее, поэтому он не может быть завершен еще раз.')
    db.query(f'INSERT OR IGNORE INTO blocked_users(cid) VALUES({int(cid)})')
    await callback.message.answer('Пользователь был заблокирован.')
    await callback.answer()



@dp.callback_query_handler(IsAdmin(), Text(startswith='close_'))
async def admin_prefinish_order(callback : types.CallbackQuery):
    cid = callback.data.split('_')[1]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text='Да', callback_data=f"fclose_{cid}"))
    await callback.message.answer('Точно завершить заказ?', reply_markup=markup)
    await callback.answer()

@dp.callback_query_handler(IsAdmin(), Text(startswith='fclose_'))
async def admin_finish_order(callback : types.CallbackQuery):
    cid = callback.data.split('_')[1]
    cid_open_orders = db.fetchall('SELECT * FROM open_orders WHERE cid=?', (int(cid),))
    if len(cid_open_orders):
        for cid, username, order_time in cid_open_orders:
            # Сосиска
            db.query("INSERT INTO closed_orders VALUES (?, ?, ?)", (int(cid), username, order_time))
        db.query("DELETE FROM orders WHERE cid=?", (int(cid),))
        db.query("DELETE FROM open_orders WHERE cid=?", (int(cid),))
        await callback.message.answer('Заказ был успешно завершен.')
    else:
        await callback.message.answer('Заказ был завершен ранее, поэтому он не может быть завершен еще раз.')
    await callback.answer()






question_cb = CallbackData('question', 'cid', 'action')
@dp.message_handler(IsAdmin(), text=questions)
async def process_questions(message: Message):

    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    questions = db.fetchall('SELECT * FROM questions')

    if len(questions) == 0:

        await message.answer('Нет вопросов.')

    else:

        for cid, question in questions:

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                'Ответить', callback_data=question_cb.new(cid=cid, action='answer')))

            await message.answer(question, reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), question_cb.filter(action='answer'))
async def process_answer(query: CallbackQuery, callback_data: dict, state: FSMContext):

    async with state.proxy() as data:
        data['cid'] = callback_data['cid']

    await query.message.answer('Напиши ответ.', reply_markup=ReplyKeyboardRemove())
    await AnswerState.answer.set()


@dp.message_handler(IsAdmin(), state=AnswerState.answer)
async def process_submit(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['answer'] = message.text

    await AnswerState.next()
    await message.answer('Убедитесь, что не ошиблись в ответе.', reply_markup=submit_markup())

from aiogram.types import ReplyKeyboardMarkup
catalog = '🛍️ Каталог'
balance = '💰 Баланс'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'
rewiews = '😎 Отзывы'
@dp.message_handler(IsAdmin(), text=cancel_message, state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(catalog)
    # markup.add(balance, cart)
    markup.add(cart)
    markup.add(delivery_status)
    #markup.add(rewiews)

    await message.answer('Отменено!', reply_markup=markup)
    await state.finish()


@dp.message_handler(IsAdmin(), text=all_right_message, state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):

    async with state.proxy() as data:

        answer = data['answer']
        cid = data['cid']

        question = db.fetchone(
            'SELECT question FROM questions WHERE cid=?', (cid,))[0]
        db.query('DELETE FROM questions WHERE cid=?', (cid,))
        text = f'Вопрос: <b>{question}</b>\n\nОтвет: <b>{answer}</b>'

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(catalog)
        # markup.add(balance, cart)
        markup.add(cart)
        markup.add(delivery_status)
        #markup.add(rewiews)

        await message.answer('Отправлено!', reply_markup=markup)
        await bot.send_message(cid, text, reply_markup=markup)

    await state.finish()
