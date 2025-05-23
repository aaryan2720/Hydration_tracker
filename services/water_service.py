from typing import Dict
import requests
from datetime import datetime
from .ai_service import AIService

class WaterService:
    def __init__(self):
        self.ai_service = AIService()
        self.weather_api_key = "YOUR_WEATHER_API_KEY"  # Replace with actual API key
        self.weather_base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    def calculate_base_water_intake(self, weight_lbs: float) -> float:
        """Calculate base daily water intake in ounces based on weight."""
        # Using the formula: Weight in pounds x 0.67 = daily water intake in ounces
        return weight_lbs * 0.67
    
    def get_weather_adjustment(self, city: str) -> float:
        """Get weather-based adjustment factor for water intake."""
        try:
            params = {
                'q': city,
                'appid': self.weather_api_key,
                'units': 'imperial'
            }
            response = requests.get(self.weather_base_url, params=params)
            weather_data = response.json()
            
            temp = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
            
            # Increase water intake for high temperature and humidity
            temp_factor = 1.0
            if temp > 80:
                temp_factor += 0.1
            if temp > 90:
                temp_factor += 0.1
            
            humidity_factor = 1.0
            if humidity > 60:
                humidity_factor += 0.05
            if humidity > 80:
                humidity_factor += 0.05
            
            return temp_factor * humidity_factor
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return 1.0
    
    def get_daily_quote(self) -> str:
        """Get a motivational quote about hydration using AI."""
        prompt = "Generate a short, motivational quote about staying hydrated and healthy."
        try:
            response = self.ai_service.generate_text(prompt)
            return response.strip()
        except Exception as e:
            return "Stay hydrated for a healthier you!"
    
    def calculate_recommended_intake(self, weight_lbs: float, height_inches: float,
                                   activity_level: str, city: str) -> Dict:
        """Calculate recommended daily water intake based on all factors."""
        # Calculate base intake
        base_intake = self.calculate_base_water_intake(weight_lbs)
        
        # Activity level adjustment
        activity_factors = {
            'sedentary': 1.0,
            'light': 1.1,
            'moderate': 1.2,
            'active': 1.3,
            'very_active': 1.4
        }
        activity_factor = activity_factors.get(activity_level.lower(), 1.0)
        
        # Weather adjustment
        weather_factor = self.get_weather_adjustment(city)
        
        # Calculate final recommendation
        total_intake = base_intake * activity_factor * weather_factor
        
        # Get daily quote
        quote = self.get_daily_quote()
        
        return {
            'recommended_intake_oz': round(total_intake, 1),
            'recommended_intake_ml': round(total_intake * 29.5735, 1),  # Convert to milliliters
            'weather_factor': round(weather_factor, 2),
            'activity_factor': round(activity_factor, 2),
            'daily_quote': quote,
            'timestamp': datetime.now().isoformat()
        }