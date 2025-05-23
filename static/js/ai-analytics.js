// AI Analytics Dashboard Integration

class AIAnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.loadAnalytics();
            this.setupChartUpdates();
        });
    }

    async loadAnalytics() {
        try {
            const response = await fetch('/api/analytics/report');
            const data = await response.json();
            this.updateDashboard(data);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    updateDashboard(data) {
        this.updateProgressMetrics(data);
        this.updateRecommendations(data.recommendations);
        this.updateAchievements(data.achievements);
        this.updateInsightsPanel(data.insights);
        this.renderAnalyticsCharts(data);
    }

    updateProgressMetrics(data) {
        const metrics = {
            'consistencyScore': data.consistency_score?.toFixed(1) || '0',
            'dailyAverage': data.daily_average?.toFixed(0) || '0',
            'goalAchievementRate': data.goal_achievement_rate?.toFixed(1) || '0',
            'currentStreak': data.streak_data?.current_streak || '0'
        };

        Object.entries(metrics).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }

    updateRecommendations(recommendations) {
        const container = document.getElementById('aiRecommendations');
        if (!container || !recommendations) return;

        const recommendationHTML = recommendations.map(rec => `
            <div class="recommendation-card">
                <div class="recommendation-icon">
                    <i class="bi ${this.getRecommendationIcon(rec.type)}"></i>
                </div>
                <div class="recommendation-content">
                    <h6>${rec.title}</h6>
                    <p>${rec.description}</p>
                </div>
            </div>
        `).join('');

        container.innerHTML = recommendationHTML;
    }

    getRecommendationIcon(type) {
        const icons = {
            'weather': 'bi-cloud-sun',
            'activity': 'bi-activity',
            'timing': 'bi-clock',
            'general': 'bi-lightbulb'
        };
        return icons[type] || 'bi-info-circle';
    }

    updateAchievements(achievements) {
        const container = document.getElementById('achievementsList');
        if (!container || !achievements) return;

        const achievementsHTML = achievements.map(achievement => `
            <div class="achievement-card ${achievement.unlocked ? 'unlocked' : 'locked'}">
                <div class="achievement-icon">
                    <i class="bi ${achievement.icon}"></i>
                </div>
                <div class="achievement-info">
                    <h6>${achievement.title}</h6>
                    <p>${achievement.description}</p>
                </div>
            </div>
        `).join('');

        container.innerHTML = achievementsHTML;
    }

    updateInsightsPanel(insights) {
        const container = document.getElementById('aiInsights');
        if (!container || !insights) return;

        const insightsHTML = insights.map(insight => `
            <div class="insight-card">
                <div class="insight-header">
                    <i class="bi ${this.getInsightIcon(insight.type)}"></i>
                    <h6>${insight.title}</h6>
                </div>
                <p>${insight.description}</p>
                ${this.generateInsightMetric(insight)}
            </div>
        `).join('');

        container.innerHTML = insightsHTML;
    }

    getInsightIcon(type) {
        const icons = {
            'trend': 'bi-graph-up',
            'pattern': 'bi-calendar-check',
            'achievement': 'bi-trophy',
            'alert': 'bi-exclamation-triangle'
        };
        return icons[type] || 'bi-info-circle';
    }

    generateInsightMetric(insight) {
        if (!insight.metric) return '';
        
        return `
            <div class="insight-metric">
                <span class="metric-value">${insight.metric.value}</span>
                <span class="metric-label">${insight.metric.label}</span>
            </div>
        `;
    }

    renderAnalyticsCharts(data) {
        this.renderIntakePatternChart(data.intake_patterns);
        this.renderGoalProgressChart(data.goal_progress);
        this.renderTrendAnalysisChart(data.trends);
    }

    renderIntakePatternChart(patterns) {
        const ctx = document.getElementById('intakePatternChart');
        if (!ctx || !patterns) return;

        if (this.charts.intakePattern) {
            this.charts.intakePattern.destroy();
        }

        this.charts.intakePattern = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: patterns.labels,
                datasets: [{
                    label: 'Intake Pattern',
                    data: patterns.data,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Water Intake (ml)'
                        }
                    }
                }
            }
        });
    }

    renderGoalProgressChart(progress) {
        const ctx = document.getElementById('goalProgressChart');
        if (!ctx || !progress) return;

        if (this.charts.goalProgress) {
            this.charts.goalProgress.destroy();
        }

        this.charts.goalProgress = new Chart(ctx, {
            type: 'line',
            data: {
                labels: progress.labels,
                datasets: [{
                    label: 'Daily Goal Progress',
                    data: progress.data,
                    fill: true,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Achievement Rate (%)'
                        }
                    }
                }
            }
        });
    }

    renderTrendAnalysisChart(trends) {
        const ctx = document.getElementById('trendAnalysisChart');
        if (!ctx || !trends) return;

        if (this.charts.trendAnalysis) {
            this.charts.trendAnalysis.destroy();
        }

        this.charts.trendAnalysis = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trends.labels,
                datasets: [{
                    label: 'Intake Trend',
                    data: trends.data,
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Water Intake (ml)'
                        }
                    }
                }
            }
        });
    }

    setupChartUpdates() {
        const updateButtons = document.querySelectorAll('[data-chart-period]');
        updateButtons.forEach(button => {
            button.addEventListener('click', () => {
                const period = button.dataset.chartPeriod;
                this.updateChartsForPeriod(period);
            });
        });
    }

    async updateChartsForPeriod(period) {
        try {
            const response = await fetch(`/api/analytics/report?period=${period}`);
            const data = await response.json();
            this.renderAnalyticsCharts(data);
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }
}

// Initialize the dashboard
const aiDashboard = new AIAnalyticsDashboard();