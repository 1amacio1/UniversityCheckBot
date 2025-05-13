from aiogram import types, Dispatcher, Bot, executor # модули для работы с ботом
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup # модули для создания клавиатур

from aiogram.contrib.middlewares.logging import LoggingMiddleware # модули для создания состояний ожидания сообщений
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN_API # импортируем токен из файла config.py
import sqlite3 # испортируем sqlite - библиотека для работы с базами данных
import pandas as pd # импортируем библиотеку для работы с excel файлами

# подключаем бота по токену, подключаем функцию запоминания состояний (нам нужно будет подключить состояние, когда бот ожидает сообщение от пользователя)
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# создаем класс состояний
class Form(StatesGroup):
    waiting_for_message = State()

# Прописываем тексты для комманд
START_COMMAND_TEXT = """
Привет👋
Я бот, который поможет тебе выбрать вуз, опираясь на твои предпочтения и возможности👨‍🎓

Нажмите /help, и я выведу вам список своих возможностей.
"""

HELP_COMMAND_TEXT = """
<b>Вот всё, что я умею:</b>\n
/start - начать работу
/help - список моих возможностей
/check_vuzes - подобрать ВУЗ
/check_colleges - выбрать колледж
/links - полезные ссылки
/info - инорфмация о боте
"""

INFO_COMMAND_TEXT = """
Наш телеграмм бот поможет определиться будущим студентам с выбором ВУЗА или колледжа.🏛

Наш бот это:
    🔴 Более 100 вузов и колледжей Москвы и Санкт-Петербурга
    🔴 Информация в пару кликов
    🔴 Актуальные баллы и цены на обучение

Также настоятельно рекомендуем ознакомиться с сайтом https://vuzopedia.ru 👨‍🎓
Нажмите /help, чтобы увидеть полный список возможностей.
"""

LINKS_COMMAND_TEXT = """
<b>Ниже представлены ссылки, которые могут быть полезны абитуриентам:</b>

🔴 https://vuzopedia.ru - сайт для изучения образовательных организаций
🔴 https://checkege.rustest.ru - проверить результаты экзаменов
🔴 https://mathus.ru/calendar.php - календарь олимпиад на 24/25 год.

Нажмите /help, чтобы вернуться в меню.
"""

MOSCOW_COLLEGES = """
<b>Самые популярные и современные колледжи Москвы, подходящие под любой балл аттестата:</b>

👉 Компьютерная академия ТОП в г. МоскваЛоготип IT колледж TOP в г. Москва
       Ссылка: https://msk.top-academy.ru

👉 Колледж Архитектуры, Дизайна и Реинжиниринга № 26
       Ссылка: https://www.26kadr.ru

👉 Технологический колледж № 34
       Ссылка: https://tk34.mskobr.ru

👉 Колледж многоуровневого профессионального образования РАНХИГС
       Ссылка: https://kmpo.ranepa.ru

👉 Московский государственный образовательный комплекс
       Ссылка: https://mgok.mskobr.ru

👉 Колледж Автоматизации и Информационных Технологий № 20
       Ссылка: https://kait20.mskobr.ru

👉 Медицинский колледж Управления делами Президента Российской Федерации
       Ссылка: https://mcud.ru

👉 Московский городской открытый колледж
       Ссылка: https://open-college.ru

👉 Колледж предпринимательства № 11
       Ссылка: https://kp11.mskobr.ru
"""

SPB_COLLEGES = """
<b>Самые популярные и современные колледжи Санкт-Петербурга, подходящие под любой балл аттестата:</b>

👉 Петровский колледж
       Ссылка: http://www.petrocollege.ru

👉 Академия управления городской средой, градостроительства и печати
       Ссылка: https://agp.edu.ru

👉 Санкт-Петербургский технический колледж управления и коммерции
       Ссылка: http://www.tcmc.spb.ru

👉 Ленинградский областной колледж культуры и искусства
       Ссылка: https://lokkii.ru

👉 Морская техническая академия имени адмирала Д.Н. Сенявина
       Ссылка: https://spbmta.com

👉 Колледж «Звёздный»
       Ссылка: https://zvezdny.spb.ru

👉 Колледж туризма и гостиничного сервиса
       Ссылка: https://www.ktgs.ru

👉 Российский колледж традиционной культуры
       Ссылка: https://rktk.org

👉 Политехнический колледж городского хозяйства
       Ссылка: https://pkgh.edu.ru
"""

