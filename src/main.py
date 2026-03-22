import os
import sys
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_tools import VkHandler

load_dotenv()

# Проверка загрузки переменных
user_token = os.getenv('VK_AUTH_TOKEN')
group_token = os.getenv('VK_GROUP_TOKEN')

if not user_token or not group_token:
    print("Ошибка: Токены не найдены в файле .env")
    sys.exit()

try:
    vk = VkHandler(user_token, group_token)
    # Проверка токена группы при создании LongPoll
    longpoll = VkLongPoll(vk.group_vk)
except Exception as e:
    print(f"Ошибка авторизации в VK: {group_token}")
    print(f"Ошибка авторизации в VK: {e}")
    print("Попробуйте обновить VK_GROUP_TOKEN в файле .env")
    sys.exit()

# Инициализация VK
vk = VkHandler(os.getenv('VK_AUTH_TOKEN'), os.getenv('VK_GROUP_TOKEN'))
longpoll = VkLongPoll(vk.group_vk)

# Хранилище: {user_id: [список кандидатов]}
user_states = {}

def send_msg(user_id, message, attachment=None):
    vk.group_vk.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'attachment': attachment,
        'random_id': 0
    })

def show_next_candidate(user_id):
    stack = user_states.get(user_id, [])
    
    if not stack:
        send_msg(user_id, "Анкеты закончились. Введите 'поиск', чтобы найти новых людей.")
        return

    # Берем первого человека из списка (не удаляя пока что)
    person = stack[0]
    photos = vk.get_best_photos(person['id'])
    
    msg = f"{person['first_name']} {person['last_name']}\nСсылка: https://vk.com/id{person['id']}"
    send_msg(user_id, msg, attachment=",".join(photos))
    send_msg(user_id, "Команды:\n'дальше' - пропустить\n'лайк' - в избранное")

def main():
    print("Бот запущен (без БД)...")
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            text = event.text.lower().strip()

            if text in ["привет", "старт", "поиск"]:
                send_msg(user_id, "Ищу подходящих людей...")
                u_info = vk.get_user_info(user_id)
                
                # Поиск людей (результаты хранятся только в этой сессии)
                results = vk.search_people(u_info)
                
                if not results:
                    send_msg(user_id, "Никого не нашлось. Проверьте, указан ли у вас город в профиле.")
                else:
                    user_states[user_id] = results
                    show_next_candidate(user_id)

            elif text in ["дальше", "следующий"]:
                if user_id in user_states and user_states[user_id]:
                    # Удаляем просмотренного и показываем следующего
                    user_states[user_id].pop(0)
                    show_next_candidate(user_id)
                else:
                    send_msg(user_id, "Сначала введите 'поиск'")

            elif text in ["лайк", "в избранное"]:
                if user_id in user_states and user_states[user_id]:
                    person = user_states[user_id].pop(0)
                    # Просто выводим подтверждение (сохранять некуда)
                    send_msg(user_id, f"❤️ {person['first_name']} добавлена в ваш список (временно)!\nИдем дальше:")
                    show_next_candidate(user_id)
                else:
                    send_msg(user_id, "Некого лайкать. Введите 'поиск'")

if __name__ == "__main__":
    main()