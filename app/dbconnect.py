import mysql.connector
import os
from flask import g, current_app

def connection(**kwargs):
    # if "db" not in g:
    try:
        g.db = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
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