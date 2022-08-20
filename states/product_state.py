from aiogram.dispatcher.filters.state import StatesGroup, State

class MailingState(StatesGroup):
    message_text = State()
    image = State()
    confirm = State()

class ProductState(StatesGroup):
    title = State()
    body = State()
    image = State()
    price = State()
    confirm = State()

class CategoryState(StatesGroup):
    title = State()

class ChatState(StatesGroup):
    inchat = State()

class AddRewiewState(StatesGroup):
    photo_rewiew = State()