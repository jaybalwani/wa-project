# Production config, overriden by local config that is git ignored.

import os
from dotenv import load_dotenv

load_dotenv()  

class Config:
    SECRET_KEY = "somethingjustlikethis"
    DB_HOST="127.0.0.1"
    DB_USER="root"
    DB_PASSWORD="password"
    DB_NAME = "projectv2"
    DB_PORT=3306

    DEBUG = os.getenv("DEBUG", False)