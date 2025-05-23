import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, List, Tuple, Optional

class WaterIntakeAnalyzer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    def analyze_intake_patterns(self, water_log: List[Dict]) -> Dict:
        """Analyze water intake patterns and generate insights."""
        if not water_log:
            return self._generate_empty_analysis()
        
        daily_totals = self._calculate_daily_totals(water_log)
        consistency_score = self._calculate_consistency_score(daily_totals)
        peak_hours = self._identify_peak_hours(water_log)
        intake_trends = self._analyze_intake_trends(daily_totals)
        
        return {
            'consistency_score': consistency_score,
            'peak_hydration_hours': peak_hours,
            'intake_trends': intake_trends,
            'daily_average': np.mean(list(daily_totals.values())),
            'streak': self._calculate_streak(daily_totals)
        }
    
    def generate_personalized_recommendations(self,
                                            user_data: Dict,
                                            water_log: List[Dict],
                                            weather_data: Dict) -> Dict:
        """Generate personalized hydration recommendations."""
        base_recommendation = self._calculate_base_recommendation(user_data)
        weather_adjustment = self._calculate_weather_adjustment(weather_data)
        activity_adjustment = self._calculate_activity_adjustment(user_data)
        
        total_recommendation = base_recommendation + weather_adjustment + activity_adjustment
        
        return {
            'base_recommendation': base_recommendation,
            'weather_adjustment': weather_adjustment,
            'activity_adjustment': activity_adjustment,
            'total_recommendation': total_recommendation,
            'tips': self._generate_personalized_tips(user_data, water_log, weather_data)
        }
    
    def generate_progress_report(self,
                               user_data: Dict,
                               water_log: List[Dict],
                               period: str = 'week') -> Dict:
        """Generate a comprehensive progress report."""
        if not water_log:
            return self._generate_empty_report()
        
        analysis = self.analyze_intake_patterns(water_log)
        daily_totals = self._calculate_daily_totals(water_log)
        
        return {
            'period': period,
            'total_intake': sum(daily_totals.values()),
            'daily_average': analysis['daily_average'],
            'goal_achievement_rate': self._calculate_goal_achievement_rate(daily_totals, user_data['daily_goal']),
            'consistency_score': analysis['consistency_score'],
            'improvement_areas': self._identify_improvement_areas(water_log, user_data),
            'achievements': self._identify_achievements(water_log, user_data),
            'streak_data': {
                'current_streak': analysis['streak'],
                'best_streak': self._calculate_best_streak(daily_totals)
            }
        }
    
    def _calculate_daily_totals(self, water_log: List[Dict]) -> Dict:
        daily_totals = {}
        for entry in water_log:
            date = datetime.fromisoformat(entry['timestamp']).date()
            daily_totals[date] = daily_totals.get(date, 0) + entry['amount']
        return daily_totals
    
    def _calculate_consistency_score(self, daily_totals: Dict) -> float:
        if not daily_totals:
            return 0.0
        values = list(daily_totals.values())
        mean = np.mean(values)
        std = np.std(values) if len(values) > 1 else 0
        cv = (std / mean) if mean > 0 else 0
        return max(0, min(100, 100 * (1 - cv)))
    
    def _identify_peak_hours(self, water_log: List[Dict]) -> List[int]:
        hour_counts = [0] * 24
        for entry in water_log:
            hour = datetime.fromisoformat(entry['timestamp']).hour
            hour_counts[hour] += entry['amount']
        
        # Return top 3 hours
        return sorted(range(24), key=lambda x: hour_counts[x], reverse=True)[:3]
    
    def _analyze_intake_trends(self, daily_totals: Dict) -> Dict:
        if not daily_totals:
            return {'trend': 'neutral', 'change_rate': 0}
        
        dates = sorted(daily_totals.keys())
        if len(dates) < 2:
            return {'trend': 'neutral', 'change_rate': 0}
        
        values = [daily_totals[date] for date in dates]
        change_rate = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
        
        return {
            'trend': 'increasing' if change_rate > 0.1 else 'decreasing' if change_rate < -0.1 else 'stable',
            'change_rate': change_rate
        }
    
    def _calculate_streak(self, daily_totals: Dict) -> int:
        if not daily_totals:
            return 0
        
        dates = sorted(daily_totals.keys())
        current_streak = 1
        max_streak = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        
        return max_streak
    
    def _calculate_base_recommendation(self, user_data: Dict) -> int:
        weight = user_data.get('weight', 70)  # Default weight 70kg
        height = user_data.get('height', 170)  # Default height 170cm
        activity_level = user_data.get('activity_level', 'moderate')
        
        base = weight * 30  # 30ml per kg of body weight
        height_factor = height / 170.0
        
        activity_multipliers = {
            'low': 0.8,
            'moderate': 1.0,
            'high': 1.2
        }
        
        return int(base * height_factor * activity_multipliers.get(activity_level, 1.0))
    
    def _calculate_weather_adjustment(self, weather_data: Dict) -> int:
        temp = weather_data.get('temperature', 20)  # Default 20°C
        humidity = weather_data.get('humidity', 50)  # Default 50%
        
        temp_adjustment = max(0, (temp - 20) * 15)  # 15ml per degree above 20°C
        humidity_adjustment = max(0, (humidity - 50) * 5)  # 5ml per % above 50%
        
        return int(temp_adjustment + humidity_adjustment)
    
    def _calculate_activity_adjustment(self, user_data: Dict) -> int:
        activity_level = user_data.get('activity_level', 'moderate')
        
        adjustments = {
            'low': 0,
            'moderate': 300,
            'high': 700
        }
        
        return adjustments.get(activity_level, 0)
    
    def _generate_personalized_tips(self,
                                   user_data: Dict,
                                   water_log: List[Dict],
                                   weather_data: Dict) -> List[str]:
        tips = []
        
        # Weather-based tips
        temp = weather_data.get('temperature', 20)
        if temp > 25:
            tips.append("It's hot today! Consider increasing your water intake.")
        
        # Activity-based tips
        if user_data.get('activity_level') == 'high':
            tips.append("Remember to hydrate before, during, and after your workouts.")
        
        # Time-based tips
        peak_hours = self._identify_peak_hours(water_log)
        if 8 not in peak_hours:
            tips.append("Start your day with a glass of water to boost metabolism.")
        
        return tips
    
    def _calculate_goal_achievement_rate(self, daily_totals: Dict, daily_goal: int) -> float:
        if not daily_totals or daily_goal <= 0:
            return 0.0
        
        achieved_days = sum(1 for total in daily_totals.values() if total >= daily_goal)
        return (achieved_days / len(daily_totals)) * 100 if daily_totals else 0
    
    def _identify_improvement_areas(self, water_log: List[Dict], user_data: Dict) -> List[str]:
        areas = []
        daily_totals = self._calculate_daily_totals(water_log)
        
        if not daily_totals:
            return ["Start tracking your water intake regularly"]
        
        avg_intake = np.mean(list(daily_totals.values()))
        if avg_intake < user_data['daily_goal']:
            areas.append("Increase daily water intake to meet your goal")
        
        peak_hours = self._identify_peak_hours(water_log)
        if 8 not in peak_hours and 9 not in peak_hours:
            areas.append("Consider adding morning hydration to your routine")
        
        return areas
    
    def _identify_achievements(self, water_log: List[Dict], user_data: Dict) -> List[str]:
        achievements = []
        daily_totals = self._calculate_daily_totals(water_log)
        
        if not daily_totals:
            return achievements
        
        streak = self._calculate_streak(daily_totals)
        if streak >= 7:
            achievements.append("7-day streak achieved!")
        
        goal_rate = self._calculate_goal_achievement_rate(daily_totals, user_data['daily_goal'])
        if goal_rate >= 80:
            achievements.append("Consistently meeting daily goals")
        
        return achievements
    
    def _generate_empty_analysis(self) -> Dict:
        return {
            'consistency_score': 0,
            'peak_hydration_hours': [],
            'intake_trends': {'trend': 'neutral', 'change_rate': 0},
            'daily_average': 0,
            'streak': 0
        }
    
    def _generate_empty_report(self) -> Dict:
        return {
            'period': 'week',
            'total_intake': 0,
            'daily_average': 0,
            'goal_achievement_rate': 0,
            'consistency_score': 0,
            'improvement_areas': ["Start tracking your water intake"],
            'achievements': [],
            'streak_data': {
                'current_streak': 0,
                'best_streak': 0
            }
        }