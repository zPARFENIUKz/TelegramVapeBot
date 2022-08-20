
from aiogram.types import Message
from loader import dp, db
from .menu import delivery_status
from filters import IsUser

@dp.message_handler(IsUser(), text=delivery_status)
async def process_delivery_status(message: Message):
    
    orders = db.fetchall('SELECT * FROM orders WHERE cid=?', (message.chat.id,))
    
    if len(orders) == 0: await message.answer('Активных заказов нету. Оформить заказ можно в Корзине🛒')
    else: await delivery_status_answer(message, orders)

async def delivery_status_answer(message, orders):

    res = 'Заказ:\n🔥🔥🔥🔥🔥🔥🔥\n'

    for order in orders:

        #items = '\n'.join(ord.strip() + 'шт.' for ord in order[3].split('*'))
        items = order[3]
        res += f'<b>{items}</b>'
    res += '🔥🔥🔥🔥🔥🔥🔥\n'
    answer = [
        'Мы получили твой заказ.🔥\nНапиши менеджеру @vape_brest_manager или подожди пока он сам напишет.👾',
        ' прибыл и ждет вас на почте!'
    ]

    res += answer[0]
    res += '\n\n'

    await message.answer(res)