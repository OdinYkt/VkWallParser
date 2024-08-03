### VK PARSER BOT
Бот для создания группы-двойника (VK -> TG)

### Note
* Информация из группы VK забирается с помощью Selenium (без api vk)
* Телеграмм бот форматирует данные и создаёт пост в заданной группе TG

### Install
* Клонировать репозиторий `git clone https://github.com/OdinYkt/VkWallParser.git`
* Создать виртуальное окружение `python -m venv .venv` и активировать его
* Установить зависимости `pip install -r requirements.txt`

* Задать параметры окружения:
* ##### .env
    ```
    TG_TOKEN_BOT=       # токен бота
    TG_GROUP_ID=        # id группы в tg, куда постить
    
    ADMIN_TG_IDS=        # id админа в tg
    
    INTERVAL_HOURS=1    # интервал запуска
    
    VK_GROUP_NAME=cat0science       # id vk группы
    ```
* Запустить `python main.py`

### Linux
* Для работы на сервере без монитора необходимо установить xvfbwrapper
* Рекомендуется держать включенным, используя systemctl
* Для периодического перезапуска использовать crontab
