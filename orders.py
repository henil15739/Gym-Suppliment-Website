from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)

# Enhanced CORS configuration to allow headers and the OPTIONS method
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'gainz_db'
}

@app.route('/deploy-order', methods=['POST', 'OPTIONS']) 
def save_order():
    # Handle the Browser Preflight (OPTIONS) request
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.json
    
    # Debugging: Print received data to terminal to ensure it's arriving
    print("Received deployment data:", data)
    
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        query = """INSERT INTO orders 
                   (first_name, last_name, email, phone, address, city, pin_code, total_amount) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        
        # Using .get() prevents the "KeyError" crash if a field is missing
        # Note: Checked for 'total_amount' to match your previous JS code
        values = (
            data.get('first_name'), 
            data.get('last_name'), 
            data.get('email'), 
            data.get('phone'), 
            data.get('address'), 
            data.get('city'), 
            data.get('pin_code'), 
            data.get('total_amount') 
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({"status": "success", "message": "Order synced to database"}), 200
    
    except Exception as e:
        print("Database Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
        
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # Running on 0.0.0.0 makes it more accessible for local network testing
    app.run(debug=True, port=5000)