import logging
import io
import os
import db_init
from pony.orm import commit, select
from pony.orm.core import db_session
import prettytable as pt
 
import pandas

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


with open('bot_token.txt', 'r', encoding="utf-8") as f:
    API_TOKEN = f.read()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

db_init.init()

button_list_data = KeyboardButton('Вывести таблицу')
button_calc_average = KeyboardButton('Посчитать среднее')

keyb = ReplyKeyboardMarkup(resize_keyboard=True).row(button_list_data, button_calc_average)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi!\nI'm Bot for downloading\nfiles with parsing data!\n", reply_markup=keyb)

async def data_output(message):
    table = pt.PrettyTable(['#', 'name', 'url', 'xpath'])
    table.align['#'] = 'l'
    table.align['name'] = 'l'
    table.align['url'] = 'l'
    table.align['xpath'] = 'l'
    with db_session:
        query = select(s for s in db_init.Sites)
        for n, record in enumerate(query, 1):
            table.add_row(
            [str(n),
            record.name,
            record.url[:15] + '...'*(len(record.url)>15),
            record.xpath[:10] + '...'*(len(record.xpath)>10)])

    await bot.send_message(message.from_user.id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML) 



@dp.message_handler(content_types=['text'])
async def message_welcome(message: types.Message):
    if(message.text == 'Вывести таблицу'):
        await data_output(message)
        # await bot.send_message(message.from_user.id, text='Данные таблицы')
    elif(message.text == 'Посчитать среднее'):
        await bot.send_message(message.from_user.id, text='Средние значения')




@dp.message_handler(content_types=['document'])
async def doc_handler(message: types.Message):
    i = 0
    while os.path.isfile(f'file{i}.xlsx'):
        i += 1
    with open(f'file{i}.xlsx', 'wb') as f:
        await message.document.download(destination_file=f)




    excel_data_df = pandas.read_excel(f'file{i}.xlsx', engine='openpyxl')

    # print whole sheet data
    # print(excel_data_df)
    data_list = excel_data_df.to_dict(orient='records')
    # await bot.send_message(message.from_user.id, 'Добавленные сайты для поиска:',)


