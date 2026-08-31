from aiogram.fsm.state import StatesGroup, State

class Upl(StatesGroup):
    day_data = State()
    confirmation = State()

class ChangeData(StatesGroup):
    select_number = State()
    action = State()
