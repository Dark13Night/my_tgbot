import logging
import re
import paramiko
import os
import subprocess

import psycopg2
from psycopg2 import Error

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext


from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('TOKEN')
RM_HOST = os.getenv('RM_HOST')
RM_PORT = os.getenv('RM_PORT')
RM_USER = os.getenv('RM_USER')
RM_PASSWORD = os.getenv('RM_PASSWORD')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_REPL_USER = os.getenv('DB_REPL_USER')
DB_REPL_PASSWORD = os.getenv('DB_REPL_PASSWORD')
DB_REPL_HOST = os.getenv('DB_REPL_HOST')
DB_REPL_PORT = os.getenv('DB_REPL_PORT')


logging.basicConfig(
filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(
        f"Привет {user.full_name}! "
        "Я бот, который может выполнять различные задачи. "
        "Такие как поиск телефонных номеров и email в тексте, проверка сложности пароля. "
        "А также мониторинг Linux system с использованием ssh подключения.\n"
        "Для получения более подробной информации используйте комманду /help"
)
    

def helpCommand(update: Update, context):
    update.message.reply_text(
        "Help for you: \n"
        "/find_email - поиск email в тексте\n"
        "/find_phone_number - поиск телефонного номера в тексте\n"
        "/verify_password - проверка сложности пароля\n"
        "Мониторинг Linux-системы: чтобы использовать команды нужно подключиться по ssh, убедитесь что на вашей linux системе включён ssh\n"
        "Сбор информации о системе:\n"
        "1) О релизе. - /get_release \n"
        "2) Об архитектуры процессора, имени хоста системы и версии ядра - /get_uname\n"
        "3) О времени работы - /get_uptime\n"
        "Сбор информации о состоянии файловой системы -/get_df\n"
        "Сбор информации о состоянии оперативной памяти - /get_free\n"
        "Сбор информации о производительности системы - /get_mpstat\n"
        "Сбор информации о работающих в данной системе пользователях -/get_w\n"
        "Сбор логов: \n"
        "1) Последние 10 входов в систему - /get_auths\n"
        "2) Последние 5 критических события - /get_critical\n"
        "Сбор информации о запущенных процессах - /get_ps\n"
        "Сбор информации об используемых портах - /get_ss\n"
        "Сбор информации об установленных пакетах - /get_apt_list\n"
        "Два варианта взаимодействия с предыдущей командой: \n"
        "1 Вывод всех пакетов;\n"
        "2 Поиск информации о пакете, название которого будет запрошено у пользователя.\n"
        "Сбор информации о запущенных сервисах -/get_services\n"
        "/get_repl_logs - вывод логов о репликации бд\n"
        "/get_emails - вывод email из база дынных\n"
        "/get_phone_numbers - вывод телефонных номеров из базы данных\n"

        )

def get_ssh_connection():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=RM_HOST, port=int(RM_PORT), username=RM_USER, password=RM_PASSWORD)
    return ssh

def get_db_connection():
    connect = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_DATABASE
    )
    return connect

FIND_EMAIL, SAVE_EMAILS = range(2)

def findEmailCommand(update: Update, context):
    
    update.message.reply_text("Отправь мне текст, чтобы найти в нем email адреса.")
    return FIND_EMAIL


def findEmails(update: Update, context):
    user_input = update.message.text
    email_regex = r'\b[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+)*' \
                r'@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
    EmailList = re.findall(email_regex, user_input)

    if not EmailList:
        update.message.reply_text('Email не найдены')
        return ConversationHandler.END

    Emails = ''
    for i, email in enumerate(EmailList):
        Emails += f'{i+1}. {email}\n'

    update.message.reply_text(Emails)
    update.message.reply_text('Хотите сохранить эти email-адреса в базу данных? (да/нет)')
    context.user_data['EmailList'] = EmailList 
    return SAVE_EMAILS


def saveEmails(update: Update, context):
    user_answer = update.message.text.lower()
    if user_answer == 'да':
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            for email in context.user_data['EmailList']:
                cursor.execute("INSERT INTO Emails (email) VALUES (%s)", (email,))
            connection.commit()
            update.message.reply_text('Email-адреса успешно сохранены.')
        except Exception as e:
            update.message.reply_text('Произошла ошибка при сохранении email-адресов.')
            print(f'Ошибка подключения: {e}')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
    else:
        update.message.reply_text('Email-адреса не сохранены.')

    return ConversationHandler.END

FIND_PHONE_NUMBERS, SAVE_PHONE_NUMBERS = range(2)

def findPhoneNumbersCommand(update: Update, context):
    
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return FIND_PHONE_NUMBERS


def findPhoneNumbers (update: Update, context):
    user_input = update.message.text
    phoneNumRegex = re.compile(r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})')

    phoneNumberList = phoneNumRegex.findall(user_input) 

    if not phoneNumberList: 
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    
    phoneNumbers = '' 
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'   

    update.message.reply_text(phoneNumbers)
    update.message.reply_text('Хотите сохранить эти email-адреса в базу данных? (да/нет)')
    context.user_data['phoneNumberList'] = phoneNumberList
    return SAVE_EMAILS

def savePhoneNumbers(update: Update, context):
    user_answer = update.message.text.lower()
    if user_answer == 'да':
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            for phoneNumber in context.user_data['phoneNumberList']:
                cursor.execute("INSERT INTO PhoneNumbers (PhoneNumber) VALUES (%s)", (phoneNumber,))
            connection.commit()
            update.message.reply_text('Телефонные номера успешно сохранены.')
        except Exception as e:
            update.message.reply_text('Произошла ошибка при сохранении телефонных номеров.')
            print(f'Ошибка подключения: {e}')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
    else:
        update.message.reply_text('Телефонные номера не сохранены.')

    return ConversationHandler.END

