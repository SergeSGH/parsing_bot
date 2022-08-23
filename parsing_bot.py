import logging
import os
from logging.handlers import RotatingFileHandler

import pandas
import prettytable as pt
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from pony.orm import commit, select
from pony.orm.core import db_session

import db_init
from parsing import site_av_price

# устанавливаем настройки для логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=50000000,
    backupCount=5,
    encoding='utf-8'
)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# берем токен бота из локального файла
with open('bot_token.txt', 'r', encoding="utf-8") as f:
    API_TOKEN = f.read()

# инициализируем бот и диспетчер, настраиваем кнопки
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
button_list_data = KeyboardButton('Вывести таблицу')
button_calc_average = KeyboardButton('Посчитать средние цены')
keyb = ReplyKeyboardMarkup(resize_keyboard=True).row(button_list_data, button_calc_average)

# инициализируем базу данных
db_init.init()


# сообщение при запуске бота
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Привет!\nЭто бот для загрузки файлов\nс данными для парсинга!\n",
        reply_markup=keyb
    )


# вывод таблицы
async def data_output(message):
    table = pt.PrettyTable(['#', 'name', 'url', 'xpath'])
    table.align['#'] = 'l'
    table.align['name'] = 'l'
    table.align['url'] = 'l'
    table.align['xpath'] = 'l'
    with db_session:
        query = select(s for s in db_init.Sites)
        for n, record in enumerate(query, 1):
            table.add_row([
                str(n), record.name,
                record.url[:20] + '...' * (len(record.url) > 20),
                record.xpath[:20] + '...' * (len(record.xpath) > 20)
            ])
    await bot.send_message(
        message.from_user.id,
        f'<pre>{table}</pre>',
        parse_mode=types.ParseMode.HTML
    )


# вывод средних цен
async def average_output(message):
    table = pt.PrettyTable(['#', 'name', 'url', 'average price'])
    table.align['#'] = 'l'
    table.align['name'] = 'l'
    table.align['url'] = 'l'
    table.align['average price'] = 'l'
    with db_session:
        query = select(s for s in db_init.Sites)
        for n, record in enumerate(query, 1):
            table.add_row([
                str(n), record.name,
                record.url[:20] + '...' * (len(record.url) > 20),
                site_av_price(record.url, record.xpath)
            ])
    logger.info('Посчитали средние цены')
    await bot.send_message(
        message.from_user.id,
        f'<pre>{table}</pre>',
        parse_mode=types.ParseMode.HTML
    )


# обработка сообщений кнопок
@dp.message_handler(content_types=['text'])
async def message_welcome(message: types.Message):
    if message.text == 'Вывести таблицу':
        await data_output(message)
    elif message.text == 'Посчитать средние цены':
        await average_output(message)


# обработка загруженного файла
@dp.message_handler(content_types=['document'])
async def doc_handler(message: types.Message):
    i = 0
    while os.path.isfile(f'file{i}.xlsx'):
        i += 1
    with open(f'file{i}.xlsx', 'wb') as f:
        await message.document.download(destination_file=f)
        logger.info('Загрузили данные')
    excel_data_df = pandas.read_excel(f'file{i}.xlsx', engine='openpyxl')
    data_list = excel_data_df.to_dict(orient='records')
    table = pt.PrettyTable(['#', 'name', 'url', 'xpath'])
    table.align['#'] = 'l'
    table.align['name'] = 'l'
    table.align['url'] = 'l'
    table.align['xpath'] = 'l'
    for n, record in enumerate(data_list, 1):
        table.add_row([
            str(n),
            str(record.get('name')),
            str(record.get('url'))[:20] + '...' * (len(record.get('url')) > 20),
            str(record.get('xpath'))[:20] + '...' * (len(record.get('xpath')) > 20)
        ])
    await bot.send_message(
        message.from_user.id,
        f'<pre>{table}</pre>',
        parse_mode=types.ParseMode.HTML
    )
    with db_session:
        for record in data_list:
            r = db_init.Sites(
                name=str(record.get('name')),
                url=str(record.get('url')),
                xpath=str(record.get('xpath'))
            )
            commit()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
