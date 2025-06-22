from flask import Flask, jsonify, request, session, render_template, redirect
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
import os
import jwt
import time
from datetime import datetime, timedelta
from functools import wraps
from services.water_service import WaterService

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Root route handler
@app.route('/')
def index():
    if 'user' in session:
        return render_template('dashboard.html')
    return render_template('login.html')

# Initialize MongoDB connection with retry mechanism
def get_db_connection(max_retries=3, retry_delay=2):
    for attempt in range(max_retries):
        try:
            # Check if MONGO_URI is set
            mongo_uri = os.getenv('MONGO_URI')
            if not mongo_uri:
                print('Error: MONGO_URI environment variable is not set')
                return None

            # Connect with serverSelectionTimeoutMS
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Get database
            db = client.water_tracker
            
            # Test the connection
            db.command('ping')
            
            print(f'Successfully connected to MongoDB on attempt {attempt + 1}')
            return db
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f'Failed to connect to MongoDB on attempt {attempt + 1}: {str(e)}')
                print(f'Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
            else:
                print(f'Failed to connect to MongoDB after {max_retries} attempts: {str(e)}')
                return None

# Initialize database connection
db = get_db_connection()

if db is None:
    print('Warning: Failed to establish initial database connection')

# Function to ensure database connection is available
def ensure_db_connection():
    global db
    if db is None:
        print('Attempting to reconnect to database...')
        db = get_db_connection()
        if db is None:
            return False
    try:
        # Test the connection
        db.command('ping')
        return True
    except Exception as e:
        print(f'Database connection test failed: {str(e)}')
        # Try to reconnect
        db = get_db_connection()
        return db is not None

# Middleware to check database connection before each request
@app.before_request
def check_db_connection():
    if request.endpoint and 'static' not in request.endpoint:
        if not ensure_db_connection():
            return jsonify({
                'success': False,
                'error': 'Database connection is not available',
                'details': 'Server is experiencing database connectivity issues'
            }), 503

# Add debug route to test database connection
@app.route('/api/debug/db-status')
def check_db_status():
    if db is None:
        return jsonify({
            'status': 'error',
            'message': 'Database connection not available',
            'details': 'Initial connection failed. Check MONGO_URI and network connectivity.'
        }), 503
    
    try:
        # Test the connection
        db.command('ping')
        # Get server info for more details
        server_info = db.command('serverStatus')
        return jsonify({
            'status': 'success',
            'message': 'Database connection is healthy',
            'details': {
                'version': server_info.get('version', 'unknown'),
                'uptime': server_info.get('uptime', 0),
                'connections': server_info.get('connections', {})
            }
        })
    except ConnectionFailure as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to database',
            'details': str(e)
        }), 503
    except ServerSelectionTimeoutError as e:
        return jsonify({
            'status': 'error',
            'message': 'Database server selection timeout',
            'details': str(e)
        }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Unexpected database error',
            'details': str(e)
        }), 503

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            return jsonify({'success': False, 'error': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        except:
            return jsonify({'success': False, 'error': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/user/profile', methods=['GET', 'PUT'])
@token_required
def user_profile():
    if db is None:
        print('Error: Database connection is not available')
        return jsonify({
            'success': False,
            'error': 'Database connection is not available',
            'details': 'Please try again later'
        }), 503
    
    if request.method == 'PUT':
        try:
            # Get update data from request
            update_data = request.json
            allowed_fields = {'name', 'gender', 'weight', 'height', 'activity_level'}
            
            # Validate required fields
            if not update_data:
                return jsonify({
                    'success': False,
                    'error': 'No update data provided'
                }), 400
            
            # Filter out invalid fields
            valid_updates = {k: v for k, v in update_data.items() if k in allowed_fields}
            
            if not valid_updates:
                return jsonify({
                    'success': False,
                    'error': 'No valid fields to update'
                }), 400
            
            # Get user phone from token
            token = session.get('token')
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            phone = data.get('phone')
            
            # Update user profile
            result = db.users.update_one(
                {'phone': phone},
                {'$set': valid_updates}
            )
            
            if result.modified_count == 0:
                return jsonify({
                    'success': False,
                    'error': 'Profile not found or no changes made'
                }), 404
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
            
        except Exception as e:
            print(f'Error updating profile: {str(e)}')
            return jsonify({
                'success': False,
                'error': 'Failed to update profile',
                'details': str(e)
            }), 500

    try:
        token = session.get('token')
        if not token:
            print('Error: Authentication token is missing')
            return jsonify({
                'success': False,
                'error': 'Authentication token is missing'
            }), 401

        # Decode token and extract user info
        data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        phone = data.get('phone')
        if not phone:
            print('Error: Phone number missing in token payload')
            return jsonify({
                'success': False,
                'error': 'Invalid token payload',
                'details': 'Phone number is missing'
            }), 400

        print(f'Fetching user profile for phone: {phone}')
        try:
            # Attempt database query with timeout
            user = db.users.find_one(
                {'phone': phone},
                {'name': 1, 'gender': 1, 'weight': 1, 'height': 1, 'activity_level': 1, 'daily_goal': 1, '_id': 1},
                max_time_ms=5000
            )
        except ConnectionFailure as e:
            print(f'Database connection error: {str(e)}')
            return jsonify({
                'success': False,
                'error': 'Database connection error',
                'details': str(e)
            }), 503
        except Exception as e:
            print(f'Database query error: {str(e)}')
            return jsonify({
                'success': False,
                'error': 'Database query failed',
                'details': str(e)
            }), 500

        if not user:
            print(f'User not found for phone: {phone}')
            return jsonify({
                'success': False,
                'error': 'User not found',
                'details': 'No user profile found with the provided phone number'
            }), 404

        print(f'Successfully retrieved user profile: {user}')
        profile_data = {
            'name': user.get('name', ''),
            'gender': user.get('gender', ''),
            'weight': user.get('weight', 0),
            'height': user.get('height', 0),
            'activity_level': user.get('activity_level', ''),
            'daily_goal': user.get('daily_goal', 0)
        }

        return jsonify({
            'success': True,
            'data': profile_data
        })

    except jwt.ExpiredSignatureError as e:
        print(f'Token expired: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Authentication token has expired'
        }), 401
    except jwt.InvalidTokenError as e:
        print(f'Invalid token: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Invalid authentication token'
        }), 401
    except Exception as e:
        print(f'Unexpected error in get_user_profile: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        if not phone or not password:
            return 'Phone number and password are required', 400
        
        user = db.users.find_one({'phone': phone})
        if not user or user.get('password') != password:  # In production, use proper password hashing
            return 'Invalid phone number or password', 401
        
        # Generate JWT token
        token = jwt.encode(
            {'phone': phone, 'exp': time.time() + 86400},  # 24 hour expiration
            app.secret_key,
            algorithm='HS256'
        )
        
        # Store token in session
        session['token'] = token
        session['user'] = {'phone': phone}
        
        return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')  # In production, hash the password
        
        if not all([name, phone, password]):
            return 'All fields are required', 400
        
        # Check if user already exists
        if db.users.find_one({'phone': phone}):
            return 'Phone number already registered', 409
        
        # Create new user
        new_user = {
            'name': name,
            'phone': phone,
            'password': password,  # In production, store hashed password
            'created_at': time.time()
        }
        
        try:
            db.users.insert_one(new_user)
            return redirect('/login')
        except Exception as e:
            return f'Registration failed: {str(e)}', 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/water/weekly-stats')
@token_required
def get_weekly_stats():
    try:
        if not ensure_db_connection():
            return jsonify({
                'success': False,
                'error': 'Database connection is not available',
                'details': 'Server is experiencing database connectivity issues'
            }), 503

        # Get user's phone from token
        token = session.get('token')
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        user_phone = data.get('phone')
        if not user_phone:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        # Get current date
        current_date = datetime.now().date()
        
        # Calculate start of week (Monday)
        start_of_week = current_date - timedelta(days=current_date.weekday())
        
        # Query water intake records for the past week
        weekly_records = db.water_intake.find({
            'user_phone': user_phone,
            'date': {'$gte': start_of_week.isoformat()}
        })

        try:
            # Calculate statistics
            daily_totals = {}
            streak = 0
            current_streak = 0
            today = datetime.now().date()
            
            # Process weekly records
            for record in weekly_records:
                try:
                    date = datetime.strptime(record['date'], '%Y-%m-%d').date()
                    amount = float(record.get('amount', 0))
                    
                    if amount > 0:  # Only count valid intake amounts
                        if date not in daily_totals:
                            daily_totals[date] = 0
                        daily_totals[date] += amount
                except (ValueError, KeyError) as e:
                    print(f'Error processing record: {e}')
                    continue

            # Calculate streak
            dates = sorted(daily_totals.keys(), reverse=True)
            for date in dates:
                if (today - date).days <= len(dates):  # Only count consecutive days
                    if daily_totals[date] > 0:
                        streak += 1
                    else:
                        break
                else:
                    break

            # Calculate best day and weekly average
            best_day = max(daily_totals.values()) if daily_totals else 0
            total_intake = sum(daily_totals.values())
            days_recorded = len(daily_totals)
            weekly_average = round(total_intake / max(days_recorded, 1))

        except Exception as e:
            print(f'Error calculating statistics: {e}')
            return jsonify({
                'success': False,
                'error': 'Error calculating statistics',
                'details': str(e)
            }), 500

        return jsonify({
            'success': True,
            'data': {
                'streak': streak,
                'weekly_average': weekly_average,
                'best_day': best_day
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/water/data')
@token_required
def get_water_data():
    try:
        # Add logging for debugging
        app.logger.info('Fetching water data')
        
        if not ensure_db_connection():
            return jsonify({
                'success': False,
                'error': 'Database connection is not available'
            }), 503

        # Get user's phone from token
        token = session.get('token')
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        phone = data.get('phone')
        
        if not phone:
            app.logger.error('User not authenticated')
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        # Get today's date
        today = datetime.now().date().isoformat()
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()

        # Get user profile for recommended intake
        user = db.users.find_one({'phone': phone})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User profile not found'
            }), 404

        # Calculate recommended intake based on user profile
        weight = user.get('weight', 70)  # default to 70kg
        activity_level = user.get('activity_level', 'moderate')
        
        # Basic calculation: 30ml per kg of body weight
        recommended_intake = weight * 30
        
        # Adjust based on activity level
        activity_multipliers = {
            'sedentary': 1.0,
            'light': 1.2,
            'moderate': 1.4,
            'active': 1.6,
            'very_active': 1.8
        }
        recommended_intake *= activity_multipliers.get(activity_level, 1.0)

        # Get today's water intake
        today_intake = db.water_intake.find_one(
            {'phone': phone, 'date': today}
        )
        
        # Get yesterday's water intake
        yesterday_intake = db.water_intake.find_one(
            {'phone': phone, 'date': yesterday}
        )

        # Get a motivational quote
        quotes = [
            "Stay hydrated, stay healthy!",
            "Water is the driving force of all nature.",
            "Drink water, your body will thank you!",
            "Every cell in your body needs water to function.",
            "Make drinking water a daily habit!"
        ]
        import random
        daily_quote = random.choice(quotes)

        # Calculate next refresh time (midnight)
        now = datetime.now()
        next_refresh = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        return jsonify({
            'success': True,
            'data': {
                'today_intake': today_intake.get('total_intake', 0) if today_intake else 0,
                'yesterday_intake': yesterday_intake.get('total_intake', 0) if yesterday_intake else 0,
                'recommended_intake': int(recommended_intake),
                'daily_quote': daily_quote,
                'next_refresh': next_refresh.isoformat()
            }
        })

    except Exception as e:
        app.logger.error(f'Unexpected error in get_water_data: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/api/water/add', methods=['POST'])
@token_required
def add_water_intake():
    if not ensure_db_connection():
        return jsonify({
            'success': False,
            'error': 'Database connection is not available'
        }), 503

    try:
        amount = request.json.get('amount')
        if not amount or not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid amount provided'
            }), 400

        token = session.get('token')
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        phone = data.get('phone')

        # Get today's date in YYYY-MM-DD format
        today = time.strftime('%Y-%m-%d')
        current_time = time.strftime('%H:%M:%S')

        # Create new intake record
        new_record = {
            'amount': amount,
            'timestamp': current_time
        }

        # Update or create water intake document for today
        result = db.water_intake.update_one(
            {
                'phone': phone,
                'date': today
            },
            {
                '$push': {'intake_records': new_record},
                '$inc': {'total_intake': amount},
                '$setOnInsert': {'created_at': time.time()}
            },
            upsert=True
        )

        return jsonify({
            'success': True,
            'message': 'Water intake recorded successfully'
        })

    except Exception as e:
        print(f'Error recording water intake: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to record water intake',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)