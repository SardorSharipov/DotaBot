import phrases
import random
import sqlite3


def stats_player_txt(hero_info, location_info):
    return f"""
Герой: *{hero_info[0]}*
Уровень: {hero_info[1]}
HP: {hero_info[2]}/ {hero_info[3]}
Золото: {hero_info[4]}
Физическая атака: {hero_info[5]}
Магическая атака: {hero_info[6]}
Опыт: {hero_info[7] + hero_info[1] * 100}/{(hero_info[1] + 1) * 100}
Броня: {hero_info[8]}
Магическое защита: {hero_info[9]}
Локация: {location_info[0]}
"""


def stats_location_txt(cursor):
    cursor.execute(f'SELECT location_name, location_cd, x_coord, y_coord, description FROM locations')
    locations = list(cursor.fetchall())
    joiner = ""
    for location in locations:
        cur_location_text = f"""
Название: *{location[0]}*
Тип: {location[1]}
Описание: {location[4]}
Местонахождение: ({location[2]}, {location[3]})
"""
        joiner += cur_location_text
    return joiner


def stats_inventory_txt(cursor, message):
    cursor.execute(f"""
    SELECT
       items.item_name,
       items.req_level,
       items.item_type,
       items.cost_to_sale,
       items.cost,
       items.magic_armour,
       items.armour,
       items.attack,
       items.magic_attack,
       hero_x_item.status_cd,
       items.mana,
       items.hp,
       hero_x_item.quantity
    FROM hero_x_item
        INNER JOIN items
            ON items.item_id = hero_x_item.item_id
    WHERE hero_id = {message.chat.id}
    """)
    hero_item = list(cursor.fetchall())
    if len(hero_item) == 0:
        return phrases.EMPTY_INVENTORY_TEXT
    text = "Инвентарь:\n"
    for item in hero_item:
        item = list(item)
        if item[2] == 'зелье':
            continue
        cur_text = f"""
Предмет:\t{item[0]}                                            
Тип:\t{item[2]}                                        
Количество:\t{item[-1]}                             
Цена покупки:\t{item[4]}
Цена продажи:\t{item[3]}       
Бонусы:                                                  
    Здоровье:\t{item[-2]} 
    Мана:\t{item[-3]}      
    Физическая атака:\t{item[7]} 
    Магическая атака:\t{item[8]}
    Броня:\t{item[6]} 
    Магическая защита:\t{item[5]}
Минимальный уровень ношения:\t{item[1]}          
"""
        if item[-4] == 1:
            cur_text += f"Статус:\t{phrases.ITEM_IS_IN_USE_TEXT}\n"
        else:
            cur_text += f"Статус:\t{phrases.ITEM_IS_NOT_IN_USE_TEXT}\n"
        text += cur_text
    for item in hero_item:
        item = list(item)
        if item[2] != 'зелье':
            continue
        cur_text = f"""
Предмет:\t{item[0]}                                            
Тип:\t{item[2]}                                        
Бонусы:                                                  
    Здоровье:\t{item[-2]} 
    Мана:\t{item[-3]}   
"""
        text += cur_text
    return text


def create_items_text(cursor, message):
    cursor.execute(f"""
    SELECT 
    locations.location_name,    
    heroes.money,
    item_x_location.item_id
    FROM heroes 
        INNER JOIN locations ON heroes.location_id = locations.location_id
        INNER JOIN item_x_location ON heroes.location_id = item_x_location.location_id
    WHERE hero_id = {message.chat.id}
    """)
    items = cursor.fetchall()
    location_name, money, item_id = items[0]
    text = f"Ты находишься в {location_name}, твой баланс: {money}\n" \
           f"Здесь можно купить/продать:\n\n"
    cnt = 1
    for item in items:
        cursor.execute(f"""
        SELECT 
            quantity 
        FROM 
            hero_x_item 
        WHERE item_id = {item[-1]} and hero_id = {message.chat.id}
    """)
        quantity = cursor.fetchall()
        if len(quantity) == 0:
            quantity = 0
        else:
            quantity = quantity[0][0]
        cursor.execute(f"""
        SELECT 
            item_type, 
            cost, 
            cost_to_sale, 
            HP, 
            Mana,  
            Attack, 
            magic_attack, 
            armour, 
            magic_armour,
            req_level,
            item_name            
        FROM
            items
        WHERE item_id = {item[-1]}
        """)
        cur_item = list(cursor.fetchall()[0])
        cur_text = f"""
№{str(cnt)} {cur_item[-1]} ID = {item[-1]}
Тип: {cur_item[0]}
Цена: {cur_item[1]}
Продажа: {cur_item[2]}
Бонусы:                                                  
    Здоровье {cur_item[3]} 
    Мана {cur_item[4]}      
    Физическая атака {cur_item[5]} 
    Магическая атака {cur_item[6]}
    Броня {cur_item[7]} 
    Магическая защита {cur_item[8]}
Минимальный уровень ношения: {cur_item[9]} 
Количество: {quantity}
"""
        text += cur_text
        cnt += 1
    return text


