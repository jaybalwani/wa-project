from datetime import datetime, timezone
from flask import jsonify, Blueprint, request, current_app, make_response, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
import os
import shutil
import requests
import threading
from werkzeug.utils import secure_filename
from PIL import Image
import pandas as pd
from app.dbconnect import connection, close_connection
import pytz
import io

message = Blueprint("message", __name__)

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


import io

@message.route('/broadcast', methods=['POST'])
@jwt_required()
def broadcast():
    user_id = int(get_jwt_identity())
    data = request.form
    message = data.get("message", "").strip()
    file = request.files.get("file")

    if not message and not file:
        return jsonify({'error': 'Message or file required'}), 400

    conn, cursor = connection(dictFlag=True)

    try:
        cursor.execute("SELECT number FROM contact WHERE user_id = %s", (user_id,))
        contacts = cursor.fetchall()

        # Read file content into memory once (if any)
        file_content = None
        if file:
            file.stream.seek(0)
            file_content = file.read()
            file_name = file.filename
            mime_type = file.mimetype or 'application/octet-stream'

        def send_to_contact(number):
            if file_content:
                # Create a BytesIO buffer per thread
                file_buffer = io.BytesIO(file_content)
                files = [('file', (file_name, file_buffer, mime_type))]

                payload = {
                    'chatId': f'91{number}@c.us',
                    'fileName': file_name,
                    'caption': message
                }

                url = "https://7105.media.greenapi.com/waInstance7105280978/sendFileByUpload/c82c4aead70446efbcb64c00e2a16d81346dbcc1b4424a0bbe"
                response = requests.post(url, data=payload, files=files)
                print(response.text.encode('utf8'))
            else:
                sendMessage(number, message)

        for contact in contacts:
            number = contact["number"]
            threading.Thread(target=send_to_contact, args=(number,)).start()

        return jsonify({"message": "Broadcast started"}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        close_connection()


def sendMedia(phone_number, file_name, file_path, message):
    url = "https://7105.media.greenapi.com/waInstance7105280978/sendFileByUpload/c82c4aead70446efbcb64c00e2a16d81346dbcc1b4424a0bbe"

    payload = {
    'chatId': f'91{phone_number}@c.us',
    'fileName': file_name,
    'caption': message
    }
    files = [
    ('file', (f'{file_name}', open(file_path,'rb'),'image/png'))
    ]
    headers= {}

    response = requests.post(url, data=payload, files=files)

    print(response.text.encode('utf8'))

def sendMessage(phone_number, message):
    url = "https://7105.api.greenapi.com/waInstance7105280978/sendMessage/c82c4aead70446efbcb64c00e2a16d81346dbcc1b4424a0bbe"
    payload = {
    "chatId": f"91{phone_number}@c.us", 
    "message": message
    }
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text.encode('utf8'))

def extract_filename(filename):
    return filename.rsplit(".", 1)[0]


@message.route('/upload-excel', methods=['POST'])
@jwt_required()
def upload_excel():
    user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    conn, cursor = connection()

    try:
        df = pd.read_excel(file)

        expected_columns = {'MOBILE'}
        if set(df.columns) != expected_columns:
            return jsonify({'error': 'Excel file must contain exact columns: ' + str(expected_columns)}), 400

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT IGNORE INTO contact (number, user_id)
                VALUES (%s, %s)
            """, (
                str(row['MOBILE']).strip(),
                user_id
            ))

        conn.commit()
        return jsonify({'message': 'Excel data uploaded successfully'}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        close_connection()


@message.route('/get-customers', methods=['GET'])
@jwt_required()
def get_customers():
    user_id = int(get_jwt_identity())

    conn, cursor = connection(dictFlag=True)
    try:
        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Calculate offset
        offset = (page - 1) * per_page

        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM contact WHERE user_id = %s;", (user_id,))
        total_count = cursor.fetchone()['count']

        # Get paginated results
        cursor.execute("SELECT * FROM contact WHERE user_id = %s LIMIT %s OFFSET %s", (user_id, per_page, offset))
        customers = cursor.fetchall()
        response = []

        for customer in customers:
            customer_dict = {
                'id': customer['id'],
                'mobile': customer['number'],
            }
            response.append(customer_dict)

        total_pages = (total_count + per_page - 1) // per_page

        return jsonify({
            "data": response,
            "meta": {
                "page": page,
                "per_page": per_page,
                "count": total_count,
                "total_pages": total_pages
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        close_connection()

@message.route('/get-customer/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    user_id = int(get_jwt_identity())
    conn, cursor = connection(dictFlag=True)
    try:
        cursor.execute("SELECT * FROM contact WHERE id = %s AND user_id = %s", (customer_id, user_id,))
        customer = cursor.fetchone()

        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        customer_dict = {
            'id': customer['id'],
            'mobile': customer['number'],
        }

        return jsonify(customer_dict), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        close_connection()

@message.route('/add-customer', methods=['POST'])
@jwt_required()
def add_customer():
    user_id = int(get_jwt_identity())

    conn, cursor = connection()
    try:
        mobile = request.form.get('mobile', None) 
        
        cursor.execute("SELECT * FROM contact WHERE number = %s AND user_id = %s;", (mobile, user_id))
        if cursor.fetchone():
            return jsonify({'error': 'Customer already exists'}), 400
        

        cursor.execute("""
            INSERT INTO contact (number, user_id)
            VALUES (%s, %s)
        """, (
            mobile,
            user_id
        ))
        conn.commit()
        return jsonify({'message': 'Customer added successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        close_connection()

@message.route('/delete-customer', methods=['POST'])
@jwt_required()
def delete_customer():
    user_id = int(get_jwt_identity())
    conn, cursor = connection(dictFlag = True)
    try:
        customer_id = request.json.get('customer_id')
        if not customer_id:
            return jsonify({'error': 'Missing customer ID'}), 400

        cursor.execute("SELECT * FROM contact WHERE id = %s AND user_id = %s;", (customer_id, user_id))
        customer = cursor.fetchone()

        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        cursor.execute("DELETE FROM contact WHERE id = %s", (customer_id,))
        conn.commit()

        return jsonify({'message': 'Customer deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        close_connection()

