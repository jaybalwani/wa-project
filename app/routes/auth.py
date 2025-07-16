from flask import Blueprint, jsonify, current_app, request, make_response
from datetime import datetime
from app.dbconnect import connection, close_connection
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, decode_token

auth = Blueprint("auth", __name__)

bcrypt = Bcrypt()

# @auth.route('/register', methods = ["POST", ])
# def register():
#     data = request.get_json()
#     username = data.get("username", None)
#     password = data.get("password", None)
#     if not username or not password:
#         return jsonify({"message": "Invalid credentials"}), 400
#     conn, cur = connection(dictFlag=True)
#     cur.execute("SELECT * FROM user WHERE username = %s;", (username, ))
#     user = cur.fetchone()
#     if user:
#         return jsonify({"message": "User already exists."}), 400
#     hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
#     cur.execute("INSERT INTO user (username, password) VALUES (%s, %s);", (username, hashed_password))
#     conn.commit()
#     close_connection()
#     return jsonify({"message": "User registered successfully."}), 200

@auth.route('/login', methods = ["POST",])
def login():

    data = request.get_json()
    username = data.get("username", None)
    password = data.get("password", None)
    if not username or not password:
        return jsonify({"message": "Invalid credentials"}), 400
    conn, cur = connection(dictFlag=True)
    try:
        cur.execute("SELECT * FROM user WHERE username = %s;", (username,))
        user = cur.fetchone()
        if not user:
            return jsonify({"message": "User not found."}), 404
        
        if not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"message": "Invalid credentials"}), 400
        
        access_token = create_access_token(identity=str(user["id"]))
        refresh_token = create_refresh_token(identity=str(user["id"]))

        response = make_response(jsonify({"access_token": access_token, "refresh_token": refresh_token}))
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        print(f"Error in login: {e}")
        return jsonify({"message": "An error occurred during login."}), 500
    finally:
        close_connection()