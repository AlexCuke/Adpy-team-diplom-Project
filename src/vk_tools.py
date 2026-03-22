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
        # Определение пола (если 2(муж), то ищем 1(жен) и наоборот)
        search_sex = 1 if user_info.get('sex') == 2 else 2
        
        # Получаем ID города (если нет, по дефолту Москва - 1)
        city_id = user_info.get('city', {}).get('id', 1)
        
        # Получаем возраст (если нет, ставим 20-30 лет)
        age = user_info.get('age')
        age_from = age - 2 if age else 20
        age_to = age + 2 if age else 30
        
        try:
            res = self.user_vk.method('users.search', {
                'city': city_id,
                'sex': search_sex,
                'status': 6, # В активном поиске
                'age_from': age_from,
                'age_to': age_to,
                'has_photo': 1,
                'count': 30,
                'offset': offset,
                'fields': 'is_closed, can_access_closed'
            })
            # Оставляем только открытые профили
            return [p for p in res.get('items', []) if not p.get('is_closed')]
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
            
            # Сортировка по лайкам
            sorted_photos = sorted(
                photos, 
                key=lambda x: x['likes']['count'], 
                reverse=True
            )
            return [f"photo{p['owner_id']}_{p['id']}" for p in sorted_photos[:3]]
        except:
            return []