from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import bcrypt

app = Flask(__name__)
CORS(app)  # This is crucial for allowing the HTML to talk to Python

# --- 1. Database Connection ---
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123456', 
            database='logres'  # This MUST match the name in CREATE DATABASE
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# --- 2. Register Route ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        # Hash password before saving
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        query = "INSERT INTO members (first_name, last_name, email, password_hash) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (first_name, last_name, email, hashed.decode('utf-8')))
        conn.commit()
        
        # This JSON response tells your HTML to redirect/toggle
        return jsonify({"status": "success", "message": "Registration Successful!"})
    
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- 3. Login Route ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT password_hash FROM members WHERE email = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({"status": "success", "message": "Access Granted!"})
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(port=5000, debug=True)