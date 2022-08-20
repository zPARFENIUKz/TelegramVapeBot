
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message
from states import SosState
from filters import IsUser
from loader import dp, db


@dp.message_handler(commands='sos')
async def cmd_sos(message: Message):
    await SosState.question.set()
    await message.answer('В чем суть проблемы? Опишите как можно детальнее и администратор обязательно вам ответит.', reply_markup=ReplyKeyboardRemove())


@dp.message_handler(state=SosState.question)
async def process_question(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text

    await message.answer('Убедитесь, что все верно.', reply_markup=submit_markup())
    await SosState.next()


@dp.message_handler(lambda message: message.text not in [cancel_message, all_right_message], state=SosState.submit)
async def process_price_invalid(message: Message):
    await message.answer('Такого варианта не было.')

from aiogram.types import ReplyKeyboardMarkup
catalog = '🛍️ Каталог'
balance = '💰 Баланс'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'
rewiews = '😎 Отзывы'
@dp.message_handler(text=cancel_message, state=SosState.submit)
async def process_cancel(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(catalog)
    # markup.add(balance, cart)
    markup.add(cart)
    markup.add(delivery_status)
    #markup.add(rewiews)
    await message.answer('Отменено!', reply_markup=markup)
    await state.finish()


@dp.message_handler(text=all_right_message, state=SosState.submit)
async def process_submit(message: Message, state: FSMContext):

    cid = message.chat.id

    #if db.fetchone('SELECT * FROM questions WHERE cid=?', (cid,)) == None:
    if True:

        async with state.proxy() as data:
            db.query('INSERT INTO questions VALUES (?, ?)',
                     (cid, data['question']))
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(catalog)
        # markup.add(balance, cart)
        markup.add(cart)
        markup.add(delivery_status)
        #markup.add(rewiews)
        await message.answer('Отправлено!', reply_markup=markup)

    else:

        await message.answer('Превышен лимит на количество задаваемых вопросов.', reply_markup=ReplyKeyboardRemove())

    await state.finish()
