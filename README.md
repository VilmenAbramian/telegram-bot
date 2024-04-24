# Проект бот для Telegram
**Telegram бот** - проект, помогающий отследить статус код-ревью других проектов на платформе Яндекс.Практикум
![27_1700215565](https://github.com/VilmenAbramian/telegram-bot/assets/58857991/e8d93b08-ae1a-47a3-852b-e07a80e0c7d8)

### Используемые технологии:
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
### Запуск проекта:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/VilmenAbramian/telegram-bot
```
```
cd telegram-bot
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
```
-   Для Linux/macOS
```
source env/bin/activate
```
-   Для Windows
```
source env/scripts/activate
```
Обновить менеджер пакетов pip
```
python3 -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
Создать бота в Telegram: https://core.telegram.org/bots

В директории проекта требуется создать файл с названием `.env`, в котором нужно определить 3 переменные: `PRACTICUM_TOKEN` - токен для доступа к API Яндекс.Практикум, `TELEGRAM_TOKEN` - токен Telegram бота , `TELEGRAM_CHAT_ID` - идентификатор пользователя (можно узнать с помощью @userinfobot).
Пример файла:
```
PRACTICUM_TOKEN = 'your_yandex_practicum_token'
TELEGRAM_TOKEN = 'your_telegram_bot_token'
TELEGRAM_CHAT_ID = 'your_telegram_chat_token'
```
### Устройство проекта:
В проекте реализовано несколько функций:

**Функция main()** описывает основную логику работы программы. Все остальные функции запускаются из неё. Последовательность действий в общем виде следующая:
1.  Сделать запрос к API.
2.  Проверить ответ.
3.  Если есть обновления — получить статус работы из обновления и отправить сообщение в Telegram.
4.  Подождать некоторое время и вернуться в пункт 1.

**Функция check_tokens()** проверяет доступность переменных окружения, которые необходимы для работы программы. Если отсутствует хотя бы одна переменная окружения — продолжать работу бота нет смысла.

**Функция get_api_answer()** делает запрос к единственному эндпоинту API-сервиса. В качестве параметра в функцию передается временная метка. В случае успешного запроса возвращает ответ API, приведя его из формата JSON к типам данных Python.

**Функция check_response()** проверяет ответ API на соответствие документации API сервиса Практикум.Домашка. В качестве параметра функция получает ответ API, приведенный к типам данных Python.

**Функция parse_status()** извлекает из информации о конкретной домашней работе статус этой работы. В качестве параметра функция получает только один элемент из списка домашних работ. В случае успеха, функция возвращает подготовленную для отправки в Telegram строку, содержащую один из вердиктов словаря `HOMEWORK_VERDICTS`.

**Функция send_message()** отправляет сообщение в Telegram чат, определяемый переменной окружения `TELEGRAM_CHAT_ID`. Принимает на вход два параметра: экземпляр класса `Bot` и строку с текстом сообщения.

### Логирование:
В процессе работы проект создаёт журнал логов в файле `homework.py.log`, в котором содержится информация о следующих событиях:
-   отсутствие обязательных переменных окружения во время запуска бота (уровень CRITICAL).
-   удачная отправка любого сообщения в Telegram (уровень DEBUG);
-   сбой при отправке сообщения в Telegram (уровень ERROR);
-   недоступность эндпоинта [https://practicum.yandex.ru/api/user_api/homework_statuses/](https://practicum.yandex.ru/api/user_api/homework_statuses/) (уровень ERROR);
-   любые другие сбои при запросе к эндпоинту (уровень ERROR);
-   отсутствие ожидаемых ключей в ответе API (уровень ERROR);
-   неожиданный статус домашней работы, обнаруженный в ответе API (уровень ERROR);
-   отсутствие в ответе новых статусов (уровень DEBUG).

События уровня ERROR не только записываются в журнал, но и отправляются в telegram чат.

Примеры записей в журнале:
```
2024-03-09 15:34:45,150 [ERROR] Сбой в работе программы: Эндпоинт https://practicum.yandex.ru/api/user_api/homework_statuses/111 недоступен. Код ответа API: 404
2024-03-09 15:34:45,355 [DEBUG] Бот отправил сообщение "Сбой в работе программы: Эндпоинт [https://practicum.yandex.ru/api/user_api/homework_statuses/](https://practicum.yandex.ru/api/user_api/homework_statuses/) недоступен. Код ответа API: 404"
```
или
```
2021-10-09 16:19:13,149 [CRITICAL] Отсутствует обязательная переменная окружения: 'TELEGRAM_CHAT_ID'
Программа принудительно остановлена.
```
Примеры сообщений:

<img width="448" alt="Снимок экрана 2024-04-24 в 14 28 36" src="https://github.com/VilmenAbramian/telegram-bot/assets/58857991/6e562775-99b9-4f33-8b18-fb67e3fdc544">
<img width="482" alt="Снимок экрана 2024-04-24 в 14 28 54" src="https://github.com/VilmenAbramian/telegram-bot/assets/58857991/64887d53-6e47-4aee-a57b-3d15ee9469e0">

Проект-12

![GitHub top language](https://img.shields.io/github/languages/top/VilmenAbramian/telegram-bot)
