import telebot
from telebot import types
from telebot.util import update_types
import sqlite3

def open_db():
    global db_connector, db_cursor
    db_connector = sqlite3.connect('referrals.db')
    db_cursor = db_connector.cursor()

def close_db():
    db_cursor.close()
    db_connector.close()


open_db()
db_cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (id INTEGER PRIMARY KEY, user INTEGER, reffer TEXT, chanel TEXT, use INTEGER)''')
db_cursor.execute('''CREATE TABLE IF NOT EXISTS referral_chanels (id INTEGER PRIMARY KEY, name TEXT, url TEXT, plan INTEGER)''')

db_connector.commit()
close_db()

space_traffic_bot = telebot.TeleBot('7396330399:AAHrbIcBdmI8yoJSd9hNX5baqqWq8KZyMvc')
space_traffic_bot_users = {}

def clear_messages(message_type, chat_id):
    for delete_message_id in space_traffic_bot_users[chat_id]["messages"][message_type]:
        space_traffic_bot.delete_message(chat_id, delete_message_id)
        space_traffic_bot_users[chat_id]["messages"][message_type]=[]

def add_message(message_type, message):
    space_traffic_bot_users[message.chat.id]["messages"][message_type].append(message.message_id)

@space_traffic_bot.chat_member_handler()
def handle_new_member(message):
    if message.new_chat_member.status == 'member' and message.invite_link!=None:
        referral_id = message.invite_link.invite_link
        open_db()
        db_cursor.execute(f"SELECT use FROM referrals WHERE reffer='{referral_id}'")
        use=db_cursor.fetchone()[0]+1

        db_cursor.execute(f"UPDATE referrals SET use={use} WHERE reffer='{referral_id}'")
        db_connector.commit()

        db_cursor.execute(f"SELECT url, name, plan FROM referral_chanels")
        chanels = {chanel_url: (chanel_name, chanel_plan) for chanel_url, chanel_name, chanel_plan in db_cursor.fetchall()}

        db_cursor.execute(f"SELECT user, reffer, chanel, use FROM referrals ORDER BY chanel ASC, user ASC, id ASC")
        statistic = db_cursor.fetchall()
        close_db()

        startistic_text = '📈Ссылка : Пришло : Осталось📉'
        for chanel_url, chanel_info in chanels.items():
            chanel_name, chanel_plan=chanel_info
            sorted_reffer_link = [(referral_link, use) for user, referral_link, chanel, use in statistic if chanel == chanel_url]
            if sorted_reffer_link != []:
                startistic_text += f'\n\n📍{chanel_name}:'
                for reffer_user in list(set(map(lambda stat:stat[0], statistic))):
                    sorted_reffer_link = [(referral_link, use) for user, referral_link, chanel, use in statistic if chanel == chanel_url and reffer_user==user]
                    
                    startistic_text += f'\n\n🔹{reffer_user}:'

                    for referral_link, use in sorted_reffer_link:
                        startistic_text += f'\n\n    🔸{referral_link} : {use} : {chanel_plan-use}'

        for UserId, InfoUser in space_traffic_bot_users.items():
            if InfoUser["static_id"] != None:
                try:
                    message=space_traffic_bot.edit_message_text(UserId, f'Статистика:\n\n{startistic_text}', message_id=InfoUser["static_id"])
                except:
                    pass

@space_traffic_bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.id not in space_traffic_bot_users: space_traffic_bot_users[message.chat.id]={"read_message":"none", "messages":{"start":[], "menu":[], "admin":[]}, "static_id":None}

    clear_messages('start', message.chat.id)
    add_message('start', message)

    message=space_traffic_bot.send_message(message.chat.id, 'Привет ✌️! Я бот для арбитража трафика.\n\nИспользуйте команду /menu для отображения меню 📕.')

    add_message('start', message)


@space_traffic_bot.message_handler(commands=['menu'])
def open_menu(message):
    
    if message.chat.id not in space_traffic_bot_users: space_traffic_bot_users[message.chat.id]={"read_message":"none", "messages":{"start":[], "menu":[], "admin":[]}, "static_id":None}

    clear_messages('menu', message.chat.id)
    add_message('menu', message)


    menu_buttons = types.InlineKeyboardMarkup()
    menu_buttons.add(types.InlineKeyboardButton("Генерация ссылки", callback_data=f"generate_link"))
    menu_buttons.add(types.InlineKeyboardButton("Статистика", callback_data=f"statistic"))
    if message.chat.username in ["dmitrokds", "spaceetraffic"]: menu_buttons.add(types.InlineKeyboardButton("Admin", callback_data=f"adminRsp1"))

    message=space_traffic_bot.send_message(message.chat.id, '📙 Тут выберите команду из меню:', reply_markup=menu_buttons)

    add_message('menu', message)


@space_traffic_bot.callback_query_handler(func=lambda callback_message: "generate_link" in callback_message.data)
def generate_link_menu(callback_message):
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["menu"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)

    generate_link_menu_buttons = types.InlineKeyboardMarkup()
    open_db()
    db_cursor.execute(f"SELECT name, url FROM referral_chanels")
    chanels = db_cursor.fetchall()
    close_db()
    for chanel_name, chanel_url in chanels:
        generate_link_menu_buttons.add(types.InlineKeyboardButton(f"{chanel_name}", callback_data=f"{chanel_url}link_generate_chanel"))

    message=space_traffic_bot.send_message(message.chat.id, 'Выберите канал для генерации ссылки:', reply_markup=generate_link_menu_buttons)

    add_message('menu', message)
    
@space_traffic_bot.callback_query_handler(func=lambda callback_message: "link_generate_chanel" in callback_message.data)
def generate_link_menu(callback_message):
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["menu"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)

    chanel = callback_message.data.replace('link_generate_chanel', '')

    open_db()
    db_cursor.execute(f"SELECT MAX(Id) FROM referrals")
    referral_id=db_cursor.fetchone()[0]
    referral_id=referral_id+1 if referral_id!=None else 0
    referral_link = space_traffic_bot.create_chat_invite_link(chat_id=chanel, name=f"{referral_id}", creates_join_request=True).invite_link

    db_cursor.execute(f"SELECT name FROM referral_chanels WHERE url='{chanel}'")
    channel_name=db_cursor.fetchone()[0]

    db_cursor.execute(f"INSERT INTO referrals VALUES ({referral_id}, '{message.chat.id}', '{referral_link}', '{chanel}', 0)")
    db_connector.commit()
    close_db()

    message=space_traffic_bot.send_message(message.chat.id, f'Ваша уникальная ссылка для {channel_name}:\n\n{referral_link}') 


@space_traffic_bot.callback_query_handler(func=lambda callback_message: "statistic" in callback_message.data)
def generate_link_menu(callback_message):
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["menu"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)

    open_db()
    db_cursor.execute(f"SELECT url, name, plan FROM referral_chanels")
    chanels = {chanel_url: (chanel_name, chanel_plan) for chanel_url, chanel_name, chanel_plan in db_cursor.fetchall()}

    db_cursor.execute(f"SELECT reffer, chanel, use FROM referrals WHERE user='{message.chat.id}' ORDER BY chanel ASC, id ASC")
    statistic = db_cursor.fetchall()
    close_db()

    startistic_text = '📈Ссылка : Пришло : Осталось📉'
    for chanel_url, chanel_info in chanels.items():
        chanel_name, chanel_plan=chanel_info
        sorted_reffer_link = [(referral_link, use) for referral_link, chanel, use in statistic if chanel == chanel_url]
        
        if sorted_reffer_link != []:
            startistic_text += f'\n\n📍{chanel_name}:'
            for referral_link, use in sorted_reffer_link:
                startistic_text += f'\n\n    🔸{referral_link} : {use} : {chanel_plan-use}'
            


    message=space_traffic_bot.send_message(message.chat.id, f'Статистика юзера {message.chat.first_name}:\n\n{startistic_text}')

    add_message('menu', message)

@space_traffic_bot.message_handler(commands=['adminRsp1'])
def admin_panel(message):
    
    if message.chat.id not in space_traffic_bot_users: space_traffic_bot_users[message.chat.id]={"read_message":"none", "messages":{"start":[], "menu":[], "admin":[]}, "static_id":None}

    add_message('admin', message)
    clear_messages('admin', message.chat.id)

    admin_buttons = types.InlineKeyboardMarkup()
    admin_buttons.add(types.InlineKeyboardButton("Статистика", callback_data=f"admin_stat"))
    admin_buttons.add(types.InlineKeyboardButton("Добавить канал", callback_data=f"add_chanel"))
    admin_buttons.add(types.InlineKeyboardButton("Удалить канал", callback_data=f"delete_chanel"))
    admin_buttons.add(types.InlineKeyboardButton("Изменить план", callback_data=f"edit_plan"))

    message=space_traffic_bot.send_message(message.chat.id, 'Это админ панель. Выбери команду:', reply_markup=admin_buttons)

    add_message('admin', message)


@space_traffic_bot.callback_query_handler(func=lambda callback_message: "adminRsp1" in callback_message.data)
def admin_panel_button(callback_message):
    message=callback_message.message
    clear_messages('admin', message.chat.id)

    admin_buttons = types.InlineKeyboardMarkup()
    admin_buttons.add(types.InlineKeyboardButton("Статистика", callback_data=f"admin_stat"))
    admin_buttons.add(types.InlineKeyboardButton("Добавить канал", callback_data=f"add_chanel"))
    admin_buttons.add(types.InlineKeyboardButton("Удалить канал", callback_data=f"delete_chanel"))
    admin_buttons.add(types.InlineKeyboardButton("Изменить план", callback_data=f"edit_plan"))

    message=space_traffic_bot.send_message(message.chat.id, 'Это админ панель. Выбери команду:', reply_markup=admin_buttons)

    add_message('admin', message)

@space_traffic_bot.callback_query_handler(func=lambda callback_message: "admin_stat" in callback_message.data)
def admin_stat(callback_message):
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["admin"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)

    open_db()
    db_cursor.execute(f"SELECT url, name, plan FROM referral_chanels")
    chanels = {chanel_url: (chanel_name, chanel_plan) for chanel_url, chanel_name, chanel_plan in db_cursor.fetchall()}

    db_cursor.execute(f"SELECT user, reffer, chanel, use FROM referrals ORDER BY chanel ASC, user ASC, id ASC")
    statistic = db_cursor.fetchall()
    close_db()

    startistic_text = '📈Ссылка : Пришло : Осталось📉'
    for chanel_url, chanel_info in chanels.items():
        chanel_name, chanel_plan=chanel_info
        sorted_reffer_link = [(referral_link, use) for user, referral_link, chanel, use in statistic if chanel == chanel_url]
        if sorted_reffer_link != []:
            startistic_text += f'\n\n📍{chanel_name}:'
            for reffer_user in list(set(map(lambda stat:stat[0], statistic))):
                sorted_reffer_link = [(referral_link, use) for user, referral_link, chanel, use in statistic if chanel == chanel_url and reffer_user==user]
                
                startistic_text += f'\n\n🔹{reffer_user}:'

                for referral_link, use in sorted_reffer_link:
                    startistic_text += f'\n\n    🔸{referral_link} : {use} : {chanel_plan-use}'

    message=space_traffic_bot.send_message(message.chat.id, f'Статистика:\n\n{startistic_text}')
    if space_traffic_bot_users[message.chat.id]["static_id"]!=None:
        space_traffic_bot.delete_message(message.chat.id, space_traffic_bot_users[message.chat.id]["static_id"])

    space_traffic_bot_users[message.chat.id]["static_id"]=message.message_id

@space_traffic_bot.callback_query_handler(func=lambda callback_message: "add_chanel" in callback_message.data)
def add_chanel(callback_message):
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["admin"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)

    message=space_traffic_bot.send_message(message.chat.id, f'Напиши название канала:')
    space_traffic_bot_users[message.chat.id]["read_message"]="chanel_name"

    add_message('admin', message)

@space_traffic_bot.callback_query_handler(func=lambda callback_message: "edit_plan" in callback_message.data)
def edit_plan(callback_message):
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["admin"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)
    open_db()
    db_cursor.execute(f"SELECT name, url FROM referral_chanels")
    chanels = db_cursor.fetchall()
    close_db()
    
    chanel_buttons = types.InlineKeyboardMarkup()
    for chanel_name, chanel_url in chanels:
        chanel_buttons.add(types.InlineKeyboardButton(chanel_name, callback_data=f"edit_chanel_plan{chanel_url}"))

    message=space_traffic_bot.send_message(message.chat.id, f'Выбери канал:', reply_markup=chanel_buttons)

    add_message('admin', message)

@space_traffic_bot.callback_query_handler(func=lambda callback_message: "edit_chanel_plan" in callback_message.data)
def edit_chanel_plan(callback_message):
    global edit_chanel
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["admin"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)

    edit_chanel=callback_message.data.replace('edit_chanel_plan', '')

    message=space_traffic_bot.send_message(message.chat.id, f'Напиши новий план:')
    space_traffic_bot_users[message.chat.id]["read_message"]="edit_plan"

    add_message('admin', message)


@space_traffic_bot.callback_query_handler(func=lambda callback_message: "delete_chanel" in callback_message.data)
def delete_chanel(callback_message):
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["admin"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)
    open_db()
    db_cursor.execute(f"SELECT name, url FROM referral_chanels")
    chanels = db_cursor.fetchall()
    close_db()
    
    chanel_buttons = types.InlineKeyboardMarkup()
    for chanel_name, chanel_url in chanels:
        chanel_buttons.add(types.InlineKeyboardButton(chanel_name, callback_data=f"delete_name_chanel{chanel_url}"))

    message=space_traffic_bot.send_message(message.chat.id, f'Выбери канал:', reply_markup=chanel_buttons)

    add_message('admin', message)

@space_traffic_bot.callback_query_handler(func=lambda callback_message: "delete_name_chanel" in callback_message.data)
def delete_chanel_from_db(callback_message):
    global edit_chanel
    message=callback_message.message
    space_traffic_bot_users[message.chat.id]["messages"]["admin"].remove(message.message_id)
    space_traffic_bot.delete_message(message.chat.id, message.message_id)

    delete_name_chanel=callback_message.data.replace('delete_name_chanel', '')
    open_db()
    db_cursor.execute(f"SELECT name FROM referral_chanels WHERE url='{delete_name_chanel}'")
    delete_name_chanel = db_cursor.fetchone()[0]

    db_cursor.execute(f"DELETE FROM referral_chanels WHERE url='{delete_name_chanel}'")
    db_connector.commit()
    close_db()

    message=space_traffic_bot.send_message(message.chat.id, f'Канал {delete_name_chanel} удален')


@space_traffic_bot.message_handler(content_types=['text'])
def GetText(message):
    global chanel_name, chanel_url
    if message.chat.id not in space_traffic_bot_users:
        space_traffic_bot.delete_message(message.chat.id, message.message_id)
    elif space_traffic_bot_users[message.chat.id]["read_message"]=='chanel_name':
        chanel_name=message.text
        add_message('admin', message)

        message=space_traffic_bot.send_message(message.chat.id, f'Напиши url канала (@chanel):')
        space_traffic_bot_users[message.chat.id]["read_message"]="chanel_url"

        add_message('admin', message)
    elif space_traffic_bot_users[message.chat.id]["read_message"]=='chanel_url':
        chanel_url=message.text
        add_message('admin', message)
        try:
            space_traffic_bot.create_chat_invite_link(chat_id=chanel_url, name=f"123456789")
        except:
            message=space_traffic_bot.send_message(message.chat.id, f'Url неправильное или в канал не добаавлен бот.\n\nНапиши url канала (@chanel):')
            space_traffic_bot_users[message.chat.id]["read_message"]="chanel_url"

            add_message('admin', message)
            return True

        message=space_traffic_bot.send_message(message.chat.id, f'Напиши план канала:')
        space_traffic_bot_users[message.chat.id]["read_message"]="chanel_plan"

        add_message('admin', message)
    elif space_traffic_bot_users[message.chat.id]["read_message"]=='chanel_plan':
        chanel_plan=message.text
        add_message('admin', message)
        try:
            int(chanel_plan)
            if int(chanel_plan)<1:
                raise ValueError
        except:
            message=space_traffic_bot.send_message(message.chat.id, f'План канала должен быть числом.\n\nНапиши план канала:')
            space_traffic_bot_users[message.chat.id]["read_message"]="chanel_url"

            add_message('admin', message)
            return True


        open_db()
        db_cursor.execute(f"SELECT id FROM referral_chanels WHERE url='{chanel_url}'")
        if len(db_cursor.fetchall())>0:
            message=space_traffic_bot.send_message(message.chat.id, f'Такой канал уже есть:')
            add_message('admin', message)
            close_db()
            return True

        db_cursor.execute(f"SELECT MAX(Id) FROM referral_chanels")
        referral_chanel_id=db_cursor.fetchone()[0]
        referral_chanel_id=referral_chanel_id+1 if referral_chanel_id!=None else 0
        db_cursor.execute(f"INSERT INTO referral_chanels VALUES ({referral_chanel_id}, '{chanel_name}', '{chanel_url}', {chanel_plan})")
        db_connector.commit()
        close_db()

        message=space_traffic_bot.send_message(message.chat.id, f'Создан реферальний канал:\n\n{chanel_name} - {chanel_url} - {chanel_plan}')
        space_traffic_bot_users[message.chat.id]["read_message"]="none"
    elif space_traffic_bot_users[message.chat.id]["read_message"]=='edit_plan':
        chanel_plan=message.text
        add_message('admin', message)
        try:
            int(chanel_plan)
            if int(chanel_plan)<1:
                raise ValueError
        except:
            message=space_traffic_bot.send_message(message.chat.id, f'План канала должен быть числом.\n\nНапиши план канала:')
            space_traffic_bot_users[message.chat.id]["read_message"]="edit_plan"

            add_message('admin', message)
            return True


        open_db()
        db_cursor.execute(f"UPDATE referral_chanels SET plan={chanel_plan} WHERE url='{edit_chanel}'")
        db_connector.commit()
        close_db()

        message=space_traffic_bot.send_message(message.chat.id, f'Оновлен план канал:\n\n{edit_chanel} - {chanel_plan}')
        space_traffic_bot_users[message.chat.id]["read_message"]="none"
    elif message.chat.type == "private":
        space_traffic_bot.delete_message(message.chat.id, message.message_id)


      
space_traffic_bot.infinity_polling(none_stop=True, interval=0, allowed_updates=update_types)