from app.database import SessionLocal
from app import models
from app.auth import verify_password

db = SessionLocal()
user = db.query(models.User).filter(models.User.login == 'pilot').first()
if user:
    print("Пользователь найден:", user.login)
    print("Хеш пароля:", user.hashed_password)
    # Проверьте, что пароль 'pilot123' подходит
    print("Пароль верен?", verify_password('pilot123', user.hashed_password))
else:
    print("Пользователь не найден, выполните seed.py")
db.close()