PASSWORD_CHECK, PASSWORD_ENTER = range(2)

def verify_password_command(update, context):
    
    update.message.reply_text("Введите пароль для проверки сложности:")
    return PASSWORD_ENTER

def verify_password(update, context):
    password = update.message.text.strip()
    if verify_password_complexity(password):
        update.message.reply_text("Пароль сложный")
    else:
        update.message.reply_text("Пароль простой")
    return ConversationHandler.END

def verify_password_complexity(password):
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Z]|[А-Я]', password):
        return False
    
    if not re.search(r'[a-z]|[а-я]', password):
        return False
    
    if not re.search(r'[0-9]', password):
        return False
    
    if not re.search(r'[!@#$%^&*()]', password):
        return False
    
    return True


def get_uptime(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('uptime')
        uptime_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Время работы системы: \n{uptime_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END


def get_uname(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('uname -a')
        uname_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о системе: \n{uname_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END



def get_releases(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('lsb_release -a')
        release_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о релизе: \n{release_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END


def get_df(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('df -h')
        df_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о состоянии файловой системы: \n{df_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END



def get_free(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('free -m')
        free_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о состоянии оперативной памяти: \n{free_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END



def get_mpstat(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('mpstat')
        mpstat_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о производительности системы: \n{mpstat_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END



def get_w(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('w')
        w_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о работающих в данной системе пользователях: \n{w_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END



def get_auths(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('last -n 10')
        auths_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Последние 10 входов в систему: \n{auths_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END
    

import subprocess

def get_critical(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('journalctl --system -p info | tail -n 5')
        critical_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Последние 5 критических событий: \n{critical_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END


def get_ps(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('ps aux | head')
        process_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о запущенных процессах: \n{process_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END


def get_ss(update, context):
    
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('ss -tuln')
        port_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация об используемых портах: \n{port_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END

APT_LIST_ACTION, APT_SEARCH_PACKAGE = range(2)


def get_apt_list(update: Update, context: CallbackContext) -> int:
    
    update.message.reply_text("Выберите действие:\n1. Вывести все установленные пакеты.\n2. Найти информацию о конкретном пакете.")
    return APT_LIST_ACTION

def apt_list_action(update: Update, context: CallbackContext) -> int:
    action = update.message.text.strip()
    if action not in ['1', '2']:
        update.message.reply_text("Некорректный ввод. Пожалуйста, выберите 1 или 2.")
        return APT_LIST_ACTION

    if action == '1':
        return get_all_apt_packages(update, context)
    elif action == '2':
        update.message.reply_text("Введите название пакета:")
        return APT_SEARCH_PACKAGE

def get_all_apt_packages(update: Update, context: CallbackContext) -> int:
        
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('apt list --installed | head')
        package_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация об установленных пакетах: \n{package_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END

def apt_search_package(update: Update, context: CallbackContext) -> int:
    package_name = update.message.text.strip()
        
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command(f'apt show {package_name}')
        package_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о пакете '{package_name}': \n{package_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END


def get_services(update, context):
       
    try:
        ssh = get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command('systemctl list-units --type=service | head -n 20')
        service_info = stdout.read().decode('utf-8')
        update.message.reply_text(f"Информация о запущенных сервисах: \n{service_info}")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        ssh.close()
    return ConversationHandler.END


def get_repl_logs(update, context):
    
    connection = None    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
    
        data = cursor.execute("SELECT pg_read_file(pg_current_logfile());")
        data = cursor.fetchall()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        answer = 'Логи репликации:\n'

        for str1 in data.split('\n'):
           if 'replication command' in str1:
              answer += str1 + '\n'
        if len(answer) == 17:
           answer = 'События репликации не обнаружены'
        for x in range(0, len(answer), 4096):
          update.message.reply_text(answer[x:x+4096])
    except (Exception, Error) as error:
        update.message.reply_text(f"Ошибка при работе с PostgreSQL: {error}")
        return 'get_repl_logs'

    return ConversationHandler

def get_emails(update, context):
    
    connection = None
    try:
        
        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Emails;")
        data = cursor.fetchall()
        message = '\n'.join([str(row) for row in data])
        update.message.reply_text(message)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def get_phone_numbers(update, context):
    
    connection = None
    try:
        
        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM PhoneNumbers;")
        data = cursor.fetchall()
        message = '\n'.join([str(row) for row in data])
        update.message.reply_text(message)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler_find_phone_numbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            FIND_PHONE_NUMBERS: [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            SAVE_PHONE_NUMBERS: [MessageHandler(Filters.text & ~Filters.command, savePhoneNumbers)]
        },
        fallbacks=[]
    )
    conv_handler_find_emails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            FIND_EMAIL: [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            SAVE_EMAILS: [MessageHandler(Filters.text & ~Filters.command, saveEmails)]
        },
        fallbacks=[]
    )
    conv_handler_verify_password = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_password_command)],
        states={
            PASSWORD_ENTER: [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[],
    )


    conv_handler_get_apt_list = ConversationHandler(
            entry_points=[CommandHandler('get_apt_list', get_apt_list)],
            states={
                APT_LIST_ACTION: [MessageHandler(Filters.text & ~Filters.command, apt_list_action)],
                APT_SEARCH_PACKAGE: [MessageHandler(Filters.text & ~Filters.command, apt_search_package)],
            },
            fallbacks=[],
        )



    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(conv_handler_find_emails)
    dp.add_handler(conv_handler_find_phone_numbers)
    dp.add_handler(conv_handler_verify_password) 
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_release", get_releases))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(conv_handler_get_apt_list)
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
