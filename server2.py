from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Allows your port 5500 frontend to talk to this backend
# Adjust origins if you use 127.0.0.1 instead of localhost
CORS(app, resources={r"/api/*": {"origins": ["http://127.0.0.1:5500", "http://localhost:5500"]}})

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'gainz_hq'
}

def get_db_connection():
    """Centralized connection handler."""
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """Initializes the database and vault table on startup."""
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS gainz_hq")
        cursor.execute("USE gainz_hq")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_name VARCHAR(100) NOT NULL,
                sku VARCHAR(50) UNIQUE,
                stock_level INT DEFAULT 0,
                safety_limit INT DEFAULT 10,
                batch_id VARCHAR(50),
                status VARCHAR(20)
            )
        """)
        conn.commit()
        print("--- [SYSTEM] MySQL Vault Online & Synchronized ---")
    except Error as e:
        print(f"--- [CRITICAL] Init Error: {e} ---")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- API ENDPOINTS ---

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Fetches inventory items with optional search telemetry."""
    search = request.args.get('search')
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if search:
            query = "SELECT * FROM inventory WHERE sku LIKE %s OR product_name LIKE %s ORDER BY id DESC"
            cursor.execute(query, (f"%{search}%", f"%{search}%"))
        else:
            cursor.execute("SELECT * FROM inventory ORDER BY id DESC")
            
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": "Read Failure", "details": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/inventory', methods=['POST'])
def add_item():
    """Commits a new compound to the vault."""
    data = request.json
    conn = None
    try:
        # Extract and sanitize
        name = data.get('name')
        sku = data.get('sku')
        stock = int(data.get('stock', 0))
        limit = int(data.get('limit', 10))
        batch = data.get('batch_id')

        # Automated Status Logic for Dashboard Tags
        if stock <= 5: 
            status = "Critical"
        elif stock <= limit: 
            status = "Low Stock"
        else: 
            status = "Optimal"

        conn = get_db_connection()
        cursor = conn.cursor()
        query = """INSERT INTO inventory (product_name, sku, stock_level, safety_limit, batch_id, status) 
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        
        cursor.execute(query, (name, sku, stock, limit, batch, status))
        conn.commit()
        
        return jsonify({"status": "success", "message": f"Compound {sku} Synchronized"}), 201
    except Error as e:
        return jsonify({"error": "Commit Rejected", "details": str(e)}), 400
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Revokes a compound from the vault."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
        conn.commit()
        return jsonify({"status": "deleted"}), 200
    except Error as e:
        return jsonify({"error": "Revoke Failed", "details": str(e)}), 400
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    init_db()
    # Debug mode is active for development
    app.run(debug=True, port=5000)