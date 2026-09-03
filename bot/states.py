from aiogram.fsm.state import StatesGroup, State

class Upl(StatesGroup):
    day_data = State()
    confirmation = State()

class ChangeData(StatesGroup):
    select_number = State()
    action = State()
    choose_field = State()
    enter_new_values = State()

class CaptureProcess(StatesGroup):
    waiting_for_save = State()