# функция для подключения к базе данных
def connect_db():
    conn = sqlite3.connect("vuzes.db")
    return conn

# Создаем клавиатуру для вывода доп вариантов
def keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Ещё варианты", callback_data="more_var"),
        InlineKeyboardButton("Больше не надо", callback_data="no_more")
    )

    return keyboard

# Функция для получения данных из базы данных. Она принимает город, результаты егэ, платное/очное
def get_universities_by_user_info(city, ege_score, edu_form, prev_ind=0, ind=5):
    #Подключаемся к базе данных через функцию выше
    conn = connect_db()
    cursor = conn.cursor()

    # Пишем sql запрос в базу данных и достаем те вузы, которые соответствуют нашим параметрам
    if edu_form.lower() == 'бюджет':
        query = """
        SELECT Вуз, Бюджет, Ссылка
        FROM universities
        WHERE Регион = ? AND Бюджет <= ?
        ORDER BY Бюджет DESC
        """
        cursor.execute(query, (city, ege_score))
        results = cursor.fetchall()
        
        # Выводим первые 5 подходящих результатов (если их >= 5, иначе выводим все, что есть)
        if results:
            if len(results) >= 5:
                response = "\n\n".join([f"👉 {row[0]}:\n\tСредний балл ЕГЭ на бюджет: {row[1]}\n\tСсылка: {row[2]}" for row in results[prev_ind:ind]])
            else:
                response = "\n\n".join([f"👉 {row[0]}:\n\tСредний балл ЕГЭ на бюджет: {row[1]}\n\tСсылка: {row[2]}" for row in results[prev_ind:ind]]) + "\n\n\tВарианты по вашему запросу закончились."
        else:
            response = "Нет подходящих вузов для поступления по вашему запросу."

    elif edu_form.lower() == 'платное':
        query = """
        SELECT Вуз, Платное, Стоимость, Ссылка
        FROM universities
        WHERE Регион = ? AND Бюджет <= ?
        ORDER BY Платное DESC
        """
        cursor.execute(query, (city, ege_score))
        results = cursor.fetchall()
        
        if results:
            if len(results) >= 5:
                response = "\n\n".join([f"👉 {row[0]}:\n\tСредний балл ЕГЭ на бюджет: {row[1]}\n\tСтоимость: {row[2]} руб.\n\tСсылка: {row[3]}" for row in results[prev_ind:ind]])
            else:
                response = "\n\n".join([f"👉 {row[0]}:\n\tСредний балл ЕГЭ на бюджет: {row[1]}\n\tСтоимость: {row[2]} руб.\n\tСсылка: {row[3]}" for row in results[prev_ind:ind]]) + "\n\n\tВарианты по вашему запросу закончились."
        else:
            response = "Нет подходящих вузов для поступления по вашему запросу."
    else:
        response = "Выбрана неверная форма обучения. Выберите 'бюджет' или 'платное'."

    conn.close()
    return response

# Задаем список команд, которые доступны для запроса пользователем 
async def on_startup(dp):
    await bot.set_my_commands([
        types.BotCommand('start', 'начать работу с ботом'),
        types.BotCommand('check_vuzes', 'подобрать вузы'),
        types.BotCommand('check_colleges', 'подобрать колледжи'),
        types.BotCommand('help', 'список команд'),
        types.BotCommand('info', 'информация о боте'),
        types.BotCommand('links', 'полезные ссылки')
    ])


#Дальше @dp.message_handler(commands=[...]) используется для того, чтобы отлавливать в чате определённую команду, указанную в скобках
#В параметрах text указываем текст сообщения, а в chat_id=message.from_user.id указываем, что сообщение нужно отправить в тот чат, из которого пришла команда

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await bot.send_message(text=START_COMMAND_TEXT, chat_id=message.from_user.id)

#Обработчик команды /help
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await bot.send_message(text=HELP_COMMAND_TEXT, chat_id=message.from_user.id, parse_mode="HTML")

# Обработчик команды /info
@dp.message_handler(commands=["info"])
async def info_command(message: types.Message):
    await bot.send_message(text=INFO_COMMAND_TEXT, chat_id=message.from_user.id, disable_web_page_preview=True)

