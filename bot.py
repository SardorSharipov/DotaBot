import math
import random
import sqlite3
import logging
import traceback
import time

import telebot
from telebot.async_telebot import AsyncTeleBot
import phrases
import command_handler
from data.db_add import db_add_all, give_open_bonus
from data.db_init import initialize_db

logger = telebot.logger
telebot.logger.setLevel(logging.ERROR)  # Outputs debug messages to console.


class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception: Exception):
        logger.error(exception)
        print(traceback.format_exc())


connect = sqlite3.connect('game.db', check_same_thread=False)
cursor = connect.cursor()

TOKEN = '5852417103:AAFen2MdFQ9qdVyrVofwGsRoRyADt29zvgM'
bot = AsyncTeleBot(TOKEN, exception_handler=ExceptionHandler())


@bot.message_handler(commands=["help"])
async def help_command(message: telebot.types.Message):
    await bot.send_message(chat_id=message.chat.id,
                           text=phrases.HELP_MESSAGE,
                           parse_mode='Markdown')


@bot.message_handler(commands=["start"])
async def start(message: telebot.types.Message):
    cursor.executescript(
        f"""
        DELETE FROM heroes WHERE hero_id = {message.chat.id};
        DELETE FROM hero_x_item where hero_id = {message.chat.id};
        """)
    connect.commit()
    cursor.execute("""
        INSERT INTO heroes (hero_id, nickname, location_id) VALUES (?, ?, ?)
        """, [message.chat.id, message.from_user.username, 2])
    connect.commit()
    give_open_bonus(message)
    await bot.send_message(chat_id=message.chat.id,
                           text=phrases.HELP_MESSAGE,
                           parse_mode='Markdown')


@bot.message_handler(commands=["stats"])
async def stats_player(message: telebot.types.Message):
    cursor.execute(f"""
        SELECT 
            nickname, 
            level, 
            hp, 
            current_hp, 
            money, 
            attack, 
            magick_attack, 
            xp, 
            armour, 
            magic_armour,
            location_id 
        FROM heroes 
        WHERE hero_id = {message.chat.id}
        """)
    hero_info = list(cursor.fetchall()[0])
    cursor.execute(f'SELECT location_name, description FROM locations WHERE location_id = {hero_info[-1]}')
    location_info = list(cursor.fetchall()[0])
    await bot.send_message(chat_id=message.chat.id,
                           text=command_handler.stats_player_txt(hero_info, location_info),
                           parse_mode='Markdown')


@bot.message_handler(commands=["locations"])
async def stats_locations(message: telebot.types.Message):
    await bot.send_message(chat_id=message.chat.id,
                           text=command_handler.stats_location_txt(cursor),
                           parse_mode='Markdown')


@bot.message_handler(commands=["inventory"])
async def inventory(message: telebot.types.Message):
    await bot.send_message(chat_id=message.chat.id,
                           text=command_handler.stats_inventory_txt(cursor, message),
                           parse_mode='Markdown')