def add_item(cursor: sqlite3.Cursor, connect, message, item_id):
    cursor.execute(f'SELECT cost, req_level, item_type FROM items WHERE item_id = {item_id}')
    cost, req_level, item_type = cursor.fetchall()[0]
    print(cost, req_level, item_type)
    cursor.execute(f'SELECT quantity FROM hero_x_item WHERE hero_id = {message.chat.id} AND item_id = {item_id}')
    quantity = cursor.fetchall()
    if quantity:
        cursor.execute(f'UPDATE hero_x_item SET quantity = {quantity[0][0] + 1} '
                       f'WHERE hero_id = {message.chat.id} AND item_id = {item_id}')
        connect.commit()
    else:
        cursor.execute('INSERT INTO hero_x_item (hero_id, item_id, quantity, status_cd)'
                       'values (?, ?, ?, ?)',
                       [message.chat.id, item_id, 1, int(item_type == 'зелье')])
        connect.commit()


def buy_item(item_id, cursor, connect, message):
    cursor.execute(f'SELECT money, level FROM heroes WHERE hero_id = {message.chat.id}')
    money, Level = cursor.fetchall()[0]
    cursor.execute(f'SELECT cost, req_level, item_type FROM items WHERE item_id = {item_id}')
    item_cost, req_level, item_type = cursor.fetchall()[0]
    if req_level > Level:
        return phrases.NOT_ENOUGH_LEVEL_TEXT
    if item_cost > money:
        return phrases.NOT_ENOUGH_MONEY_TEXT
    cursor.execute(f'UPDATE heroes SET money = {money - item_cost} WHERE hero_id = {message.chat.id}')
    connect.commit()
    add_item(cursor, connect, message, item_id)
    return phrases.SUCCESSFUL_PURCHASE_TEXT


def sell_item(item_id, cursor, connect, message):
    cursor.execute(
        f'SELECT quantity FROM hero_x_item WHERE hero_id = {message.chat.id} and item_id = {item_id}')
    quantity = cursor.fetchall()
    if quantity and quantity[0][0] > 0:
        cursor.execute(f'SELECT status_cd FROM hero_x_item WHERE hero_id = {message.chat.id} AND ITEM_ID = {item_id}')
        status_cd = cursor.fetchall()[0][0]
        cursor.execute(f'select item_type from items where item_id = {item_id}')
        ItemType = cursor.fetchall()[0][0]
        if status_cd == 1 and quantity[0][0] == 1 and not ItemType == 'зелье':
            return phrases.TAKE_OFF_ITEM_TEXT
        cursor.execute(f'select money from heroes where hero_id = {message.chat.id}')
        money = cursor.fetchall()[0][0]
        cursor.execute(f'select cost_to_sale from items where item_id = {item_id}')
        item_cost = cursor.fetchall()[0][0]
        remain = quantity[0][0] - 1
        if remain > 0:
            cursor.execute(f'UPDATE hero_x_item set quantity = {remain} '
                           f'WHERE hero_id = {message.chat.id} and item_id = {item_id}')
            connect.commit()
        else:
            cursor.execute(f'DELETE FROM hero_x_item where hero_id = {message.chat.id} and item_id = {item_id}')
        cursor.execute(f'UPDATE heroes SET Money = {money + item_cost} '
                       f'WHERE hero_id = {message.chat.id}')
        connect.commit()
    else:
        return phrases.NO_ITEMS_FOR_SALE_TEXT
    return phrases.SUCCESSFUL_SALE_TEXT


