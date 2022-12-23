import sqlite3


def initialize_db():
    create_heroes_db()
    create_mobs_db()
    create_items()
    create_locations()
    create_hero_x_item()
    create_item_x_location()


def create_heroes_db():
    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS heroes;
        
        CREATE TABLE heroes (            
            hero_id INTEGER PRIMARY KEY autoincrement,
            nickname TEXT DEFAULT "hero",
            level INT DEFAULT 1,
            hp INT DEFAULT 100,
            current_hp INT DEFAULT 100,
            money INT DEFAULT 10,
            attack INT DEFAULT 10,
            magick_attack INT DEFAULT 10,
            xp INT DEFAULT 0,
            armour INT DEFAULT 0,
            magic_armour INT DEFAULT 0,
            location_id INT DEFAULT 1,
            mob_id INT,
            mob_hp INT
        );
        """)
    connect.commit()


def create_mobs_db():
    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()

    cursor.executescript(
        """
        DROP TABLE IF EXISTS mobs;
        
        CREATE TABLE mobs (
            mob_id INTEGER PRIMARY KEY AUTOINCREMENT,
            mob_name TEXT,
            hp INT,
            xp INT,
            req_level INT,
            attack_type TEXT, 
            attack INT,
            armour INT,
            magic_armour INT
        );
        """
    )
    connect.commit()


def create_locations():
    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS locations;
        
        CREATE TABLE locations (
            location_id INTEGER PRIMARY KEY autoincrement,
            x_coord INT DEFAULT 0,
            y_coord INT DEFAULT 0,
            location_cd TEXT,
            location_name TEXT,
            description TEXT
        );
    """)
    connect.commit()


def create_items():
    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS items;
        
        CREATE TABLE items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                cost INT DEFAULT 0,
                cost_to_sale INT DEFAULT 0,
                item_type TEXT,
                hp INT DEFAULT 0,
                mana INT DEFAULT 0,
                attack INT DEFAULT 0,
                magic_attack INT DEFAULT 0,
                armour INT DEFAULT 0,
                magic_armour INT DEFAULT 0,
                req_level INT DEFAULT 0
        );
    """)
    connect.commit()


def create_hero_x_item():
    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS hero_x_item;
        CREATE TABLE hero_x_item (
            hero_x_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id   INT NOT NULL,
            hero_id   INT NOT NULL,
            quantity  INT NOT NULL,
            status_cd INT NOT NULL
        );
        """
    )
    connect.commit()


def create_item_x_location():
    connect = sqlite3.connect('game.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS item_x_location;
        CREATE TABLE item_x_location (
            item_x_location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id        INT NOT NULL,
            item_id            INT NOT NULL,
            quantity           INT NOT NULL
        );
        """
    )
    connect.commit()
