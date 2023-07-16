import asyncio
import json
import logging
import re
import datetime

import aiofiles
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, Application

from bot import config
from decode import decode_teachers
from config import TELEGRAM_TOKEN
from lazy_logger import lazy_logger

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

MONTHS = {
    1: "Января",
    2: "Февраля",
    3: "Марта",
    4: "Апреля",
    5: "Мая",
    6: "Июня",
    7: "Июля",
    8: "Августа",
    9: "Сентября",
    10: "Октября",
    11: "Ноября",
    12: "Декабря"
}

WEEKDAYS = {
    1: "Понедельник",
    2: "Вторник",
    3: "Среда",
    4: "Четверг",
    5: "Пятница",
    6: "Суббота",
    7: "Воскресенье"
}

GROUP_PATTERN = r'[А-Яа-я]{4}-\d{2}-\d{2}'
ROOM_PATTERN = re.compile(r'ауд (.+)', re.IGNORECASE)


async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Привет!\nНа период сессии включен режим сессии.\n\n"
                                        "Доступен поиск по преподавателям, группам и аудиториям.\n"
                                        "Введите ваш запрос.\n\n"
                                        "Примеры: \n"
                                        "`Карпов Д.А.`\n"
                                        "`Иванов`\n"
                                        "`ИВБО-07-22`\n"
                                        "`ауд 307`\n"
                                        "`ауд г-428`\n"
                                   , parse_mode='Markdown')


async def search(update, context):
    query = update.message.text
    mode = determine_search_mode(query)

    if mode == 'teacher':
        query = prepare_teacher_query(query)
    elif mode == 'group':
        query = query.lower()
    elif mode == 'room':
        query = query.lower()[4:]

    if len(query) < 3:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Слишком короткий запрос")
        return

    lazy_logger.info(json.dumps({"type": "request", "query": query.lower(), **update.message.from_user.to_dict()},
                                ensure_ascii=False))

    exams = await load_exams_from_file()

    exam_ids = find_exam_ids(query, exams, mode)

    if not exam_ids:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="По вашему запросу ничего не найдено")
        return

    unique_exams = create_unique_exams(exam_ids, exams)
    sorted_exams = sort_exams(unique_exams)

    if mode == 'teacher':
        context.user_data['teacher'] = query
        surnames_count = await check_same_surnames(sorted_exams, update, context)
        if surnames_count:
            return

    await send_exam_info(update, context, sorted_exams, mode)


async def check_same_surnames(sorted_exams, update, context):
    surnames = list(set([exam[1]['teacher'] for exam in sorted_exams]))
    surnames_str = ', '.join(await decode_teachers(surnames))
    for surname in surnames:
        if context.user_data['teacher'] == surname.lower():
            return
    surnames_count = len(surnames)
    if surnames_count > 1:
        keyboard = [[surname] for surname in surnames]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"По запросу ({context.user_data['teacher'][:-1].title()}) найдено несколько "
                                            f"преподавателей:\n\n({surnames_str})"
                                            f"\n\nУточните запрос:",
                                       reply_markup=reply_markup)
        return surnames_count


def determine_search_mode(query):
    if re.match(GROUP_PATTERN, query):
        return 'group'
    elif re.match(ROOM_PATTERN, query):
        return 'room'
    return 'teacher'


def prepare_teacher_query(query):
    if " " not in query:
        query += " "
    return query.lower()


async def load_exams_from_file():
    async with aiofiles.open('data/exams.json', 'r', encoding='utf-8') as f:
        exams = json.loads(await f.read())
    return exams


def find_exam_ids(query, exams, mode):
    if mode == 'teacher':
        exam_ids = [exam_id for exam_id, teacher in exams['teachers'].items() if query in teacher.lower()]
    elif mode == 'group':
        exam_ids = [exam_id for exam_id, group in exams['group'].items() if query == group.lower()]
    else:
        exam_ids = [exam_id for exam_id, room in exams['rooms'].items() if query in room.lower()]
    return exam_ids


def create_unique_exams(exam_ids, exams):
    unique_exams = {}
    for exam_id in exam_ids:
        key = (exams['day'][exam_id], exams['time_start'][exam_id], exams['month'][exam_id])
        if key in unique_exams:
            unique_exams[key]['group'].append(exams['group'][exam_id])
        else:
            unique_exams[key] = {
                'exam': exams['exam'][exam_id],
                'group': [exams['group'][exam_id]],
                'teacher': exams['teachers'][exam_id],
                'room': exams['rooms'][exam_id] if exams['rooms'][exam_id] else "",
                'day': exams['day'][exam_id],
                'month': exams['month'][exam_id],
                'time_start': exams['time_start'][exam_id],
                'type': exams['exam_type'][exam_id] if exams['exam_type'][exam_id] else ""
            }
    return unique_exams


def sort_exams(unique_exams):
    return sorted(unique_exams.items(), key=lambda x: (x[1]['month'], x[1]['day'], x[1]['time_start']))


async def send_exam_info(update, context, sorted_exams, mode):
    chunks = []
    chunk = ""

    for exam in sorted_exams:
        exam_info = await format_exam_info(exam, mode)
        if len(chunk) + len(exam_info) <= 4096:
            chunk += exam_info
        else:
            chunks.append(chunk)
            chunk = exam_info

    if chunk:
        chunks.append(chunk)

    for chunk in chunks:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, reply_markup=ReplyKeyboardRemove())


async def format_exam_info(exam, mode):
    exam_info = ""
    groups = ', '.join(exam[1]['group'])
    date = exam[1]['day']
    time_start = exam[1]['time_start']
    room = exam[1]['room']
    teacher = exam[1]['teacher']
    teachers = ", ".join(await decode_teachers([teacher]))
    lesson = exam[1]['exam']
    time_start = datetime.datetime.strptime(time_start, "%H:%M:%S").strftime("%H:%M")
    month_name = MONTHS[int(exam[1]['month'])]

    weekday = WEEKDAYS[
        datetime.datetime(datetime.datetime.now().year, exam[1].get('month'), exam[1].get('day')).weekday() + 1]

    formatted_time = f"{time_start}"
    exam_info += f"📆 Дата: {date} {month_name} ({weekday})\n"
    exam_info += f'⏰ Время: {formatted_time}\n'
    exam_info += f"🏫 Аудитории: {room}\n"
    exam_info += f'📝 {lesson}\n'
    if len(groups) > 0:
        exam_info += f'👥 Группы: {groups}\n'
    if exam[1]['type']:
        exam_info += f'📚 Тип: {exam[1]["type"].title()}\n'
    if len(teachers) > 0:
        exam_info += f"👨🏻‍🏫 Преподаватели: {teachers}\n\n"
    else:
        exam_info += "\n"

    return exam_info


def main():
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start, block=False))
    application.add_handler(CommandHandler('help', start, block=False))
    application.add_handler(CommandHandler('about', start, block=False))
    application.add_handler(MessageHandler(filters.TEXT, search, block=False))

    application.run_polling()


if __name__ == '__main__':
    main()
