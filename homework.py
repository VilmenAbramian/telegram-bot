from contextlib import suppress
import logging
import os
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


ABSENCE = 'Внимание! Отсутствует {name}'
MSG_DONE = 'Сообщение: "{message}", - успешно отправлено пользователю'
ERROR_API = ('Ошибка запроса к API Практикум.Домашки'
             '{error}'
             'Параметры запроса: url={url},'
             'headers={headers}, params={timestamp}')
ERROR_CODE = ('Ошибка статус-кода ответа от Практикум.Домашки'
              'Код ответа={code}'
              'Параметры запроса: url={url},'
              'headers={headers}, params={timestamp}')
ERROR_MSG = ('В ответе обнаружено сообщение об ошибке: {msg}'
             'по ключу: {key} с параметрами: {params}')
ERROR_TYPE = ('Неправильный тип ответа ({response_type})'
              'от Практикум.Домашка!')
ABSENCE_HW = 'В ответе нет списка домашних работ!'
ERROR_HW_TYPE = 'Список домашних работ неверного типа: {type_hw}!'
ERROR_API_KEY = ('В ответе API Практикум.Домашки'
                 'нет ключа `homework_name`')
ERROR_API_STATUS = 'В ответе Практикум.Домашки не указан статус задания'
ERROR_STATUS = ('В ответе Практикум.Домашки указан'
                'неизвестный статус задания: {status}')
CHANGE_STATUS = 'Изменился статус проверки работы "{hw_name}". {verdict}'
FAILURE = 'Сбой в работе программы: {error}'

TOKENS = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')


def check_tokens():
    """Проверка наличия необходимых для работа бота токенов."""
    flag = 0
    for name in TOKENS:
        if not globals()[name]:
            logging.critical(ABSENCE.format(name=name))
            flag += 1
    if flag > 0:
        raise NameError(ABSENCE.format(name=name))


def send_message(bot, message):
    """Отправка сообщений пользователю."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug(MSG_DONE.format(message=message))


def get_api_answer(timestamp):
    """Запрос к API Практикум.Домашки."""
    timestamp = {'from_date': timestamp}
    try:
        response = requests.get(
            url=ENDPOINT, headers=HEADERS, params=timestamp
        )
    except requests.RequestException as error:
        raise ConnectionError(
            ERROR_API.format(error=error,
                             url=ENDPOINT,
                             headers=HEADERS,
                             timestamp=timestamp)
        )
    if response.status_code != 200:
        raise ConnectionError(
            ERROR_CODE.format(
                code=response.status_code,
                url=ENDPOINT,
                headers=HEADERS,
                timestamp=timestamp
            )
        )
    response_dict = response.json()
    for key in ('code', 'error'):
        if response_dict.get(key):
            raise ConnectionError(ERROR_MSG.format(
                msg=response_dict.get(key),
                key=key,
                params=(ENDPOINT, HEADERS, timestamp)
            )
            )
    return response_dict


def check_response(response):
    """Проверка корректности ответа сервиса Практикум.Домашка."""
    if not isinstance(response, dict):
        raise TypeError((ERROR_TYPE.format(
            response_type=type(response)))
        )
    if 'homeworks' not in response:
        raise KeyError(ABSENCE_HW)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(ERROR_HW_TYPE.format(
            type_hw=type(homeworks))
        )


def parse_status(homework):
    """Извлечение данных о последней домашней работе."""
    if 'homework_name' in homework:
        homework_name = homework['homework_name']
    else:
        raise KeyError(ERROR_API_KEY)
    if 'status' not in homework:
        raise KeyError(ERROR_API_STATUS)
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(
            (ERROR_STATUS.format(status=homework_status))
        )
    return CHANGE_STATUS.format(
        hw_name=homework_name,
        verdict=HOMEWORK_VERDICTS[homework_status]
    )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

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
            message = FAILURE.format(error=telegram_error)
            logging.exception(message)
        except Exception as error:
            message = FAILURE.format(error=error)
            logging.exception(message)
            with suppress(telegram.error.TelegramError):
                old_msg = ''
                if old_msg != message:
                    send_message(bot, message)
                old_msg = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    handler1 = logging.StreamHandler()
    handler2 = logging.FileHandler('logfile.log')

    formatter = logging.Formatter(
        "%(asctime)s, %(levelname)s, %(funcName)s, %(message)s"
    )
    handler1.setFormatter(formatter)
    handler2.setFormatter(formatter)

    logger.addHandler(handler1)
    logger.addHandler(handler2)
    main()
