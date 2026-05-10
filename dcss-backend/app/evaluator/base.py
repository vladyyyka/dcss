from abc import ABC, abstractmethod

class BaseQuestChecker(ABC):
    def __init__(self, type_id):
        self.type_id = type_id
        self.progress = {1: 0, 2: 0, 3: 0, 4: 0}
        self.guid = None   

    @abstractmethod
    def update(self, msg_type, msg):
        pass

    @abstractmethod
    def is_finished(self):
        pass

    def get_progress(self):
        return self.progress

    def get_final_result(self):
        return all(v >= 100 for v in self.progress.values())