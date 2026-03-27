import vk_api
from datetime import datetime

class VkHandler:
    def __init__(self, user_token, group_token):
        self.user_vk = vk_api.VkApi(token=user_token)
        self.group_vk = vk_api.VkApi(token=group_token)

    def _calculate_age(self, bdate):
        try:
            if not bdate or len(bdate.split('.')) < 3:
                return None
            today = datetime.today()
            birth = datetime.strptime(bdate, '%d.%m.%Y')
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            return None

    def get_user_info(self, user_id):
        res = self.group_vk.method('users.get', {'user_ids': user_id, 'fields': 'city, bdate, sex'})
        if not res: return {}
        info = res[0]
        info['age'] = self._calculate_age(info.get('bdate'))
        return info

    def search_people(self, user_info, offset=0):
        # Определение пола (ищем противоположный)
        search_sex = 1 if user_info.get('sex') == 2 else 2
        
        # Получаем ID города (если в профиле нет, по умолчанию Москва - 1)
        city_data = user_info.get('city')
        city_id = city_data.get('id') if city_data else 1
        
        # Получаем возраст
        age = user_info.get('age')
        age_from = age - 3 if age else 20
        age_to = age + 3 if age else 30
        
        print(f"--- Параметры поиска ---")
        print(f"Пол: {search_sex}, Город ID: {city_id}, Возраст: {age_from}-{age_to}")

        try:
            res = self.user_vk.method('users.search', {
                'city': city_id,           # ТЕПЕРЬ ПЕРЕДАЕМ ГОРОД
                'sex': search_sex,
                'age_from': age_from,
                'age_to': age_to,
                'has_photo': 1,
                'count': 30,
                'offset': offset,
                'fields': 'is_closed, can_access_closed',
                'v': '5.199'
            })
            items = res.get('items', [])
            # Оставляем только открытые профили
            results = [p for p in items if not p.get('is_closed')]
            print(f"Найдено анкет: {len(results)}")
            return results
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return []

    def get_best_photos(self, owner_id):
        try:
            res = self.user_vk.method('photos.get', {
                'owner_id': owner_id,
                'album_id': 'profile',
                'extended': 1
            })
            photos = res.get('items', [])
            sorted_photos = sorted(
                photos, 
                key=lambda x: x['likes']['count'], 
                reverse=True
            )
            return [f"photo{p['owner_id']}_{p['id']}" for p in sorted_photos[:3]]
        except:
            return []