from config import DATABASE
import sqlite3
from flask import g

class model_db:
    def __init__(self):
        self.name_db = DATABASE
    
    def init_db(self):
        if "db" not in g:
            g.db = sqlite3.connect(self.name_db)
            g.db.row_factory = sqlite3.Row
        return g.db

    def createdb(self):
        db = self.init_db()
        with open("schema.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()
        
        try:
            cursor = db.cursor()
            cursor.executescript(sql_script)
            db.commit()
            print("База данных успешно создана и заполнена!")
        except sqlite3.Error as e:
            print(f"Ошибка при создании БД: {e}")
        finally:
            cursor.close()

    @staticmethod
    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()
