from aiogram.dispatcher.filters.state import State, StatesGroup

class BuyState(StatesGroup):
    entering_username = State()
    waiting_for_receipt = State()
