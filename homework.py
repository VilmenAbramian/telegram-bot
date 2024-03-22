from contextlib import suppress
import logging
import os
import sys
import time

from dotenv import load_dotenv
import requests
import telegram


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

PHRASES = {
    'absence': 'Внимание! Отсутствует {name}',
    'msg_done': 'Сообщение: "{message}", - успешно отправлено пользователю',
    'error_api': ('Ошибка запроса к API Практикум.Домашки'
                  '{error}'
                  'Параметры запроса: url={ENDPOINT},'
                  'headers={HEADERS}, params={timestamp}'),
    'error_code': ('Ошибка статус-кода ответа от Практикум.Домашки'
                   'Код ответа={code}'
                   'Параметры запроса: url={ENDPOINT},'
                   'headers={HEADERS}, params={timestamp}'),
    'error_msg': 'В ответе обнаружено сообщение об ошибке: {msg}',
    'error_type': 'Неправильный тип ответа ({response_type})'
                  'от Практикум.Домашка!',
    'absence_hw': 'В ответе нет списка домашних работ!',
    'error_hw_type': 'Список домашних работ неверного типа: {type_hw}!',
    'error_api_key': 'В ответе API Практикум.Домашки'
                     'нет ключа `homework_name`',
    'error_api_status': 'В ответе Практикум.Домашки не указан статус задания',
    'error_status': ('В ответе Практикум.Домашки указан'
                     'неизвестный статус задания: {status}'),
    'change_status': 'Изменился статус проверки работы "{hw_name}". {verdict}',
    'failure': 'Сбой в работе программы: {error}'
}


def check_tokens():
    """Проверка наличия необходимых для работа бота токенов."""
    for name in ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'):
        if not globals()[name]:
            logging.critical(PHRASES['absence'].format(name=name))
            sys.exit(PHRASES['absence'].format(name=name))


def send_message(bot, message):
    """Отправка сообщений пользователю."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug(PHRASES['msg_done'].format(message=message))


def get_api_answer(timestamp):
    """Запрос к API Практикум.Домашки."""
    try:
        response = requests.get(
            url=ENDPOINT, headers=HEADERS, params=timestamp
        )
    except requests.RequestException as error:
        raise RuntimeError(
            PHRASES['error_api'].format(error=error,
                                        ENDPOINT=ENDPOINT,
                                        HEADERS=HEADERS,
                                        timestamp=timestamp)
        )
    if response.status_code != 200:
        raise RuntimeError(
            PHRASES['error_code'].format(
                code=response.status_code,
                ENDPOINT=ENDPOINT,
                HEADERS=HEADERS,
                timestamp=timestamp
            )
        )
    if response.json().get('code'):
        raise RuntimeError(PHRASES['error_msg'].format(
            msg=response.json().get("code"))
        )
    elif response.json().get('error'):
        raise RuntimeError(PHRASES['error_msg'].format(
            msg=response.json().get("error"))
        )
    return response.json()


def check_response(response):
    """Проверка корректности ответа сервиса Практикум.Домашка."""
    if not isinstance(response, dict):
        raise TypeError((PHRASES['error_type'].format(
            response_type=type(response)))
        )
    if not response.get('homeworks'):
        raise KeyError(PHRASES['absence_hw'])
    if not isinstance(response['homeworks'], list):
        raise TypeError(PHRASES['error_hw_type'].format(
            type_hw=type(response['homeworks']))
        )


def parse_status(homework):
    """Извлечение данных о последней домашней работе."""
    if 'homework_name' in homework:
        homework_name = homework['homework_name']
    else:
        raise KeyError(
            PHRASES['error_api_key']
        )
    if 'status' not in homework:
        raise KeyError(
            PHRASES['error_api_status']
        )
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError(
            (PHRASES['error_status'].format(status=homework['status']))
        )
    return PHRASES['change_status'].format(
        hw_name=homework_name,
        verdict=HOMEWORK_VERDICTS[homework["status"]]
    )


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(funcName)s, %(message)s'
    )

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
                homework_statuses.get('current_date', timestamp['from_date'])
            )
        except telegram.error.TelegramError as telegram_error:
            logging.error(telegram_error)
        except Exception as error:
            message = PHRASES['failure'].format(error=error)
            logging.exception(message)
            with suppress(telegram.error.TelegramError):
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
