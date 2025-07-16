from flask import Flask
from flask_cors import CORS
from app import create_app

app = create_app()
CORS(app)

if __name__ == '__main__':
    print("[ENV]: DEV") if app.config["DEBUG"] else print("[ENV]: PROD")
    app.run(debug=app.config["DEBUG"], port=5000)