def use_item(item_id, cursor, connect, message):
    cursor.execute(f'SELECT item_type FROM items WHERE item_id = {item_id}')
    item_type = cursor.fetchall()[0][0]
    cursor.execute(f'SELECT item_id FROM hero_x_item WHERE hero_id = {message.chat.id} AND status_cd = 1')
    active = cursor.fetchall()
    exist = False
    for item in active:
        cursor.execute(f'SELECT item_type FROM items WHERE item_id = {item[0]}')
        if cursor.fetchall()[0][0] == item_type:
            active = item[0]
            exist = True
            break
    cursor.execute(f'UPDATE hero_x_item SET status_cd = 1 WHERE hero_id = {message.chat.id} AND item_id = {item_id}')
    connect.commit()
    if not exist:
        return phrases.ITEM_IS_IN_USE_TEXT
    cursor.execute(f'UPDATE hero_x_item SET status_cd = 0 WHERE hero_id = {message.chat.id} AND item_id = {active}')
    connect.commit()
    return phrases.ITEM_IS_IN_USE_TEXT


def take_off_item(item_id, cursor, connect, message):
    cursor.execute(f'UPDATE hero_x_item SET status_cd = 0 WHERE hero_id = {message.chat.id} AND item_id = {item_id}')
    connect.commit()
    return phrases.ITEM_IS_NOT_IN_USE_TEXT


def create_mob_info_text(message, cursor: sqlite3.Cursor):
    cursor.execute(f'SELECT mob_id  FROM heroes WHERE hero_id = {message.chat.id}')
    mob_id = cursor.fetchall()[0][0]
    cursor.execute(f'SELECT mob_name, HP, XP, req_level, attack_type, attack, armour, magic_armour '
                   f'FROM mobs '
                   f'WHERE mob_id = {mob_id}')
    mob = cursor.fetchall()[0]
    text = f"Враг:{mob[0]}\n" \
           f"Здоровье: {mob[1]}\n" \
           f"Тип атака: {mob[4]}\n" \
           f"Сила атаки: {mob[5]}\n" \
           f"Броня: {mob[6]}\n" \
           f"Магическая защита: {mob[7]}\n\n" \
           f"Опыт за победу: {mob[2]}\n" \
           f"Необходимый уровень для появления у персонажа: {mob[3]}\n"
    return text


def create_bonuses(message, cursor):
    cursor.execute(f"""
    SELECT 
        item_type,
        attack,
        magic_attack,
        armour,
        magic_armour
    FROM hero_x_item 
        INNER JOIN items
            ON items.item_id = hero_x_item.item_id
    WHERE TRUE
        AND hero_id = {message.chat.id} 
        AND status_cd = 1
    """
                   )
    active_items = cursor.fetchall()
    bonuses = [0, 0, 0, 0]
    for item in active_items:
        if item[0] == 'potion':
            continue
        bonuses[0] += item[1]
        bonuses[1] += item[2]
        bonuses[2] += item[3]
        bonuses[3] += item[4]
    return bonuses


def attack_mob(message, cursor):
    bonuses = create_bonuses(message, cursor)
    cursor.execute(f'SELECT mob_id, current_hp, armour, magic_armour FROM heroes WHERE hero_id = {message.chat.id}')
    mob_id, current_hp, armour, magic_armour = cursor.fetchall()[0]
    cursor.execute(f'SELECT attack_type, attack FROM mobs WHERE mob_id = {mob_id}')
    attack_type, attack = cursor.fetchall()[0]
    if attack_type != "магический":
        attack = max(0, attack - bonuses[2] - armour)
    else:
        attack = max(0, attack - bonuses[3] - magic_armour)
    new_hp = current_hp - attack
    if new_hp <= 0:
        return phrases.END_TEXT
    cursor.execute(f'update heroes set current_hp = {new_hp} where hero_id = {message.chat.id}')
    return new_hp


def update_level(message, cursor, connect, cur_xp):
    while cur_xp >= 100:
        cur_xp -= 100
        cursor.execute(f'SELECT level, xp, money, hp, attack, magick_attack, armour, magic_armour FROM heroes '
                       f'WHERE hero_id = {message.chat.id}')
        level, xp, money, hp, attack, magick_attack, armour, magic_armour = cursor.fetchall()[0]
        cursor.execute(f'UPDATE heroes SET '
                       f'level = {level + 1}, '
                       f'hp = {hp + phrases.LEVEL_UP_HP}, '
                       f'attack = {attack + phrases.LEVEL_UP_ATTACK_ARMOUR}, '
                       f'magick_attack = {magick_attack + phrases.LEVEL_UP_ATTACK_ARMOUR}, '
                       f'XP = {cur_xp}, '
                       f'money = {money + phrases.LEVEL_UP_MONEY}, '
                       f'armour = {armour + phrases.LEVEL_UP_ATTACK_ARMOUR},'
                       f'magic_armour = {magic_armour + phrases.LEVEL_UP_ATTACK_ARMOUR} '
                       f'WHERE hero_id = {message.chat.id}')
        connect.commit()


