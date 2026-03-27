import os
import sys
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_tools import VkHandler
from class_for_database import DatabaseORM

# Загрузка настроек из .env
load_dotenv()

GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
USER_TOKEN = os.getenv('VK_AUTH_TOKEN')
DB_URL = os.getenv('DATABASE_URL')

if not GROUP_TOKEN or not USER_TOKEN:
    print("Ошибка: Токены не найдены в .env файле!")
    sys.exit()

# Инициализация
try:
    db = DatabaseORM(DB_URL)
    db.create_tables()
    vk = VkHandler(USER_TOKEN, GROUP_TOKEN)
    longpoll = VkLongPoll(vk.group_vk)
except Exception as e:
    print(f"Ошибка инициализации: {e}")
    sys.exit()

# Хранилище найденных анкет для каждого пользователя
user_states = {}

def send_msg(user_id, message, attachment=None):
    vk.group_vk.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'attachment': attachment,
        'random_id': 0
    })

def register_user_in_db(vk_id):
    """Регистрация пользователя бота в БД"""
    email = f"id{vk_id}@vk.com"
    user = db.get_user_by_email(email)
    if not user:
        info = vk.get_user_info(vk_id)
        user = db.create_user(email, "vk_auth")
        db.create_or_update_profile(
            user.id, 
            name=f"{info.get('first_name', 'User')} {info.get('last_name', '')}",
            city=info.get('city', {}).get('title') if info.get('city') else "Не указан"
        )
    return user

def show_next_candidate(user_id):
    """Показ следующей анкеты из списка"""
    stack = user_states.get(user_id, [])
    if not stack:
        send_msg(user_id, "Анкеты закончились. Введите 'поиск', чтобы найти новых людей.")
        return

    person = stack[0]
    photos = vk.get_best_photos(person['id'])
    msg = f"{person['first_name']} {person['last_name']}\nСсылка: https://vk.com/id{person['id']}"
    
    send_msg(user_id, msg, attachment=",".join(photos))
    send_msg(user_id, "Команды: 'дальше', 'лайк', 'избранное'")

def main():
    print("Бот запущен. Ожидание сообщений...")
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            u_id = event.user_id
            text = event.text.lower().strip()
            
            # Регистрируем того, кто пишет боту
            current_db_user = register_user_in_db(u_id)

            if text in ["привет", "старт", "поиск"]:
                send_msg(u_id, "Начинаю поиск подходящих людей...")
                u_info = vk.get_user_info(u_id)
                results = vk.search_people(u_info)
                
                if not results:
                    send_msg(u_id, "Никого не нашел. Проверьте настройки своего профиля.")
                else:
                    user_states[u_id] = results
                    show_next_candidate(u_id)

            elif text in ["дальше", "следующий", "нравится"]:
                if u_id in user_states and user_states[u_id]:
                    user_states[u_id].pop(0) # Удаляем текущего
                    show_next_candidate(u_id)
                else:
                    send_msg(u_id, "Сначала введите 'поиск'")

            elif text in ["лайк", "в избранное"]:
                if u_id in user_states and user_states[u_id]:
                    person = user_states[u_id].pop(0)
                    
                    # Сохраняем "цель" в БД
                    target_email = f"id{person['id']}@vk.com"
                    target_user = db.get_user_by_email(target_email)
                    if not target_user:
                        target_user = db.create_user(target_email, "target")
                        db.create_or_update_profile(target_user.id, name=f"{person['first_name']} {person['last_name']}")
                    
                    # Добавляем лайк в таблицу likes
                    db.add_like(current_db_user.id, target_user.id)
                    send_msg(u_id, f"❤️ {person['first_name']} добавлена в избранное!")
                    show_next_candidate(u_id)
                else:
                    send_msg(u_id, "Некого лайкать. Введите 'поиск'")

            elif text in ["избранное", "список"]:
                likes = db.get_user_likes_given(current_db_user.id)
                if not likes:
                    send_msg(u_id, "Ваш список избранного пуст.")
                else:
                    msg_res = "Ваше избранное:\n"
                    for like in likes:
                        p = db.get_profile(like.liked_id)
                        link = f"https://vk.com/id{like.liked.email.replace('id','').replace('@vk.com','')}"
                        msg_res += f"👤 {p.name if p else 'User'} - {link}\n"
                    send_msg(u_id, msg_res)

if __name__ == "__main__":
    main()