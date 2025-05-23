from typing import Dict


class AIConfig:
    def __init__(self):
        # OpenAI API configuration
        self.openai_config = {
            "api_key": "",  # Replace with actual API key
            "model": "gpt-4",  # or another appropriate model
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        # Weather API configuration
        self.weather_config = {
            "api_key": "YOUR_WEATHER_API_KEY",  # Replace with actual API key
            "update_frequency": 1,  # hours
            "units": "imperial"
        }
        
        # Water intake calculation settings
        self.water_settings = {
            "base_multiplier": 0.67,  # oz per pound of body weight
            "activity_levels": {
                "sedentary": 1.0,
                "light": 1.1,
                "moderate": 1.2,
                "active": 1.3,
                "very_active": 1.4
            },
            "weather_thresholds": {
                "high_temp": 80,
                "very_high_temp": 90,
                "high_humidity": 60,
                "very_high_humidity": 80
            }
        }
        
        # Analysis settings
        self.analysis_settings = {
            "update_frequency": 24,  # hours
            "min_data_points": 5,    # minimum data points for analysis
            "confidence_threshold": 0.8
        }
        
        # Report generation settings
        self.report_settings = {
            "include_visualizations": True,
            "max_recommendations": 5,
            "trend_analysis_window": 30  # days
        }
    
    def update_api_key(self, api_key: str) -> None:
        """Update the OpenAI API key."""
        self.openai_config["api_key"] = api_key
    
    def get_openai_config(self) -> Dict:
        """Get OpenAI configuration settings."""
        return self.openai_config
    
    def get_analysis_settings(self) -> Dict:
        """Get analysis configuration settings."""
        return self.analysis_settings
    
    def get_report_settings(self) -> Dict:
        """Get report generation settings."""
        return self.report_settings
    
    def get_weather_config(self) -> Dict:
        """Get weather API configuration settings."""
        return self.weather_config
    
    def get_water_settings(self) -> Dict:
        """Get water intake calculation settings."""
        return self.water_settings