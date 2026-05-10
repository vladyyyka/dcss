import time
import math
from .base import BaseQuestChecker

class Quest1Checker(BaseQuestChecker):
    def __init__(self):
        super().__init__(type_id=1)
        self.state = {
            'takeoff_detected': False,
            'landing_detected': False,
            'start_position': None,
            'total_distance': 0.0,
            'last_position': None,
            'preflight_done': False
        }

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def update(self, msg_type, msg):
        # Критерий 1: предполётная подготовка – засчитываем сразу
        if not self.state['preflight_done']:
            self.state['preflight_done'] = True
            self.progress[1] = 100
            if self.guid:
                from app.evaluator.quest_evaluator import log_to_file
                log_to_file(self.guid, "Предполётная подготовка (критерий 1) выполнена")

        if msg_type != 'GLOBAL_POSITION_INT':
            return

        lat = msg.lat / 1e7
        lon = msg.lon / 1e7
        alt = msg.relative_alt / 1000.0
        s = self.state

        if s['start_position'] is None:
            s['start_position'] = (lat, lon)

        # Критерий 2: взлёт на 30 м
        if not s['takeoff_detected'] and alt >= 30.0:
            s['takeoff_detected'] = True
            self.progress[2] = 100
            if self.guid:
                from app.evaluator.quest_evaluator import log_to_file
                log_to_file(self.guid, f"Взлёт на {alt:.1f} м (критерий 2 выполнен)")

        # Критерий 3: пройдено 500 м от старта
        if s['takeoff_detected'] and not s['landing_detected']:
            if s['last_position']:
                dist = self._haversine(s['last_position'][0], s['last_position'][1], lat, lon)
                s['total_distance'] += dist
            else:
                s['total_distance'] = 0.0
            s['last_position'] = (lat, lon)
            old_progress = self.progress[3]
            new_progress = min(100, int(s['total_distance'] / 500.0 * 100))
            if new_progress > old_progress:
                self.progress[3] = new_progress
                if self.guid and new_progress % 10 == 0:  # пишем каждые 10%
                    from app.evaluator.quest_evaluator import log_to_file
                    log_to_file(self.guid, f"Пройдено {s['total_distance']:.0f} м, прогресс {new_progress}%")

        # Критерий 4: посадка в радиусе 5 м от старта
        if s['takeoff_detected'] and not s['landing_detected'] and alt <= 1.0:
            if s['start_position']:
                dist_to_start = self._haversine(s['start_position'][0], s['start_position'][1], lat, lon)
                if dist_to_start <= 5.0:
                    self.progress[4] = 100
                    if self.guid:
                        from app.evaluator.quest_evaluator import log_to_file
                        log_to_file(self.guid, f"Посадка в радиусе {dist_to_start:.1f} м от старта (критерий 4 выполнен)")
                else:
                    if self.guid:
                        from app.evaluator.quest_evaluator import log_to_file
                        log_to_file(self.guid, f"Посадка слишком далеко от старта ({dist_to_start:.1f} м), критерий 4 не засчитан")
            s['landing_detected'] = True

    def is_finished(self):
        return self.state.get('landing_detected', False)