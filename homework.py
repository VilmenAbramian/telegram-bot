from dotenv import load_dotenv
import logging
import os
import requests
import telegram
import time
import sys


load_dotenv()  # Загружаем секретные данные В пространство переменных


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.ERROR,
    filename='log.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s'
)


def check_tokens():
    """Проверка наличия необходимых для работа бота токенов."""
    if not PRACTICUM_TOKEN:
        logging.critical('Отсутствует токен сервиса Практикум.Домашка!')
        sys.exit('Отсутствует токен сервиса Практикум.Домашка!')
    if not TELEGRAM_TOKEN:
        logging.critical('Отсутствует токен сервиса Telegram')
        sys.exit('Отсутствует токен сервиса Telegram')
    if not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствует ID чата')
        sys.exit('Отсутствует ID чата')


def send_message(bot, message):
    """Отправка сообщений пользователю."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug('Сообщение успешно отправлено пользователю')


def get_api_answer(timestamp):
    """Запрос к API Практикум.Домашки."""
    try:
        response = requests.get(
            url=ENDPOINT, headers=HEADERS, params=timestamp
        )
    except requests.RequestException:
        logging.error('Ошибка запроса к API Практикум.Домашки')
    if response.status_code != 200:
        raise('Статус-код ответа домашки отличен от 200')
    # print(response)
    # print(type(response))
    return response.json()


def check_response(response):
    """Проверка корректности ответа сервиса Практикум.Домашка."""
    if not isinstance(response, dict):
        raise TypeError('Неправильный тип ответа от Практикум.Домашка!')
    assert 'current_date' in response, 'В ответе нет текущей даты!'
    assert 'homeworks' in response, 'В ответе нет списка домашних работ!'
    if not isinstance(response['homeworks'], list):
        raise TypeError('Список домашних работ неверного типа!')


def parse_status(homework):
    """Извлечение данных о последней домашней работе."""
    if 'homework_name' in homework:
        homework_name = homework['homework_name']
    else:
        raise AssertionError(
            'В ответе API Практикум.Домашки нет ключа `homework_name`'
        )
    if 'status' not in homework:
        raise AssertionError(
            'В ответе Практикум.Домашки не указан статус задания'
        )
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise AssertionError(
            'В ответе Практикум.Домашки указан неизвестный статус задания'
        )
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = {'from_date': 0}

    while True:
        try:
            homework_statuses = get_api_answer(timestamp)
            check_response(homework_statuses)
            homeworks = homework_statuses.get('homeworks')
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            timestamp['from_date'] = (
                homework_statuses['current_date'] + RETRY_PERIOD
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()