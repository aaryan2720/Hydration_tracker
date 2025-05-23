from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from functools import wraps
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize Twilio client
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

def send_sms(to_number, message, max_retries=3, retry_delay=2):
    """Send SMS using Twilio with retry mechanism."""
    for attempt in range(max_retries):
        try:
            message = twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=to_number
            )
            return {'success': True, 'message_sid': message.sid}
        except TwilioRestException as e:
            if attempt == max_retries - 1:
                return {'success': False, 'error': str(e)}
            time.sleep(retry_delay)
        except Exception as e:
            return {'success': False, 'error': f"Unexpected error: {str(e)}"}

def test_sms_service(phone_number):
    """Test SMS service by sending a test message."""
    test_message = "This is a test message from your Water Tracker app! 💧"
    return send_sms(phone_number, test_message)

def send_goal_achievement_notification(phone_number, goal_amount, name):
    """Send notification when user reaches their daily water intake goal."""
    message = f"Hello {name}! 👋 Congratulations! You've reached your daily water intake goal of {goal_amount}ml! 💧 Keep up the great work! - Water Tracker"
    return send_sms(phone_number, message)

def send_reminder_notification(phone_number, name):
    """Send reminder notification to drink water."""
    greetings = ["Good morning", "Good afternoon", "Good evening"]
    from datetime import datetime
    hour = datetime.now().hour
    greeting = greetings[0] if hour < 12 else greetings[1] if hour < 17 else greetings[2]
    message = f"{greeting} {name}! 👋\nTime to take care of yourself! Remember to drink water and stay hydrated. 💧\nYour health matters! - Water_Tracker"
    return send_sms(phone_number, message)