@bot.message_handler(commands=["put_on"])
async def put_on(message: telebot.types.Message):
    cursor.execute(
        f"""
        SELECT
            locations.location_cd
        FROM
            heroes
            INNER JOIN locations
            ON heroes.location_id = locations.location_id
        """
    )
    location_cd = cursor.fetchall()[0][0]
    if location_cd == "подземелье":
        await bot.send_message(chat_id=message.chat.id,
                               text=phrases.FORBIDDEN_TEXT,
                               parse_mode='Markdown')
    else:
        cursor.execute(
            f"""
            SELECT
                i.item_id,
                item_type,
                item_name
            FROM hero_x_item
                INNER JOIN items i on hero_x_item.item_id = i.item_id
            WHERE hero_id = {message.chat.id} AND status_cd = 0                
            """
        )
        user_items = list(cursor.fetchall())
        if len(user_items) == 0:
            await bot.send_message(chat_id=message.chat.id,
                                   text=phrases.EMPTY_INVENTORY_TEXT + " " + phrases.OR_ALL_ITEMS_ARE_USED_TEXT,
                                   parse_mode='Markdown')
        else:
            markup = telebot.types.InlineKeyboardMarkup(row_width=4)
            can_put_on = False
            for item in user_items:
                if item[1] == 'potion':
                    continue
                can_put_on = True
                item = telebot.types.InlineKeyboardButton(f"{item[2]}", callback_data=f"use_{item[0]}")
                markup.row(item)
            if not can_put_on:
                await bot.send_message(chat_id=message.chat.id,
                                       text=phrases.NO_GARMENTS_TEXT + " " + phrases.OR_ALL_ITEMS_ARE_USED_TEXT,
                                       parse_mode='Markdown')
            else:
                await bot.send_message(chat_id=message.chat.id,
                                       text=command_handler.stats_inventory_txt(cursor,
                                                                                message) + " " +
                                            phrases.CHOOSE_ITEM_TO_USE_TEXT,
                                       parse_mode='Markdown', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
async def use_item(call: telebot.types.CallbackQuery):
    item_id = call.data.replace('use_', '')
    await bot.send_message(chat_id=call.message.chat.id,
                           text=command_handler.use_item(item_id, cursor, connect, call.message),
                           parse_mode='Markdown')


@bot.message_handler(commands=["take_off"])
async def take_off(message: telebot.types.Message):
    cursor.execute(
        f"""
        SELECT
            locations.location_cd
        FROM
            heroes
            INNER JOIN locations
            ON heroes.location_id = locations.location_id
        """
    )
    location_cd = cursor.fetchall()[0][0]
    if location_cd == "подземелье":
        await bot.send_message(chat_id=message.chat.id,
                               text=phrases.FORBIDDEN_TEXT,
                               parse_mode='Markdown')
    else:
        cursor.execute(
            f"""
            SELECT
                i.item_id,
                item_type,
                item_name
            FROM hero_x_item
                INNER JOIN items i on hero_x_item.item_id = i.item_id
            WHERE hero_id = {message.chat.id} AND status_cd = 1 AND item_type != 'зелье'               
            """
        )
        user_items = list(cursor.fetchall())
        if len(user_items) == 0:
            await bot.send_message(chat_id=message.chat.id,
                                   text=phrases.EMPTY_INVENTORY_TEXT + " " + phrases.OR_ALL_ITEMS_ARE_USED_TEXT,
                                   parse_mode='Markdown')
        else:
            markup = telebot.types.InlineKeyboardMarkup(row_width=4)
            can_put_on = False
            for item in user_items:
                if item[1] == 'potion':
                    continue
                can_put_on = True
                item = telebot.types.InlineKeyboardButton(f"{item[2]}", callback_data=f"take_off_{item[0]}")
                markup.row(item)
            if not can_put_on:
                await bot.send_message(chat_id=message.chat.id,
                                       text=phrases.NO_GARMENTS_TEXT + " " + phrases.OR_ALL_ITEMS_ARE_USED_TEXT,
                                       parse_mode='Markdown')
            else:
                await bot.send_message(chat_id=message.chat.id,
                                       text=command_handler.stats_inventory_txt(cursor,
                                                                                message) + " " +
                                            phrases.CHOOSE_ITEM_TO_TAKE_OFF_TEXT,
                                       parse_mode='Markdown', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("take_off_"))
async def take_off_item(call: telebot.types.CallbackQuery):
    item_id = call.data.replace('take_off_', '')
    await bot.send_message(chat_id=call.message.chat.id,
                           text=command_handler.take_off_item(item_id, cursor, connect, call.message),
                           parse_mode='Markdown')


@bot.message_handler(commands=["items"])
async def items(message: telebot.types.Message):
    cursor.execute(
        f"""
        SELECT
            location_name,
            location_cd
        FROM heroes
            INNER JOIN locations l on heroes.location_id = l.location_id
    """)
    location_name, location_type = cursor.fetchall()[0]
    if location_type == "подземелье":
        await bot.send_message(chat_id=message.chat.id,
                               text=phrases.FORBIDDEN_TEXT,
                               parse_mode='Markdown')

    elif location_name == 'потайная лавка' or location_name == 'база':
        if location_name == 'база':
            code = 'base'
        else:
            code = 'hidden'
        markup = telebot.types.InlineKeyboardMarkup(row_width=4)
        item = telebot.types.InlineKeyboardButton(phrases.BUY_TEXT, callback_data=f"buy_item_{code}")
        markup.row(item)
        item = telebot.types.InlineKeyboardButton(phrases.SELL_TEXT, callback_data=f"sell_item_{code}")
        markup.row(item)
        await bot.send_message(chat_id=message.chat.id,
                               text=command_handler.create_items_text(cursor, message),
                               parse_mode='Markdown',
                               reply_markup=markup)
    #


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_item_base"))
async def buy_item_base(call: telebot.types.CallbackQuery):
    cursor.execute(
        f"""
        SELECT
            item_name,
            i.item_id
        FROM item_x_location
            INNER JOIN locations l on item_x_location.location_id = l.location_id
            INNER JOIN items i on item_x_location.item_id = i.item_id
        WHERE l.location_name = 'база'
        """)
    selected_items = cursor.fetchall()
    markup = telebot.types.InlineKeyboardMarkup()
    for selected_item in selected_items:
        item = telebot.types.InlineKeyboardButton(f"{selected_item[0]}", callback_data=f"buy_{selected_item[-1]}")
        markup.row(item)
    await bot.send_message(chat_id=call.message.chat.id,
                           text=command_handler.create_items_text(cursor,
                                                                  call.message) + "\n" +
                                phrases.CHOOSE_ITEM_TO_BUY_TEXT,
                           parse_mode='Markdown',
                           reply_markup=markup)


@bot.callback_query_handler(func=lambda call: str(call.data).startswith("sell_item_base"))
async def sell_item_base(call: telebot.types.CallbackQuery):
    cursor.execute(
        f"""
            SELECT
                item_name,
                i.item_id
            FROM item_x_location
                INNER JOIN locations l on item_x_location.location_id = l.location_id
                INNER JOIN items i on item_x_location.item_id = i.item_id
            WHERE l.location_name = 'база'
            """)
    selected_items = cursor.fetchall()
    markup = telebot.types.InlineKeyboardMarkup()
    for selected_item in selected_items:
        item = telebot.types.InlineKeyboardButton(f"{selected_item[0]}", callback_data=f"buy_{selected_item[-1]}")
        markup.row(item)
    await bot.send_message(chat_id=call.message.chat.id,
                           text=command_handler.create_items_text(cursor,
                                                                  call.message) + "\n" +
                                phrases.CHOOSE_ITEM_TO_SELL_TEXT,
                           parse_mode='Markdown',
                           reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_item_hidden"))
async def buy_item_hidden(call: telebot.types.CallbackQuery):
    cursor.execute(
        f"""
            SELECT
                item_name,
                i.item_id
            FROM item_x_location
                INNER JOIN locations l on item_x_location.location_id = l.location_id
                INNER JOIN items i on item_x_location.item_id = i.item_id
            WHERE l.location_name = 'потайная лавка'
            """)
    selected_items = cursor.fetchall()
    markup = telebot.types.InlineKeyboardMarkup()
    for selected_item in selected_items:
        item = telebot.types.InlineKeyboardButton(f"{selected_item[0]}", callback_data=f"buy_{selected_item[-1]}")
        markup.row(item)
    await bot.send_message(chat_id=call.message.chat.id,
                           text=command_handler.create_items_text(cursor,
                                                                  call.message) + "\n" +
                                phrases.CHOOSE_ITEM_TO_BUY_TEXT,
                           parse_mode='Markdown',
                           reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("sell_item_hidden"))
async def buy_item_hidden(call: telebot.types.CallbackQuery):
    cursor.execute(
        f"""
            SELECT
                item_name,
                i.item_id
            FROM item_x_location
                INNER JOIN locations l on item_x_location.location_id = l.location_id
                INNER JOIN items i on item_x_location.item_id = i.item_id
            WHERE l.location_name = 'потайная лавка'
            """)
    selected_items = cursor.fetchall()
    markup = telebot.types.InlineKeyboardMarkup()
    for selected_item in selected_items:
        item = telebot.types.InlineKeyboardButton(f"{selected_item[0]}", callback_data=f"buy_{selected_item[-1]}")
        markup.row(item)
    await bot.send_message(chat_id=call.message.chat.id,
                           text=command_handler.create_items_text(cursor,
                                                                  call.message) + "\n" +
                                phrases.CHOOSE_ITEM_TO_SELL_TEXT,
                           parse_mode='Markdown',
                           reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
async def buy_item(call: telebot.types.CallbackQuery):
    item_id = call.data.replace('buy_', '')
    await bot.send_message(chat_id=call.message.chat.id,
                           text=command_handler.buy_item(item_id, cursor, connect, call.message),
                           parse_mode='Markdown')


@bot.callback_query_handler(func=lambda call: call.data.startswith("sell_"))
async def sell_item(call: telebot.types.CallbackQuery):
    item_id = call.data.replace('sell_', '')
    await bot.send_message(chat_id=call.message.chat.id,
                           text=command_handler.sell_item(item_id, cursor, connect, call.message),
                           parse_mode='Markdown')


@bot.message_handler(commands=["move"])
async def move(message: telebot.types.Message):
    cursor.execute(
        f"""
        SELECT
            l.location_id,
            location_name,
            location_cd
        FROM heroes
            INNER JOIN locations l on heroes.location_id = l.location_id
        WHERE hero_id = {message.chat.id}
        """
    )
    location_id, location_name, location_type = cursor.fetchall()[0]
    if location_type == "подземелье":
        await bot.reply_to(message, text=phrases.FORBIDDEN_TEXT)
    else:
        cursor.execute(
            f"""
            SELECT
                locations.location_id,
                other_location.location_id,
                locations.location_name,
                other_location.location_name,
                round(
                (locations.x_coord - other_location.x_coord) * (locations.x_coord - other_location.x_coord) + 
                (locations.y_coord - other_location.y_coord) * (locations.y_coord - other_location.y_coord)
                ) AS distance 
            FROM locations
                INNER JOIN locations other_location
                    ON other_location.location_id != locations.location_id
                    AND locations.location_id = {location_id}                
            """
        )
        to = cursor.fetchall()
        markup = telebot.types.InlineKeyboardMarkup(row_width=4)
        for location in to:
            item = telebot.types.InlineKeyboardButton(f"{location[-2]}", callback_data=f"move_to_{location[1]}")
            markup.row(item)
        await bot.reply_to(message, text="В какой город отправляемся?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("move_to_"))
async def move_to_callback(call: telebot.types.CallbackQuery):
    location_id_other = int(call.data.replace('move_to_', ''))

    cursor.execute(
        f"""
                SELECT
                    other_location.location_id,
                    other_location.location_cd,
                    other_location.location_name,
                    round(
                (locations.x_coord - other_location.x_coord) * (locations.x_coord - other_location.x_coord) + 
                (locations.y_coord - other_location.y_coord) * (locations.y_coord - other_location.y_coord)
                ) AS distance 
                FROM locations
                    INNER JOIN locations other_location
                        ON other_location.location_id != locations.location_id
                        AND other_location.location_id = {location_id_other}
                    INNER JOIN heroes h on locations.location_id = h.location_id                
                """
    )

    location_id, location_cd, location_name, duration = list(cursor.fetchall()[0])
    print(duration)
    duration = int(math.sqrt(duration))
    await bot.reply_to(call.message, text=phrases.create_duration_text(location_name, duration))
    await bot.reply_to(call.message, text=str(duration))
    for i in range(duration - 1, -1, -1):
        time.sleep(1)
        await bot.reply_to(call.message, text=str(i))
    cursor.execute(f'SELECT hp, current_hp FROM heroes WHERE hero_id = {call.message.chat.id}')
    max_hp, cur_hp = cursor.fetchall()[0]
    if location_cd == 'город':
        cursor.execute(f'UPDATE heroes SET location_id = {location_id}, current_hp = {max(max_hp, cur_hp)} '
                       f'WHERE hero_id = {call.message.chat.id}')
        connect.commit()
        if location_name == 'база':
            await bot.reply_to(call.message, text=phrases.BASE_ARRIVAL_TEXT)
        else:
            await bot.reply_to(call.message, text=phrases.HIDDEN_ARRIVAL_TEXT)
    else:
        cursor.execute(f'UPDATE heroes SET location_id = {location_id} '
                       f'WHERE hero_id = {call.message.chat.id}')
        connect.commit()
        cursor.execute(
            f"""
            SELECT
                mobs.mob_id
            FROM mobs
                INNER JOIN heroes h 
                    ON mobs.req_level <= h.level
                    AND mobs.req_level >= 
                        CASE 
                            WHEN {location_id} = 4
                                THEN 1
                        ELSE
                            6
                        END
                    AND mobs.req_level <= 
                        CASE 
                            WHEN {location_id} = 4
                                THEN 5
                        ELSE
                            20
                        END  
                    AND hero_id = {call.message.chat.id}                    
            """
        )
        all_req_mobs = list(cursor.fetchall())
        if not all_req_mobs:
            cursor.execute(f'UPDATE heroes SET location_id = 2 '
                           f'WHERE hero_id = {call.message.chat.id}')
            connect.commit()
            await bot.reply_to(call.message, text='Недостаточно левела, вы на базе')
            return
        if location_name == 'лес':
            await bot.reply_to(call.message, text=phrases.WOOD_ARRIVAL_TEXT)
        else:
            await bot.reply_to(call.message, text=phrases.ROSHAN_ARRIVAL_TEXT)
        mob_id = all_req_mobs[random.randrange(0, len(all_req_mobs))]

        cursor.execute(f'SELECT hp FROM mobs WHERE mob_id = {mob_id[0]}')
        mob_hp = cursor.fetchall()[0][0]
        cursor.execute(f'UPDATE heroes SET mob_id = {mob_id[0]}, mob_hp = {mob_hp} '
                       f'WHERE hero_id = {call.message.chat.id}')
        await bot.reply_to(call.message, text=command_handler.create_bonuses_text(call.message, cursor))

        markup = telebot.types.InlineKeyboardMarkup(row_width=4)
        item = telebot.types.InlineKeyboardButton(phrases.GET_MOB_INFO_TEXT, callback_data=f"mob_info")
        markup.row(item)
        item = telebot.types.InlineKeyboardButton(phrases.DRINK_POTION_TEXT, callback_data=f"drink_potion")
        markup.row(item)
        item = telebot.types.InlineKeyboardButton(phrases.ATTACK_TEXT, callback_data=f"attack")
        markup.row(item)
        await bot.reply_to(call.message, text=phrases.TURN_TEXT, reply_markup=markup)


async def attack_mod(call: telebot.types.CallbackQuery):
    action_result = command_handler.attack_mob(call.message, cursor)
    if action_result == phrases.END_TEXT:
        await bot.reply_to(call.message, text=phrases.END_TEXT)
        cursor.executescript(
            f"""
                DELETE FROM heroes WHERE hero_id = {call.message.chat.id};
                DELETE FROM hero_x_item where hero_id = {call.message.chat.id};
                """)
        connect.commit()
        cursor.execute("""
                INSERT INTO heroes (hero_id, nickname) VALUES (?, ?)
                """, [call.message.chat.id, call.message.from_user.username])
        connect.commit()
        give_open_bonus(call.message)
        await bot.reply_to(call.message, text=phrases.HELLO_TEXT)
    else:
        await bot.reply_to(call.message, text=phrases.NEW_HP_TEXT + " " + str(action_result))
        markup = telebot.types.InlineKeyboardMarkup(row_width=4)
        item = telebot.types.InlineKeyboardButton(phrases.GET_MOB_INFO_TEXT, callback_data=f"mob_info")
        markup.row(item)
        item = telebot.types.InlineKeyboardButton(phrases.DRINK_POTION_TEXT, callback_data=f"drink_potion")
        markup.row(item)
        item = telebot.types.InlineKeyboardButton(phrases.ATTACK_TEXT, callback_data=f"attack")
        markup.row(item)
        await bot.reply_to(call.message, text=phrases.TURN_TEXT, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("mob_info"))
async def mob_info(call: telebot.types.CallbackQuery):
    await bot.reply_to(call.message, text=command_handler.create_mob_info_text(call.message, cursor))
    await attack_mod(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith("drink_potion"))
async def drink_potion(call: telebot.types.CallbackQuery):
    potions_text = command_handler.stats_inventory_txt(cursor, call.message)
    if potions_text == phrases.NO_POTION_TEXT or potions_text == phrases.EMPTY_INVENTORY_TEXT:
        await bot.reply_to(call.message, text=phrases.MISS_TURN_TEXT)
    else:
        await bot.reply_to(call.message, text=potions_text)
        cursor.execute(f"SELECT items.item_id, items.item_name  FROM hero_x_item "
                       f"INNER JOIN items ON items.item_id = hero_x_item.item_id "
                       f"WHERE status_cd = 1 AND hero_id = {call.message.chat.id}")
        active_items = cursor.fetchall()
        markup = telebot.types.InlineKeyboardMarkup(row_width=4)
        for item in active_items:
            cursor.execute(f"select item_type from items where item_id = {item[0]}")
            ItemType = cursor.fetchall()[0][0]
            if ItemType != 'зелье':
                continue
            item = telebot.types.InlineKeyboardButton(f"{item[1]}", callback_data=f"potion_{item[0]}")
            markup.row(item)
        await bot.reply_to(call.message, text=phrases.WHAT_POTION_TO_USE_TEXT, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("potion"))
async def potion(call: telebot.types.CallbackQuery):
    item_id = call.data.replace('potion_', '')
    await bot.reply_to(call.message, text=command_handler.drink_potion(item_id, cursor, connect, call.message))
    await attack_mod(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith("attack"))
async def attack(call: telebot.types.CallbackQuery):
    markup = telebot.types.InlineKeyboardMarkup(row_width=4)
    item = telebot.types.InlineKeyboardButton(f"физическая атака", callback_data=f"physical")
    markup.row(item)
    item = telebot.types.InlineKeyboardButton(f"магическая атака", callback_data=f"magical")
    markup.row(item)
    await bot.reply_to(call.message, text=phrases.CHOOSE_ATTACK_TYPE_TEXT, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("physical"))
async def physical(call: telebot.types.CallbackQuery):
    action_result = command_handler.attack_user(call.message, cursor, connect, "physical")
    if not action_result[0]:
        await bot.reply_to(call.message, text=phrases.MOB_REMAIN_HP_TEXT + " " + str(action_result[1]))
        await attack_mod(call)
    else:
        await bot.reply_to(call.message, text=phrases.WIN_TEXT)
        if action_result[1] > 0:
            await bot.reply_to(call.message, text=phrases.UPDATE_LEVEL_TEXT + " " + str(action_result[1]))
        await bot.reply_to(call.message, text="Получили предмет" + " " + str(action_result[-1]))
        await bot.reply_to(call.message, text=phrases.WIN_MONEY_TEXT + " " + str(action_result[3]))
        cursor.execute(f'SELECT hp, current_hp FROM heroes WHERE hero_id = {call.message.chat.id}')
        max_hp, cur_hp = cursor.fetchall()[0]
        cursor.execute(f'UPDATE heroes SET location_id  = 2, current_hp = {max(max_hp, cur_hp)} '
                       f'WHERE hero_id = {call.message.chat.id}')
        connect.commit()
        await bot.reply_to(call.message, text=phrases.BASE_ARRIVAL_TEXT)


@bot.callback_query_handler(func=lambda call: call.data.startswith("magical"))
async def magical(call: telebot.types.CallbackQuery):
    action_result = command_handler.attack_user(call.message, cursor, connect, "magical")
    if not action_result[0]:
        await bot.reply_to(call.message, text=phrases.MOB_REMAIN_HP_TEXT + " " + str(action_result[1]))
        await attack_mod(call)
    else:
        await bot.reply_to(call.message, text=phrases.WIN_TEXT)
        if action_result[1] > 0:
            await bot.reply_to(call.message, text=phrases.UPDATE_LEVEL_TEXT + " " + str(action_result[1]))
        await bot.reply_to(call.message, text="Получили предмет" + " " + str(action_result[-1]))
        await bot.reply_to(call.message, text=phrases.WIN_MONEY_TEXT + " " + str(action_result[3]))
        cursor.execute(f'select hp, current_hp FROM heroes WHERE hero_id = {call.message.chat.id}')
        max_hp, cur_hp = cursor.fetchall()[0]
        cursor.execute(f'UPDATE heroes SET location_id  = 2, current_hp = {max(max_hp, cur_hp)} '
                       f'WHERE hero_id = {call.message.chat.id}')
        connect.commit()
        await bot.reply_to(call.message, text=phrases.BASE_ARRIVAL_TEXT)


@bot.message_handler()
async def unknown_message(message: telebot.types.Message):
    await bot.send_message(chat_id=message.chat.id,
                           text=phrases.UNKNOWN_TEST,
                           parse_mode='Markdown')


async def main():
    initialize_db()
    db_add_all()
    await bot.polling(none_stop=True, interval=0)
