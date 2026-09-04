from aiogram.fsm.state import StatesGroup, State

class CaptureProcess(StatesGroup):
    waiting_for_save = State()

class ChangeData(StatesGroup):
    select_number = State()
    action = State()
    choose_field = State()
    enter_new_values = State()

