from datetime import datetime, timedelta
from typing import Dict, List, Optional

import openai

from ai_analytics import WaterIntakeAnalyzer
from config.ai_config import AIConfig


class AIService:
    def __init__(self):
        self.config = AIConfig()
        self.analyzer =  WaterIntakeAnalyzer()
        openai.api_key = self.config.get_openai_config()['api_key']
    
    async def generate_ai_report(self, user_data: Dict, water_log: List[Dict], weather_data: Dict) -> Dict:
        """Generate a comprehensive AI-powered hydration report."""
        try:
            # Get basic analytics
            analysis = self.analyzer.analyze_intake_patterns(water_log)
            recommendations = self.analyzer.generate_personalized_recommendations(
                user_data, water_log, weather_data
            )
            progress_report = self.analyzer.generate_progress_report(user_data, water_log)
            
            # Generate AI insights using OpenAI
            insights = await self._generate_ai_insights(
                analysis, recommendations, progress_report
            )
            
            return {
                'analysis': analysis,
                'recommendations': recommendations,
                'progress': progress_report,
                'ai_insights': insights
            }
        except Exception as e:
            print(f"Error generating AI report: {str(e)}")
            return self._generate_error_report()
    
    async def _generate_ai_insights(self, analysis: Dict, recommendations: Dict, progress: Dict) -> List[Dict]:
        """Generate natural language insights using OpenAI."""
        try:
            prompt = self._create_insight_prompt(analysis, recommendations, progress)
            response = await openai.ChatCompletion.create(
                model=self.config.get_openai_config()['model'],
                messages=[
                    {"role": "system", "content": "You are a hydration expert AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.get_openai_config()['max_tokens'],
                temperature=self.config.get_openai_config()['temperature']
            )
            
            insights = self._parse_ai_response(response.choices[0].message['content'])
            return insights
        except Exception as e:
            print(f"Error generating AI insights: {str(e)}")
            return self._generate_fallback_insights()
    
    def _create_insight_prompt(self, analysis: Dict, recommendations: Dict, progress: Dict) -> str:
        """Create a prompt for the AI model based on user data."""
        return f"""Based on the following hydration data, provide 3-5 key insights and actionable recommendations:
        
Analysis:
- Consistency Score: {analysis['consistency_score']}
- Daily Average: {analysis['daily_average']}ml
- Peak Hydration Hours: {', '.join(map(str, analysis['peak_hydration_hours']))}

Current Recommendations:
- Base: {recommendations['base_recommendation']}ml
- Weather Adjustment: {recommendations['weather_adjustment']}ml
- Activity Adjustment: {recommendations['activity_adjustment']}ml

Progress:
- Goal Achievement Rate: {progress['goal_achievement_rate']}%
- Current Streak: {progress['streak_data']['current_streak']} days
- Best Streak: {progress['streak_data']['best_streak']} days

Provide insights in a structured format with 'title' and 'description' for each insight."""
    
    def _parse_ai_response(self, response: str) -> List[Dict]:
        """Parse the AI response into structured insights."""
        insights = []
        current_insight = {}
        
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('Title:'):
                if current_insight:
                    insights.append(current_insight.copy())
                current_insight = {'title': line[6:].strip()}
            elif line.startswith('Description:'):
                current_insight['description'] = line[12:].strip()
        
        if current_insight:
            insights.append(current_insight)
        
        return insights
    
    def _generate_error_report(self) -> Dict:
        """Generate a basic error report when AI analysis fails."""
        return {
            'analysis': self.analyzer._generate_empty_analysis(),
            'recommendations': {
                'base_recommendation': 2500,
                'weather_adjustment': 0,
                'activity_adjustment': 0,
                'total_recommendation': 2500,
                'tips': ['Maintain regular water intake throughout the day']
            },
            'progress': self.analyzer._generate_empty_report(),
            'ai_insights': self._generate_fallback_insights()
        }
    
    def _generate_fallback_insights(self) -> List[Dict]:
        """Generate basic insights when AI generation fails."""
        return [
            {
                'title': 'Stay Consistent',
                'description': 'Maintain a regular hydration schedule throughout the day.'
            },
            {
                'title': 'Track Your Progress',
                'description': 'Keep logging your water intake to receive personalized insights.'
            }
        ]