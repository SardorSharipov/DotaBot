import sqlite3
import numpy as np
import telebot.types


def db_add_all():
    db_add_mobs()
    db_add_locations()
    db_add_items()
    db_add_item_x_location()


def db_add_mobs():
    def get_attr_by_level(level):
        attr_dict = {
            'hp': int(np.random.uniform(level * 100, level * 200)),
            'xp': int(np.random.uniform(level * 100, level * 200)),
            'attack_type': np.random.choice(['магический', 'физический']),
            'attack': int(np.random.uniform(level * 10, level * 20)),
            'armour': int(np.random.uniform(level * 1, level * 5)),
            'magic_armour': int(np.random.uniform(level * 1, level * 5))
        }
        return attr_dict

    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    mob_names = [
        ('крип-крипочек', 1),
        ('крип-мечник', 1),
        ('крип-маг', 2),
        ('анти-маг', 5),
        ('рошан', 10),
        ('кентавр', 4),
        ('медведь-демон', 4),
        ('знаменосец', 2),
        ('сатира', 5),
        ('крысы', 1),
        ('шишка-мен', 3),
        ('сф-дед-инсайд', 20)
    ]
    for mob in mob_names:
        mob_name = mob[0]
        req_level = mob[1]
        attr = get_attr_by_level(req_level)
        cursor.execute("""
            INSERT INTO 
                mobs (mob_name, hp, xp, req_level, attack_type, attack, armour, magic_armour)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)            
            """, [
            mob_name,
            attr['hp'],
            attr['xp'],
            req_level,
            attr['attack_type'],
            attr['attack'],
            attr['armour'],
            attr['magic_armour']
        ])
        connect.commit()


def db_add_items():
    def get_items_by_level(level):
        attr_dict = {
            'cost': int(np.random.uniform(level * 100, level * 200)),
            'cost_to_sale': int(np.random.uniform(level * 50, level * 100)),
            'hp': int(np.random.uniform(level * 100, level * 200)),
            'xp': int(np.random.uniform(level * 100, level * 200)),
            'attack': int(np.random.uniform(level * 10, level * 20)),
            'magic_attack': int(np.random.uniform(level * 10, level * 20)),
            'armour': int(np.random.uniform(level * 1, level * 5)),
            'magic_armour': int(np.random.uniform(level * 1, level * 5))
        }
        return attr_dict

    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    item_names = [
        ('наручи легкие', 1, 'наручи'),
        ('наручи стальные', 2, 'наручи'),
        ('наручи золотые', 5, 'наручи'),
        ('наручи драконьи', 10, 'наручи'),
        ('сапоги легкие', 1, 'сапоги'),
        ('сапоги стальные', 2, 'сапоги'),
        ('сапоги золотые', 5, 'сапоги'),
        ('сапоги драконьи', 10, 'сапоги'),
        ('шлем легкий', 1, 'шлем'),
        ('шлем стальной', 2, 'шлем'),
        ('шлем золотой', 5, 'шлем'),
        ('шлем драконий', 10, 'шлем'),
        ('броня легкая', 1, 'броня'),
        ('броня стальная', 2, 'броня'),
        ('броня золотая', 5, 'броня'),
        ('броня драконья', 10, 'броня'),
        ('меч деревянный', 1, 'меч'),
        ('меч стальной', 2, 'меч'),
        ('меч золотой', 5, 'меч'),
        ('меч драконий', 10, 'меч'),
        ('топор деревянный', 1, 'оружие'),
        ('топор стальной', 2, 'оружие'),
        ('топор золотой', 5, 'оружие'),
        ('топор драконий', 10, 'оружие'),
        ('хилка', 1, 'зелье'),
        ('кларити', 1, 'зелье')
    ]
    for item_name in item_names:
        item_nm = item_name[0]
        req_level = item_name[1]
        item_type = item_name[2]
        attr = get_items_by_level(req_level)
        cursor.execute("""
            INSERT INTO 
                items (
                    item_name, cost, cost_to_sale, item_type, hp, 
                    mana, attack, magic_attack,armour,magic_armour, req_level
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
            item_nm,
            attr['cost'],
            attr['cost_to_sale'],
            item_type,
            attr['hp'],
            attr['xp'],
            attr['attack'],
            attr['magic_attack'],
            attr['armour'],
            attr['magic_armour'],
            req_level
        ])
        connect.commit()


def db_add_locations():
    def get_location():
        attr_dict = {
            'x_coord': int(np.random.uniform(5, 10)),
            'y_coord': int(np.random.uniform(5, 10))
        }
        return attr_dict

    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    loc_names = [
        ('потайная лавка', "центр скупки особых предметов", "город"),
        ('база', "база", "город"),
        ('рошан', "рош пит [мобы [6-20] уровня]", "подземелье"),
        ('лес', "лес нейтральных крипов [мобы [1-5] уровня]", "подземелье")
    ]
    for loc in loc_names:
        loc_name = loc[0]
        loc_info = loc[1]
        loc_type = loc[2]
        attr = get_location()
        cursor.execute("""
            INSERT INTO 
                locations (x_coord, y_coord, location_cd, location_name, description)
            VALUES (?, ?, ?, ?, ?)
            """, [
            attr['x_coord'],
            attr['y_coord'],
            loc_type,
            loc_name,
            loc_info
        ])
        connect.commit()


def db_add_item_x_location():
    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.execute("""
                INSERT INTO item_x_location (location_id, item_id, quantity)
                SELECT
                    1,
                    item_id,
                    5
                FROM
                    items
                WHERE TRUE
                    AND items.req_level >= 5
                """)
    connect.commit()
    cursor.execute("""
                    INSERT INTO item_x_location (location_id, item_id, quantity)
                    SELECT
                        2,
                        item_id,
                        5
                    FROM
                        items
                    WHERE TRUE
                        AND items.req_level < 5
                    """)
    connect.commit()


def give_open_bonus(message: telebot.types.Message):
    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.execute(
        f"""
        INSERT INTO hero_x_item (hero_id, item_id, quantity, status_cd)
           SELECT
               {message.chat.id},
               item_id,
               1,
               1
           FROM items
           WHERE item_name = 'броня легкая'
           UNION ALL
           SELECT
               {message.chat.id},
               item_id,
               1,
               1
           FROM items
           WHERE item_type = 'зелье'           
   """)
    connect.commit()
