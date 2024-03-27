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


ABSENCE = 'Внимание! Отсутствует (-ют) {name}'
MESSAGE_DONE = 'Сообщение: "{message}", - успешно отправлено пользователю'
ERROR_API = ('Ошибка запроса к API Практикум.Домашки'
             '{error}'
             'Параметры запроса: url={url},'
             'headers={headers}, params={params}')
ERROR_CODE = ('Ошибка статус-кода ответа от Практикум.Домашки'
              'Код ответа={code}'
              'Параметры запроса: url={url},'
              'headers={headers}, params={params}')
ERROR_MESSAGE = ('В ответе обнаружено сообщение об ошибке: {message}'
                 'по ключу: {key} с параметрами: {params}')
ERROR_TYPE = ('Неправильный тип ответа ({response_type})'
              'от Практикум.Домашка!')
ABSENCE_HW = 'В ответе нет списка домашних работ!'
ERROR_HOMEWORK_TYPE = 'Список домашних работ неверного типа: {type_hw}!'
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
    fail_tokens = [name for name in TOKENS if not globals()[name]]
    if fail_tokens:
        logging.critical(ABSENCE.format(name=fail_tokens))
        raise NameError(ABSENCE.format(name=fail_tokens))


def send_message(bot, message):
    """Отправка сообщений пользователю."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug(MESSAGE_DONE.format(message=message))


def get_api_answer(time):
    """Запрос к API Практикум.Домашки."""
    timestamp = {'from_date': time}
    request_params = dict(url=ENDPOINT, headers=HEADERS, params=timestamp)
    try:
        response = requests.get(**request_params)
    except requests.RequestException as error:
        raise ConnectionError(
            ERROR_API.format(error=error, **request_params)
        )
    if response.status_code != 200:
        raise RuntimeError(
            ERROR_CODE.format(
                code=response.status_code,
                **request_params
            )
        )
    response_dict = response.json()
    for key in ('code', 'error'):
        if response_dict.get(key):
            raise RuntimeError(ERROR_MESSAGE.format(
                message=response_dict.get(key),
                key=key,
                params=(request_params)
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
        raise TypeError(ERROR_HOMEWORK_TYPE.format(
            type_hw=type(homeworks))
        )


def parse_status(homework):
    """Извлечение данных о последней домашней работе."""
    if 'homework_name' not in homework:
        raise KeyError(ERROR_API_KEY)
    name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError(ERROR_API_STATUS)
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError((ERROR_STATUS.format(status=status)))
    return CHANGE_STATUS.format(
        hw_name=name,
        verdict=HOMEWORK_VERDICTS[status]
    )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    bot_time = int(time.time())

    while True:
        old_message = ''
        try:
            statuses = get_api_answer(bot_time)
            check_response(statuses)
            homeworks = statuses.get('homeworks')
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            bot_time = (
                statuses.get('current_date', bot_time)
            )
        except telegram.error.TelegramError as telegram_error:
            message = FAILURE.format(error=telegram_error)
            logging.exception(message)
        except Exception as error:
            message = FAILURE.format(error=error)
            logging.exception(message)
            with suppress(telegram.error.TelegramError):
                if old_message != message:
                    send_message(bot, message)
                    old_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(funcName)s, %(message)s',
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            logging.FileHandler(__file__ + '.log')
        ]
    )
    main()