# Обработчик команды /links
@dp.message_handler(commands=["links"])
async def info_command(message: types.Message):
    await bot.send_message(text=LINKS_COMMAND_TEXT, chat_id=message.from_user.id, disable_web_page_preview=True, parse_mode="HTML")

# Обработчик команды /check_colleges
@dp.message_handler(commands=["check_colleges"])
async def check_colleges_command(message: types.Message):
    await bot.send_message(text="В какой город вы хотите поступать? <b>Напишите Москва или Санкт-Петербург:</b>", chat_id=message.from_user.id, parse_mode="HTML")
    await Form.waiting_for_message.set()

# Команда, ожидающая ответа на вопрос про город, здесь мы используем состояние (бот ожидает ответа и не реагирует на другие команды)
@dp.message_handler(state=Form.waiting_for_message)
async def colleges_func(message: types.Message, state=FSMContext):
    if message.text == "Москва":
        await bot.send_message(text=MOSCOW_COLLEGES, chat_id=message.from_user.id, disable_web_page_preview=True, parse_mode="HTML")
        await state.finish()
    elif message.text == "Санкт-Петербург":
        await bot.send_message(text=SPB_COLLEGES, chat_id=message.from_user.id, disable_web_page_preview=True, parse_mode="HTML")
        await state.finish()
    else:
        await bot.send_message(text='К сожалению, у меня нет такой информации.🙁', chat_id=message.from_user.id, parse_mode="HTML")
        await state.finish()


#Обработчик команды /check_vuzes
@dp.message_handler(commands=['check_vuzes'])
async def check_vuzes_command(message: types.Message):
    await bot.send_message(text="Напиши город для поступления; количество предметов, которые ты сдавал, сумму баллов и выбери бюджет/платное👇\n\n<b>Формат: 'Москва, 3, 222, платное'</b>", chat_id=message.from_user.id, parse_mode="HTML")

last_request = []

# Обрабатываем сообщение, в котором пользователь указывает свои параметра для поиска вузов
@dp.message_handler()
async def make_response(message: types.Message):
    try: # Если формат сообщения корректный, то считываем параметры, делаем запрос в базу данных с помощью функции выше
        region, exams_count, ege_score, edu_form = [item.strip() for item in message.text.split(', ')]
        ege_score = int(ege_score)
        exams_count = int(exams_count)
        if region.lower() == "москва":
            region = "Москва и Московская область"
        
        last_request.extend([region, round(ege_score/exams_count, 1), edu_form])
    
        universities = get_universities_by_user_info(region, round(ege_score/exams_count, 1), edu_form) # функция принимающая параметры и делающая запрос, возвращает список вузов

        if universities:
            await message.reply(f"Найдены следующие университеты:\n\n{universities}", reply_markup=keyboard(), disable_web_page_preview=True)
        else:
            await message.reply("По вашему запросу не найдено подходящих вузов.")
    except Exception as e:
        await message.reply("Ошибка обработки данных!\nУбедитесь, что формат введённых данных корректен.")
        print(e)

# Обрабатываем сообщения, если пользователь хочет получить больше вузов
@dp.callback_query_handler(lambda c: c.data in ["more_var", "no_more"])
async def process_help_request(callback_query: types.CallbackQuery):
    # Если выбырием кнопку more_var(больше вариантов), то выводим следующие 5 вузов
    if callback_query.data == "more_var":
        response = get_universities_by_user_info(last_request[0], last_request[1] - 8, last_request[2])
        last_request.pop(0)
        last_request.pop(0)
        last_request.pop(0)
        await bot.send_message(text=response, chat_id=callback_query.from_user.id, disable_web_page_preview=True)
        await bot.send_message(text="\nБольше вузов на сайте: https://vuzopedia.ru", chat_id=callback_query.from_user.id, disable_web_page_preview=True)    
    # Если выбираем кнопку no_more (больше не надо), то выводим сообщение досвидос.
    else:
        await bot.send_message(text='Спасибо, что выбрали наш сервис! Удачи с поступлением👨‍🎓', chat_id=callback_query.from_user.id, disable_web_page_preview=True)

# start_polling - начинаем работу бота
# dp - указываем, какой бот начинает работу
# skip_update - пропускает все запросы, сделанные пользователем, когда бот был не активен
# on_startup - активируем доступные команды
if __name__=="__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)