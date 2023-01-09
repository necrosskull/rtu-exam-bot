import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import os
from config import TELEGRAM_TOKEN
import logging
from datetime import datetime
import textwrap
import re
group_pattern = r'[А-Яа-яA-Za-z]{4}-\d{2}-\d{2}'
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет!\nНа период сессии включен режим экзаменов, в базе есть экзамены следующих институтов ИИИ, ИИТ, ИРИ, ИПТИП\nПоддерживается поиск как по фамилии, так и по группе.\n\nПримеры:\nКарпов\nКарпов Д.А\nКТСО-04-20\n")


def search(update, context):

    with open('exams.json', 'r') as f:
        exams = json.load(f)

    last_name = update.message.text
    exam_ids = [exam_id for exam_id, teacher in exams['teachers'].items() if last_name.lower() in teacher.lower()]

    unique_exams = {}

    for exam_id in exam_ids:
        if (exams['day'][exam_id], exams['month'][exam_id], exams['time_start'][exam_id]) in unique_exams:
            unique_exams[(exams['day'][exam_id], exams['month'][exam_id], exams['time_start'][exam_id])]['groups'].append(exams['group'][exam_id])
        else:
            unique_exams[(exams['day'][exam_id], exams['month'][exam_id], exams['time_start'][exam_id])] = {
                'exam': exams["exam"][exam_id],
                'room': exams["rooms"][exam_id],
                'time': exams["time_start"][exam_id],
                'day': exams["day"][exam_id],
                'month': exams["month"][exam_id],
                'groups': [exams['group'][exam_id]],
                'extype': exams["exam_type"][exam_id],
                'teacher': exams["teachers"][exam_id]
            }

    sorted_exams = sorted(unique_exams.values(), key=lambda x: (x['month'], x['day'], x['time']))


    text = ''
    for exam in sorted_exams:
        groups_str = ', '.join(exam['groups'])
        date_str = '2023-01-[day]'.replace('[day]', str(exam['day']))
        date = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = date.weekday()
        weekday_str = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][weekday]
        text += f'*Дата: {exam["day"]} Января ({weekday_str})*\n'
        text += f'*🧑‍🏫 Преподаватель: {exam["teacher"]}*\n'
        text += f'*🕜 Время: {exam["time"]}*\n'
        text += f'*📚 {exam["extype"]}*\n'
        text += f'📝 {exam["exam"]}\n'
        text += f'*🏫 Аудитория: {exam["room"]}*\n'
        text += f'👥 Группы: {groups_str}\n\n'

    if not exam_ids:
        text = 'Преподаватель не найден'

    text_len = len(text)
    for i in range(0, text_len, 4096):
        context.bot.send_message(chat_id=update.effective_chat.id, text=text[i : i + 4096], parse_mode='Markdown')


def group_search(update, context):
    with open('exams.json', 'r') as f:
        exams = json.load(f)

    group_name = update.message.text
    exam_ids = [exam_id for exam_id, group in exams['group'].items() if group_name.lower() in group.lower()]

    unique_exams = {}

    for exam_id in exam_ids:
        if (exams['day'][exam_id], exams['month'][exam_id], exams['time_start'][exam_id]) in unique_exams:
            unique_exams[(exams['day'][exam_id], exams['month'][exam_id], exams['time_start'][exam_id])][
                'groups'].append(exams['group'][exam_id])
        else:
            unique_exams[(exams['day'][exam_id], exams['month'][exam_id], exams['time_start'][exam_id])] = {
                'exam': exams["exam"][exam_id],
                'room': exams["rooms"][exam_id],
                'time': exams["time_start"][exam_id],
                'day': exams["day"][exam_id],
                'month': exams["month"][exam_id],
                'groups': [exams['group'][exam_id]],
                'extype': exams["exam_type"][exam_id],
                'teacher': exams["teachers"][exam_id]
            }

    sorted_exams = sorted(unique_exams.values(), key=lambda x: (x['month'], x['day'], x['time']))

    text = ''
    for exam in sorted_exams:
        groups_str = ', '.join(exam['groups'])
        date_str = '2023-01-[day]'.replace('[day]', str(exam['day']))
        date = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = date.weekday()
        weekday_str = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][weekday]
        text += f'*Дата: {exam["day"]} Января ({weekday_str})*\n'
        text += f'*🧑‍🏫 Преподаватель: {exam["teacher"]}*\n'
        text += f'*🕜 Время: {exam["time"]}*\n'
        text += f'*📚 {exam["extype"]}*\n'
        text += f'📝 {exam["exam"]}\n'
        text += f'*🏫 Аудитория: {exam["room"]}*\n'
        text += f'👥 Группы: {groups_str}\n\n'

    if not exam_ids:
        text = 'Группа не найдена'

    text_len = len(text)
    for i in range(0, text_len, 4096):
        context.bot.send_message(chat_id=update.effective_chat.id, text=text[i: i + 4096], parse_mode='Markdown')

def main():

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(group_pattern), group_search))
    dp.add_handler(MessageHandler(Filters.text, search))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
