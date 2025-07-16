from flask import Flask
from app.config import Config
from app.routes import api_bp
from datetime import timedelta
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__, instance_relative_config=True)    
    app.config.from_object(Config)
    app.config['JWT_SECRET_KEY'] = 'e4c54db6bab492c1d9a0ebefa87e9bc910c8bbb7e26e895ce168e79261a25fa0'
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=100)      
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    jwt = JWTManager(app)

    app.register_blueprint(api_bp, url_prefix="/api")

    print(app.config["DB_HOST"])

    return app              