# Hydration Tracker

A Flask web application to help users track their daily water intake, set hydration goals, and receive SMS notifications using Twilio.

---

## Features

- User registration and login
- Track daily water intake
- Set and update daily water goals
- SMS notifications/reminders via Twilio
- Responsive dashboard with water log
- MongoDB for data storage

-----------------------------

## Requirements

- Python 3.8+
- MongoDB 
- Twilio account (for SMS notifications)

-----------------------------

## Project Structure

```
Hydration_tracker/
│
├── app.py
├── sms_service.py
├── requirements.txt
├── .env
├── templates/
│   ├── dashboard.html
│   ├── login.html
│   └── signup.html
├── static/
│   ├── css/
│   └── js/
└── ...


-----------------------------

## Credits

- Flask
- PyMongo
- Twilio
- Passlib
- JWT
