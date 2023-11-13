from aiogram import types
import asyncio
import logging
from aiogram import Bot, Dispatcher
from pymongo import MongoClient
from aiogram import F
from aiogram.filters import Command,CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import datetime
client = MongoClient("localhost", 27017)
# Получение списка участников
print("Available databases:", client.list_database_names())
database = client["имя базы"]
books = database["имя документа"]
#подключаем дб
def addb(id,name,i,n):
    #функция для добавления пользователя в бд
    result = books.insert_one({
        "id": str(id),#айди
        "name": str(name),#имя
        "i": int(i),#количество созданных записей
        'n': int(n)#текущее место в списке записей(можно было бы сделать через FSM)
    })



logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token="6556275912:AAGTkq5Tze7D5PwcBDWnOSWaHFUzdJfUkW0")
# Диспетчер
dp = Dispatcher()
#Клавиатура
but = [
        [types.KeyboardButton(text="Сделать запись в блокнот")],
        [types.KeyboardButton(text="Мои записи")]
    ]

#Класс с наследником State с переменной записки
class UserNote(StatesGroup):
    notes = State()


@dp.message(Command("start")) #команда старт
async def send_welcome(message: types.Message):
    reg = books.find_one({"id": str(message.from_user.id)})
    if reg == None:
        addb(message.from_user.id,message.from_user.username,0,1)
    #проверка на наличие пользователя в базе, иначе создаем
    keyboard = types.ReplyKeyboardMarkup(keyboard=but)
    start_message = f'Привет {message.from_user.username}!Я КомфортБот!\n Я могу помочь тебе в написании и структурировании твоих заметок!\n Команда /page [номер заметки],переведет тебя на нужную заметку. '
    await message.answer(start_message, reply_markup=keyboard)

@dp.message(F.text.lower() == "сделать запись в блокнот")
async def with_pur(message: types.Message,state: FSMContext):
    await state.set_state(UserNote.notes)
    await message.reply(f"Введите вашу запись \n Для отмены напишите отмена или /cancel",reply_markup=types.ReplyKeyboardRemove())
@dp.message(Command("page"))
async def go_note(message: types.Message,command: CommandObject):
    try:
        rate = books.find_one({"id": str(message.from_user.id)})
        i = rate['i']
        page = command.args
        if i == 0 or page is None or int(page) > i:
            await message.reply('Ошибка!')
        else:
            await message.reply(rate[f'note{page}'], parse_mode="Markdown")
    except:
        await message.reply('Ошибка!')
        print('Exception error in page command')
@dp.message(UserNote.notes)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(notes=message.text)
    user_note = message.text
    print(user_note)
    if user_note in ['Отмена','/cancel','отмена']:
        keyboard = types.ReplyKeyboardMarkup(keyboard=but)
        await message.answer('Отмена', reply_markup=keyboard)
        await state.clear()
    else:
        rate = books.find_one({"id": str(message.from_user.id)})
        rating = rate['i']
        us = {'id': str(message.from_user.id)}
        nnnw = {'$set': {
            f'note{str(rating + 1)}': f' Запись номер {str(rating + 1)} \n' + user_note + f'\n Создана в *{datetime.datetime.now()}*'}}
        nw = {'$inc': {'i': +1}}
        books.update_one(us, nw)
        books.update_one(us, nnnw)
        keyboard = types.ReplyKeyboardMarkup(keyboard=but)
        await message.answer(f'Ваша запись под номером {str(rating + 1)} создана', reply_markup=keyboard)
        await state.clear()
def get_inline():
    buttons = [
        [
            types.InlineKeyboardButton(text="⬅", callback_data="left"),
            types.InlineKeyboardButton(text="➡", callback_data="right")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
@dp.message(F.text.lower() == "мои записи")
async def with_notecheck(message: types.Message):
    try:
        rate = books.find_one({"id": str(message.from_user.id)})
        nw = {'$set': {'n': 1}}
        books.update_one({'id': str(message.from_user.id)}, nw)
        await message.answer(
            rate['note1'], parse_mode="Markdown",
            reply_markup=get_inline()
        )
    except:
        await message.answer('Ошибка!')
@dp.callback_query(F.data == "left")
async def set_left(callback: types.CallbackQuery):
    rate = books.find_one({"id": str(callback.from_user.id)})
    ni = rate[f'n']
    if ni <= 0:
        nw = {'$set': {'n': 1}}
        books.update_one({'id': str(callback.from_user.id)}, nw)
        await callback.message.edit_text(rate[f'note1'], parse_mode="Markdown", reply_markup=get_inline())
    else:
        nw = {'$inc': {'n': -1}}
        books.update_one({'id': str(callback.from_user.id)}, nw)
        await callback.message.edit_text(rate[f'note{ni-1}'],parse_mode= "Markdown",reply_markup=get_inline())
@dp.callback_query(F.data == "right")
async def set_right(callback: types.CallbackQuery):
    rate = books.find_one({"id": str(callback.from_user.id)})
    ni = rate[f'n']
    inn = rate['i']
    if ni > inn:
        nw = {'$inc': {'n': -1}}
        books.update_one({'id': str(callback.from_user.id)}, nw)
        await callback.message.edit_text(rate[f'note{inn}'], parse_mode="Markdown", reply_markup=get_inline())
    else:
        nw = {'$inc': {'n': +1}}
        books.update_one({'id': str(callback.from_user.id)}, nw)
         # КОД НЕ ВОРКАЕТ ИСПРАВЬ БЛЯЯЯЯЯЯЯЯТЬ
        await callback.message.edit_text(rate[f'note{ni + 1}'], parse_mode="Markdown", reply_markup=get_inline())
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())
  loop.close()



