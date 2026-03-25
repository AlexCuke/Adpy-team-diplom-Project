from class_for_database import *

# Пример использования:
if __name__ == "__main__":
    # Инициализация ORM
    db = DatabaseORM("postgresql://postgres:1234@localhost/diplom_1", echo=True)

    # Создание таблиц
    db.create_tables()

    # Примеры операций
    # Создание пользователя
    user = db.create_user("test2@example.com", "hashed_password_here")

    if user:
        # Создание профиля
        db.create_or_update_profile(user.id,
                                    name="John Doe Sr",
                                    birth_date=date(1990, 1, 1),
                                    gender="male",
                                    bio="Hello, I'm John!",
                                    city="New York")

        # Добавление фото
        db.add_photo(user.id, "https://example.com/photo1.jpg", is_primary=True)

        # Поиск пользователей
        potential_matches = db.get_potential_matches(user.id)
        print(f"Found {len(potential_matches)} potential matches")