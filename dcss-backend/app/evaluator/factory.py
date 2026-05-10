from .quest1 import Quest1Checker
from .quest2 import Quest2Checker

def get_quest_checker(type_id):
    if type_id == 1:
        return Quest1Checker()
    elif type_id == 2:
        return Quest2Checker()
    else:
        raise ValueError(f"Неизвестный тип задания: {type_id}")