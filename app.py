from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
import os
import time
from dotenv import load_dotenv
from passlib.hash import pbkdf2_sha256
import jwt
from functools import wraps
from sms_service import test_sms_service, send_goal_achievement_notification, send_reminder_notification

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# MongoDB connection with retry mechanism
def get_db_connection():
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(os.getenv('MONGODB_URI'))
            # Test the connection
            client.admin.command('ping')
            return client['water_tracker']
            print("Connected to MongoDB!")
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to connect to MongoDB after {max_retries} attempts: {str(e)}")
            time.sleep(retry_delay)

try:
    db = get_db_connection()
except Exception as e:
    print(f"Database connection error: {e}")
    db = None

def calculate_water_intake(weight, height):
    """Calculate daily water intake based on weight and height."""
    base_intake = weight * 30
    
    # Adjust for height (taller people might need slightly more)
    height_factor = height / 170.0  # Using 170cm as baseline
    adjusted_intake = base_intake * height_factor
    
    # Round to nearest 100ml
    return round(adjusted_intake / 100) * 100

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            current_user = db.users.find_one({'phone': data['phone']})
            if not current_user:
                return redirect(url_for('login'))
        except:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'weight': float(request.form['weight']),
            'height': float(request.form['height']),
            'password': pbkdf2_sha256.hash(request.form['password']),
            'daily_goal': calculate_water_intake(
                float(request.form['weight']), 
                float(request.form['height'])
            ),
            'notification_frequency': 2,  # Default to 2 notifications per day
            'last_notification_time': None
        }
        
        if db.users.find_one({'phone': user_data['phone']}):
            return 'Phone number already registered', 400
        
        db.users.insert_one(user_data)
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        user = db.users.find_one({'phone': phone})
        if user and pbkdf2_sha256.verify(password, user['password']):
            token = jwt.encode(
                {'phone': phone},
                app.secret_key,
                algorithm="HS256"
            )
            session['token'] = token
            return redirect(url_for('dashboard'))
        
        return 'Invalid credentials', 401
    
    return render_template('login.html')

@app.route('/dashboard')
@token_required
def dashboard():
    db_status = True
    try:
        # Test MongoDB connection
        db.command('ping')
    except Exception as e:
        db_status = False
    return render_template('dashboard.html', db_status=db_status)

@app.route('/test-sms', methods=['POST'])
@token_required
def test_sms():
    token = session.get('token')
    user_data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    user = db.users.find_one({'phone': user_data['phone']})
    
    result = test_sms_service(user['phone'])
    if result['success']:
        return jsonify({'success': True, 'message': 'Test notification sent successfully!'})
    return jsonify({'success': False, 'message': result['error']}), 500

@app.route('/add-water', methods=['POST'])
@token_required
def add_water():
    data = request.get_json()
    amount = int(data['amount'])
    
    token = session.get('token')
    user_data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    user = db.users.find_one({'phone': user_data['phone']})
    
    water_entry = {
        'user_phone': user['phone'],
        'amount': amount,
        'timestamp': datetime.now(),
        'time': datetime.now().strftime('%I:%M %p')
    }
    
    db.water_log.insert_one(water_entry)
    
    # Calculate total intake for today
    today = datetime.now().date()
    total_intake = sum(entry['amount'] for entry in db.water_log.find({
        'user_phone': user['phone'],
        'timestamp': {
            '$gte': datetime.combine(today, datetime.min.time()),
            '$lte': datetime.combine(today, datetime.max.time())
        }
    }))
    
    # Send SMS notification if reached goal
    if total_intake >= user['daily_goal']:
        result = send_goal_achievement_notification(user['phone'], user['daily_goal'], user['name'])
        if not result['success']:
            print(f"Failed to send SMS notification: {result['error']}")

    
    return jsonify({'success': True})

@app.route('/api/water/log')
@token_required
def get_water_log():
    token = session.get('token')
    user_data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    
    # Get today's water log entries
    today = datetime.now().date()
    water_log = list(db.water_log.find({
        'user_phone': user_data['phone'],
        'timestamp': {
            '$gte': datetime.combine(today, datetime.min.time()),
            '$lte': datetime.combine(today, datetime.max.time())
        }
    }))
    
    # Convert ObjectId to string for JSON serialization
    for entry in water_log:
        entry['id'] = str(entry['_id'])
        entry['_id'] = str(entry['_id'])
        entry['timestamp'] = entry['timestamp'].isoformat()
    
    return jsonify(water_log)

@app.route('/get-user-profile')
@token_required
def get_user_profile():
    token = session.get('token')
    user_data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    user = db.users.find_one({'phone': user_data['phone']})
    return jsonify({
        'name': user['name'],
        'phone': user['phone'],
        'notification_frequency': user.get('notification_frequency', 2)
    })

@app.route('/update-notification-settings', methods=['POST'])
@token_required
def update_notification_settings():
    data = request.get_json()
    frequency = int(data['frequency'])
    
    token = session.get('token')
    user_data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    
    db.users.update_one(
        {'phone': user_data['phone']},
        {'$set': {'notification_frequency': frequency}}
    )
    
    return jsonify({'success': True})

@app.route('/send-notification')
@token_required
def send_notification():
    token = session.get('token')
    user_data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    user = db.users.find_one({'phone': user_data['phone']})
    
    current_time = datetime.now()
    if user.get('last_notification_time'):
        last_notification = user['last_notification_time']
        hours_between = 24 / user['notification_frequency']
        if (current_time - last_notification).total_seconds() < hours_between * 3600:
            return jsonify({'success': False, 'message': 'Too soon for next notification'})
    
    result = send_reminder_notification(user['phone'], user['name'])
    if result['success']:
        db.users.update_one(
            {'phone': user_data['phone']},
            {'$set': {'last_notification_time': current_time}}
        )
    return jsonify(result)

@app.route('/get-water-data')
@token_required
def get_water_data():
    token = session.get('token')
    user_data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    user = db.users.find_one({'phone': user_data['phone']})
    
    today = datetime.now().date()
    water_log = list(db.water_log.find({
        'user_phone': user['phone'],
        'timestamp': {
            '$gte': datetime.combine(today, datetime.min.time()),
            '$lte': datetime.combine(today, datetime.max.time())
        }
    }).sort('timestamp', -1))
    
    current_intake = sum(entry['amount'] for entry in water_log)
    
    return jsonify({
        'current_intake': current_intake,
        'daily_goal': user['daily_goal'],
        'log': [{
            'id': str(entry['_id']),
            'time': entry['time'],
            'amount': entry['amount']
        } for entry in water_log]
    })

@app.route('/delete-entry/<entry_id>', methods=['DELETE'])
@token_required
def delete_entry(entry_id):
    from bson.objectid import ObjectId
    db.water_log.delete_one({'_id': ObjectId(entry_id)})
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)