def attack_user(message, cursor, connect, attack_type):
    win_money, win_item_id = 0, 0
    bonuses = create_bonuses(message, cursor)
    cursor.execute(f'SELECT location_id, mob_id, mob_hp, attack, magick_attack, money, xp '
                   f'FROM heroes where '
                   f'hero_id = {message.chat.id}')
    location_id, mob_id, mob_hp, attack, magic_attack, money, xp = cursor.fetchall()[0]
    cursor.execute(f'SELECT armour, magic_armour, xp FROM mobs WHERE mob_id = {mob_id}')
    armour, magic_armour, mob_xp = cursor.fetchall()[0]
    if attack_type == "physical":
        mob_hp -= attack + bonuses[0] - armour
    elif attack_type == "magical":
        mob_hp -= magic_attack + bonuses[1] - magic_armour
    cursor.execute(f'update heroes set mob_hp = {mob_hp} where hero_id = {message.chat.id}')
    connect.commit()
    if mob_hp > 0:
        return [False, mob_hp]
    xp += mob_xp
    level_up = xp // 100
    if xp >= 100:
        update_level(message, cursor, connect, xp)
    else:
        cursor.execute(f'update heroes set xp = {xp} where hero_id = {message.chat.id}')
        connect.commit()
    if location_id == 3:
        cursor.execute("""SELECT item_id,item_name FROM items WHERE req_level <= 2""")
        items = cursor.fetchall()
        win_item_id, win_item_name = items[random.randrange(0, len(items))][0]
        win_money = random.randint(0, 7)
    elif location_id == 4:
        cursor.execute("""SELECT item_id, item_name FROM items WHERE req_level = 5""")
        items = cursor.fetchall()
        win_item_id, win_item_name = items[random.randrange(0, len(items))]
        win_money = random.randint(6, 20)
    cursor.execute(f'select money from heroes where hero_id = {message.chat.id}')
    Money = cursor.fetchall()[0][0]
    cursor.execute(f'update heroes set money = {Money + win_money} where hero_id = {message.chat.id}')
    connect.commit()
    add_item(cursor, connect, message, win_item_id)
    return [True, level_up, win_item_id, win_money, win_item_name]


def create_bonuses_text(message, cursor):
    bonuses = create_bonuses(message, cursor)
    cursor.execute(
        f"""
        SELECT 
            current_hp, 
            attack, 
            magick_attack, 
            armour, 
            magic_armour 
        FROM heroes 
        WHERE hero_id = {message.chat.id}
        """)
    stats = cursor.fetchall()[0]
    text = f"Показатели:\n" \
           f"Текущее здоровье: {stats[0]}\n" \
           f"Атака: {stats[1]} + {bonuses[0]} = {stats[1] + bonuses[0]}\n" \
           f"Магическая атака: {stats[2]} + {bonuses[1]} = {stats[2] + bonuses[1]}\n" \
           f"Броня: {stats[3]} + {bonuses[2]} = {stats[3] + bonuses[2]}\n" \
           f"Магическая защита: {stats[4]} + {bonuses[3]} = {stats[4] + bonuses[3]}\n"
    return text


def drink_potion(item_id, cursor, connect, message):
    cursor.execute(f"select HP, Mana from items where item_id = {item_id}")
    HP, Mana = cursor.fetchall()[0]
    cursor.execute(f"select current_hp from heroes where hero_id = {message.chat.id}")
    CurHP = cursor.fetchall()[0][0]
    cursor.execute(f"select quantity from hero_x_item where hero_id = {message.chat.id} and item_id = {item_id}")
    quantity = cursor.fetchall()[0][0]
    cursor.execute(f"UPDATE heroes SET current_hp = {CurHP + HP} WHERE hero_id = {message.chat.id}")
    connect.commit()
    if quantity == 1:
        cursor.execute(f"DELETE from hero_x_item where hero_id = {message.chat.id} and item_id = {item_id}")
        connect.commit()
    else:
        cursor.execute(f"UPDATE hero_x_item set quantity = {quantity - 1} "
                       f"WHERE hero_id = {message.chat.id} AND item_id = {item_id}")
    return phrases.SUCCESSFUL_POTION_USE_TEXT
