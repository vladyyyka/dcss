import time
from .base import BaseQuestChecker

class Quest2Checker(BaseQuestChecker):
    def __init__(self):
        super().__init__(type_id=2)
        self.state = {
            'mission_loaded': False,
            'total_elements': 0,
            'real_waypoints': 0,
            'waypoints_reached': set(),
            'max_wp_seq': 0,
            'auto_mode_entered': False,
            'data_recorded': False,
            'landing_detected': False,
            'home_position': None,
            'mission_accomplished': False,
        }

    def update(self, msg_type, msg):
        if self.guid:
            from app.evaluator.quest_evaluator import log_to_file

        # 1. Составление миссии 
        if msg_type == 'MISSION_COUNT' and not self.state['mission_loaded']:
            count = msg.count
            self.state['total_elements'] = count
            real = max(0, count - 1)
            self.state['real_waypoints'] = real
            if real >= 2:
                self.state['mission_loaded'] = True
                self.progress[1] = 100
                if self.guid:
                    log_to_file(self.guid, f"Миссия загружена: элементов {count}, реальных waypoint'ов: {real} (критерий 1 выполнен)")
            else:
                if self.guid:
                    log_to_file(self.guid, f"Миссия загружена, но недостаточно waypoint'ов (нужно >=2), имеется {real}")

        # 2. Стартовая позиция
        if msg_type == 'GLOBAL_POSITION_INT' and self.state['home_position'] is None:
            self.state['home_position'] = (msg.lat / 1e7, msg.lon / 1e7)
            if self.guid:
                log_to_file(self.guid, "Стартовая позиция зафиксирована")

        # 3. Выполнение миссии (прогресс только по реальным waypoint'ам)
        if msg_type == 'MISSION_CURRENT':
            wp_seq = msg.seq
            # Иногда seq=0 означает стартовую позицию, не засчитываем
            if wp_seq > 0:
                if wp_seq > self.state['max_wp_seq']:
                    self.state['max_wp_seq'] = wp_seq
                self.state['waypoints_reached'].add(wp_seq)
                total_real = self.state['real_waypoints']
                if total_real > 0:
                    # Прогресс = (максимальный достигнутый номер) / (реальное количество) * 100
                    percent = int(self.state['max_wp_seq'] / total_real * 100)
                    if percent > 100:
                        percent = 100
                    self.progress[2] = percent
                    if self.guid:
                        log_to_file(self.guid, f"Пройдена точка {wp_seq}, прогресс выполнения маршрута: {percent}%")
                # Если достигнут последний реальный waypoint
                if wp_seq >= total_real:
                    self.state['mission_accomplished'] = True
                    if self.guid:
                        log_to_file(self.guid, "Все waypoint'ы миссии пройдены (миссия выполнена)")

        # 4. Режим AUTO
        if msg_type == 'HEARTBEAT' and not self.state['auto_mode_entered']:
            if msg.base_mode & 0x80:
                self.state['auto_mode_entered'] = True
                if self.guid:
                    log_to_file(self.guid, "Режим AUTO активирован")

        # 5. Сбор данных
        if not self.state['data_recorded'] and msg_type in ('GPS_RAW_INT', 'SCALED_PRESSURE', 'VFR_HUD'):
            self.state['data_recorded'] = True
            self.progress[3] = 100
            if self.guid:
                log_to_file(self.guid, "Сбор данных (телеметрия) зафиксирован (критерий 3 выполнен)")

        # 6. Посадка после завершения миссии
        if self.state.get('mission_accomplished', False) and not self.state['landing_detected']:
            if msg_type == 'GLOBAL_POSITION_INT':
                alt = msg.relative_alt / 1000.0
                if alt <= 1.0:
                    self.state['landing_detected'] = True
                    self.progress[4] = 100
                    if self.guid:
                        log_to_file(self.guid, f"Посадка после миссии (высота {alt:.1f} м) – критерий 4 выполнен")

    def is_finished(self):
        return self.state.get('mission_accomplished', False) and self.state.get('landing_detected', False)