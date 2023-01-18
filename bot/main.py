import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from config import TELEGRAM_TOKEN
from config import cmstoken
import logging
from datetime import datetime


group_pattern = r'[А-Яа-я]{4}-\d{2}-\d{2}'
exam_pattern = r'экз (.+)|Экз (.+)|ЭКЗ (.+)'
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

extypes = {
    'экзамен': 'Экзамен',
    'консультация': 'Консультация',
}

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Привет!\nНа период сессии включен режим экзаменов.\nПоддерживается поиск как по "
                                  "фамилии,"
                                  "так и по группе.\n\nПримеры:\n\nКарпов\nКарпов Д.А\nКТСО-04-20\n\nА для поиска "
                                  "экзаменов по дисциплине введите\nэкз <название дисциплины> без кавычек")


def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Поддерживается поиск как по "
                                  "фамилии,"
                                  "так и по группе.\n\nПримеры:\n\nКарпов\nКарпов Д.А\nКТСО-04-20\n\nА для поиска "
                                  "экзаменов по дисциплине введите\nэкз <название дисциплины> без кавычек")


def search(update, context):
    with open('data/exams.json', 'r', encoding='utf-8') as f:
        exams = json.load(f)

    last_name = update.message.text
    exam_ids = [exam_id for exam_id, teacher in exams['teachers'].items() if last_name.lower() in teacher.lower()]

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
        import requests
        rawNames = [exam['teacher']]
        headers = {
            "Authorization": f"Bearer {cmstoken}"}
        params = {"rawNames": rawNames}

        response = requests.get("https://cms.mirea.ninja/api/get-full-teacher-name", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()

            decoded_names = []
            for names in data:
                if len(names["possibleFullNames"]) == 1:
                    decomposed_name = names["possibleFullNames"][0]
                    name = []
                    if surname := decomposed_name.get("lastName"):
                        name.append(surname)
                    if first_name := decomposed_name.get("firstName"):
                        name.append(first_name)
                    if middle_name := decomposed_name.get("middleName"):
                        name.append(middle_name)
                    name = " ".join(name)
                else:
                    name = names["rawName"]
                decoded_names.append(name)

            decoded_names = ", ".join(decoded_names)
        else:
            decoded_names = ", ".join(rawNames)
        text += f'Дата: {exam["day"]} Января ({weekday_str})\n'
        text += f'🧑‍🏫 Преподаватель: {decoded_names}\n'
        text += f'🕜 Время: {exam["time"]}\n'
        text += f'📚 {extypes[exam["extype"]]}\n'
        text += f'📝 {exam["exam"]}\n'
        text += f'🏫 Аудитория: {exam["room"]}\n'
        text += f'👥 Группы: {groups_str}\n\n'

    if not exam_ids:
        text = 'Преподаватель не найден'

    text_len = len(text)
    for i in range(0, text_len, 4096):
        context.bot.send_message(chat_id=update.effective_chat.id, text=text[i: i + 4096], parse_mode='Markdown')


def group_search(update, context):
    with open('data/exams.json', 'r', encoding='utf-8') as f:
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
        other_groups = ""
        for group_id, group in exams['group'].items():
            if exams['day'][group_id] == exam['day'] and exams['month'][group_id] == exam['month'] and exams['rooms'][group_id] == exam['room'] and exams['exam'][group_id] == exam['exam'] and exams['time_start'][group_id] == exam['time'] and group not in exam['groups']:
                other_groups += group + ", "
        other_groups = other_groups[:-2]
        import requests
        rawNames = [exam['teacher']]
        headers = {
            "Authorization": f"Bearer {cmstoken}"}
        params = {"rawNames": rawNames}

        response = requests.get("https://cms.mirea.ninja/api/get-full-teacher-name", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()

            decoded_names = []
            for names in data:
                if len(names["possibleFullNames"]) == 1:
                    decomposed_name = names["possibleFullNames"][0]
                    name = []
                    if surname := decomposed_name.get("lastName"):
                        name.append(surname)
                    if first_name := decomposed_name.get("firstName"):
                        name.append(first_name)
                    if middle_name := decomposed_name.get("middleName"):
                        name.append(middle_name)
                    name = " ".join(name)
                else:
                    name = names["rawName"]
                decoded_names.append(name)

            decoded_names = ", ".join(decoded_names)
        else:
            decoded_names = ", ".join(rawNames)



        text += f'Дата: {exam["day"]} Января ({weekday_str})\n'
        text += f'🧑‍🏫 Преподаватель: {decoded_names}\n'
        text += f'🕜 Время: {exam["time"]}\n'
        text += f'📚 {extypes[exam["extype"]]}\n'
        text += f'📝 {exam["exam"]}\n'
        text += f'🏫 Аудитория: {exam["room"]}\n'
        text += f'👥 Группы: {groups_str}'
        if other_groups:
            text += f' (вместе с: {other_groups})'
        text += '\n\n'
    if not exam_ids:
        text = 'Группа не найдена'

    text_len = len(text)
    for i in range(0, text_len, 4096):
        context.bot.send_message(chat_id=update.effective_chat.id, text=text[i: i + 4096], parse_mode='Markdown')


def exam_search(update, context):
    with open('data/exams.json', 'r', encoding='utf-8') as f:
        exams = json.load(f)
    examname = update.message.text
    examname = examname[4:]
    exam_ids = [exam_id for exam_id, exam in exams['exam'].items() if examname.lower() in exam.lower()]

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
        import requests
        rawNames = [exam['teacher']]
        headers = {
            "Authorization": f"Bearer {cmstoken}"}
        params = {"rawNames": rawNames}

        response = requests.get("https://cms.mirea.ninja/api/get-full-teacher-name", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()

            decoded_names = []
            for names in data:
                if len(names["possibleFullNames"]) == 1:
                    decomposed_name = names["possibleFullNames"][0]
                    name = []
                    if surname := decomposed_name.get("lastName"):
                        name.append(surname)
                    if first_name := decomposed_name.get("firstName"):
                        name.append(first_name)
                    if middle_name := decomposed_name.get("middleName"):
                        name.append(middle_name)
                    name = " ".join(name)
                else:
                    name = names["rawName"]
                decoded_names.append(name)

            decoded_names = ", ".join(decoded_names)
        else:
            decoded_names = ", ".join(rawNames)
        text += f'Дата: {exam["day"]} Января ({weekday_str})\n'
        text += f'🧑‍🏫 Преподаватель: {decoded_names}\n'
        text += f'🕜 Время: {exam["time"]}\n'
        text += f'📚 {extypes[exam["extype"]]}\n'
        text += f'📝 {exam["exam"]}\n'
        text += f'🏫 Аудитория: {exam["room"]}\n'
        text += f'👥 Группы: {groups_str}\n\n'
    if not exam_ids:
        text = 'Экзамен не найден'
    text_len = len(text)
    for i in range(0, text_len, 4096):
        context.bot.send_message(chat_id=update.effective_chat.id, text=text[i: i + 4096], parse_mode='Markdown')


def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start, run_async=True))
    dp.add_handler(CommandHandler('help', help, run_async=True))
    dp.add_handler(MessageHandler(Filters.regex(group_pattern), group_search, run_async=True))
    dp.add_handler(MessageHandler(Filters.regex(exam_pattern), exam_search, run_async=True))
    dp.add_handler(MessageHandler(Filters.text, search, run_async=True))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
