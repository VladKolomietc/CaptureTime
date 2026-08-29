from aiogram.fsm.state import StatesGroup, State

class Upl(StatesGroup):
    day_data = State()
    confirmation = State()