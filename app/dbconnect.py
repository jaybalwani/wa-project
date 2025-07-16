import mysql.connector
import os
from flask import g, current_app
from dotenv import load_dotenv

load_dotenv()

def connection(**kwargs):
    # if "db" not in g:
    try:
        g.db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "wa-project-db.cd00i02egs50.ap-south-1.rds.amazonaws.com"),
            port=os.getenv("DB_PORT", 3306),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASS", "HotAirBalloon123!"),
            database="projectv2",
        )
        if kwargs and kwargs.get('dictFlag', {}):
            cursor = g.db.cursor(dictionary=True)
        else:
            cursor = g.db.cursor()
    except mysql.connector.Error as e:
        print(f"Error in connecting to db: {e}")
    return g.db, cursor

def close_connection(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()