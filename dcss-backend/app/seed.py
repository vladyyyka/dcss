from app.database import SessionLocal, engine
from app import models
from app.auth import get_password_hash

models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()


# Инструктор
instructor = models.User(
    login="instructor",
    email="instructor@dcss.com",
    hashed_password=get_password_hash("instructor123"),
    role=models.UserRole.instructor
)
db.add(instructor)

# Обычный пилот (для тестирования)
pilot = models.User(
    login="pilot",
    email="pilot@example.com",
    hashed_password=get_password_hash("pilot123"),
    role=models.UserRole.pilot
)
db.add(pilot)

# 2. Типы заданий 
types = [
    {
        "name": "Задание №1: Основы управления и взлёт",
        "description": "Отработка базовых навыков: взлёт, полёт по прямой, посадка.",
        "max_time_sec": 900,
        "markdown": """
**Цель:** Научиться взлетать, лететь по прямой и садиться.

**Шаги:**
1. Взлететь на 30 метров.
2. Пролететь 500 метров вперёд.
3. Развернуться и вернуться обратно.
4. Посадить дрон в зону 5 метров.
""",
        "criteria": [
            {"check_id": 1, "name": "Предполётная подготовка", "desc": "Проверил системы, включил Stabilize."},
            {"check_id": 2, "name": "Взлёт на 30 м", "desc": "Поднялся на 30 м и завис."},
            {"check_id": 3, "name": "Пролёт 500 м", "desc": "Пролетел 500 м по прямой."},
            {"check_id": 4, "name": "Посадка", "desc": "Приземлился в радиусе 5 м."}
        ]
    },
    {
    "name": "Задание №2: Навигация и планирование маршрута",
    "description": "Создание автономной миссии в Mission Planner.",
    "max_time_sec": 1800,
    "markdown": """
**Цель:** Научиться создавать и загружать миссию из 5 точек.

**Шаги:**
1. В Mission Planner (вкладка Plan) поставьте 5 точек на карте.
2. Установите высоту 30 м, скорость 5 м/с.
3. Загрузите миссию в дрон.
4. Включите режим **Auto** – дрон выполнит маршрут.
""",
    "criteria": [
        {"check_id": 1, "name": "Составление миссии", "desc": "Правильно построил маршрут из 5 точек."},
        {"check_id": 2, "name": "Выполнение миссии", "desc": "Дрон прошёл все точки в автономном режиме."},
        {"check_id": 3, "name": "Сбор данных", "desc": "Записал телеметрию в заданных точках."},
        {"check_id": 4, "name": "Посадка", "desc": "Успешно приземлился после выполнения миссии."}   # добавлено
    ]
    }
]

for t in types:
    db.add(models.QuestType(**t))

db.commit()
db.close()

print("База данных инициализирована. Созданы пользователи: instructor (пароль instructor123), pilot (пароль pilot123).")
