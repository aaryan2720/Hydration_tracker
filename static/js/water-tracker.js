// Water Tracker JavaScript

let currentIntake = 0;
let dailyGoal = 2500; // Default daily goal in ml

// Calculate daily water intake based on gender and activity level
function calculateDailyWaterGoal(gender, weight, activityLevel) {
    if (!weight || weight <= 0) return 3000; // Default if weight is invalid
    
    // Base calculation in ml: 35ml per kg for men, 31ml per kg for women
    let baseAmount = gender === 'male' ? 35 : 31;
    let waterPerKg = weight * baseAmount;
    
    // Activity level multipliers
    const activityMultipliers = {
        'sedentary': 1.0,      // Little or no exercise
        'light': 1.1,          // Light exercise 1-3 times/week
        'moderate': 1.2,       // Moderate exercise 4-5 times/week
        'active': 1.3,         // Very active 6-7 times/week
        'extra_active': 1.4    // Extra active, very intense exercise daily
    };
    
    // Calculate final daily goal in ml
    return Math.round(waterPerKg * (activityMultipliers[activityLevel] || 1.0));
}

// Update water goal based on user inputs
function updateWaterGoal() {
    const gender = document.getElementById('gender').value;
    const weight = parseFloat(document.getElementById('weight').value);
    const activityLevel = document.getElementById('activityLevel').value;
    
    dailyGoal = calculateDailyWaterGoal(gender, weight, activityLevel);
    updateWaterProgress();
    
    // Save user preferences
    saveUserPreferences(gender, weight, activityLevel);
}

// Save user preferences to backend
async function saveUserPreferences(gender, weight, activityLevel) {
    try {
        const response = await fetch('/api/user/preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                gender: gender,
                weight: weight,
                activity_level: activityLevel
            })
        });
        
        if (!response.ok) throw new Error('Failed to save preferences');
        
        showSuccessToast('Preferences updated successfully!');
    } catch (error) {
        console.error('Error saving preferences:', error);
        showErrorToast('Failed to save preferences');
    }
}

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
    updateWaterProgress();
    fetchWaterData(); // Add this line
});

// Toggle profile edit form
function toggleProfileEdit() {
    const displayView = document.getElementById('profileDisplay');
    const editView = document.getElementById('profileEdit');
    
    if (editView.style.display === 'none') {
        // Switching to edit mode - populate form with current values
        document.getElementById('editName').value = document.getElementById('profileName').textContent || '';
        document.getElementById('editGender').value = document.getElementById('profileGender').textContent.toLowerCase() || '';
        document.getElementById('editWeight').value = parseFloat(document.getElementById('profileWeight').textContent) || '';
        document.getElementById('editActivity').value = document.getElementById('profileActivity').getAttribute('data-value') || '';
        
        displayView.style.display = 'none';
        editView.style.display = 'block';
    } else {
        // Switching back to display mode
        displayView.style.display = 'block';
        editView.style.display = 'none';
    }
}

// Update profile
async function updateProfile(event) {
    event.preventDefault();
    
    const updateData = {
        name: document.getElementById('editName').value,
        gender: document.getElementById('editGender').value,
        weight: parseFloat(document.getElementById('editWeight').value),
        activity_level: document.getElementById('editActivity').value
    };
    
    try {
        const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessToast('Profile updated successfully');
            loadUserProfile(); // Reload profile data
            toggleProfileEdit(); // Switch back to display view
        } else {
            throw new Error(result.error || 'Failed to update profile');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showErrorToast(error.message || 'Failed to update profile');
    }
}

// Toast notification functions
function showSuccessToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function showErrorToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Quick add water intake
function quickAdd(amount) {
    addWaterIntake(amount);
}

// Calculate recommended water intake
function calculateWaterIntake(weight, height, gender, activityLevel) {
    // Convert weight from kg to lbs
    const weightLbs = weight * 2.20462;
    
    // Convert height from cm to inches
    const heightInches = height * 0.393701;
    
    // Base calculation using weight (0.67 oz per lb)
    let baseIntake = weightLbs * 0.67;
    
    // Activity level adjustment
    const activityFactors = {
        'sedentary': 1.0,
        'light': 1.1,
        'moderate': 1.2,
        'active': 1.3,
        'extra_active': 1.4
    };
    const activityFactor = activityFactors[activityLevel] || 1.0;
    
    // Gender adjustment (women typically need slightly less)
    const genderFactor = gender.toLowerCase() === 'female' ? 0.9 : 1.0;
    
    // Calculate final intake in oz
    const totalIntakeOz = baseIntake * activityFactor * genderFactor;
    
    // Convert to milliliters
    const totalIntakeMl = totalIntakeOz * 29.5735;
    
    return {
        oz: Math.round(totalIntakeOz * 10) / 10,
        ml: Math.round(totalIntakeMl * 10) / 10
    };
}

// Load user profile and update stats periodically
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile');
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to load profile');
        }

        // Start periodic updates
        updateProfileAndStats();
        setInterval(updateProfileAndStats, 60000); // Update every minute
        
        const data = result.data;
        const activityLabels = {
            'sedentary': 'Sedentary',
            'light': 'Light Exercise',
            'moderate': 'Moderate Exercise',
            'active': 'Very Active',
            'extra_active': 'Extra Active'
        };
        
        // Update profile name
        const profileNameEl = document.getElementById('profileName');
        profileNameEl.textContent = data.name || 'Not set';
        
        // Update gender
        const profileGenderEl = document.getElementById('profileGender');
        if (data.gender) {
            profileGenderEl.textContent = data.gender.charAt(0).toUpperCase() + data.gender.slice(1);
        } else {
            profileGenderEl.textContent = 'Not set';
        }
        
        // Update weight
        const profileWeightEl = document.getElementById('profileWeight');
        if (data.weight) {
            profileWeightEl.textContent = `${data.weight} kg`;
        } else {
            profileWeightEl.textContent = 'Not set';
        }
        
        // Update activity level
        const profileActivityEl = document.getElementById('profileActivity');
        if (data.activity_level) {
            profileActivityEl.textContent = activityLabels[data.activity_level] || data.activity_level;
            profileActivityEl.setAttribute('data-value', data.activity_level);
        } else {
            profileActivityEl.textContent = 'Not set';
            profileActivityEl.setAttribute('data-value', '');
        }
        
        // Calculate and update recommended intake if all required data is available
        if (data.weight && data.height && data.gender && data.activity_level) {
            const recommendedIntake = calculateWaterIntake(
                data.weight,
                data.height,
                data.gender,
                data.activity_level
            );
            
            // Update water jar goal
            const waterJar = document.querySelector('.water-jar');
            if (waterJar) {
                waterJar.setAttribute('data-goal', recommendedIntake.ml);
                document.getElementById('dailyGoal').textContent = `${recommendedIntake.ml} ml`;
            }
        }
        
        // Calculate daily goal
        dailyGoal = calculateDailyWaterGoal(data.gender, data.weight, data.activity_level);
        
        // Load current day's intake
        const waterResponse = await fetch('/api/water/data');
        const waterResult = await waterResponse.json();
        
        if (waterResult.success) {
            currentIntake = waterResult.data.total_intake || 0;
        } else {
            console.error('Failed to load water data:', waterResult.error);
            currentIntake = 0;
        }
        
        // Update profile name in navbar and hydration profile
        const userName = data.name || 'User';
        document.getElementById('profileName').textContent = userName;
        document.getElementById('profilePhone').textContent = data.phone || '';
        document.querySelector('.card-body h3').textContent = `${userName}'s Hydration Profile`;
        
        // Update water progress and weekly stats
        await Promise.all([
            updateWaterProgress(),
            updateWeeklyStats()
        ]);
    } catch (error) {
        console.error('Error loading user profile:', error);
        showErrorToast('Failed to load profile');
    }
}
async function fetchWaterData() {
    try {
        const response = await fetch('/api/water/data');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        // Update today's intake
        currentIntake = data.data.today_intake;
        updateWaterProgress();
        
        // Update yesterday's intake
        document.getElementById('yesterdayIntake').textContent = 
            `${data.data.yesterday_intake} ml`;
        
        // Update next refresh time
        const nextRefresh = new Date(data.data.next_refresh);
        document.getElementById('nextRefresh').textContent = 
            nextRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Schedule next refresh
        const timeUntilRefresh = nextRefresh - new Date();
        setTimeout(fetchWaterData, timeUntilRefresh);
        
    } catch (error) {
        console.error('Error fetching water data:', error);
        showErrorToast('Failed to fetch water data');
    }
}

// Add this to your existing DOMContentLoaded event listener

// Add water intake
async function addWaterIntake(amount) {
    if (!amount || amount <= 0) {
        showErrorToast('Please enter a valid amount');
        return;
    }

    try {
        const response = await fetch('/api/water/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: amount,
                timestamp: new Date().toISOString()
            })
        });

        if (response.ok) {
            // Immediately update the display
            currentIntake += amount;
            const waterJar = document.querySelector('.water-jar');
            if (waterJar) {
                const goalIntake = parseFloat(waterJar.getAttribute('data-goal')) || dailyGoal;
                waterJar.style.setProperty('--current-intake', currentIntake);
                
                // Update percentage display
                const percentage = Math.min((currentIntake / goalIntake) * 100, 100);
                const levelLabel = document.querySelector('.water-level-label');
                if (levelLabel) {
                    levelLabel.textContent = `${Math.round(percentage)}%`;
                }
            }
            
            // Update intake display
            document.getElementById('currentIntake').textContent = `${currentIntake} ml`;
            
            // Fetch fresh data to ensure everything is in sync
            await fetchWaterData();
            await updateWeeklyStats();
            
            showSuccessToast('Water intake added successfully!');
        } else {
            throw new Error('Failed to add water intake');
        }
    } catch (error) {
        console.error('Error adding water intake:', error);
        showErrorToast('Failed to add water intake');
    }
}

// Update water progress
async function updateWaterProgress() {
    try {
        const response = await fetch('/api/water/data');
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to load water data');
        }
        
        const data = result.data;
        currentIntake = data.today_intake || 0;
        dailyGoal = data.recommended_intake || 2500;
        
        // Update progress display
        const waterJar = document.querySelector('.water-jar');
        if (waterJar) {
            // Set the goal attribute and CSS custom properties
            waterJar.setAttribute('data-goal', dailyGoal);
            waterJar.style.setProperty('--goal-intake', dailyGoal);
            waterJar.style.setProperty('--current-intake', currentIntake);
            
            // Calculate and display percentage
            const percentage = Math.min((currentIntake / dailyGoal) * 100, 100);
            const levelLabel = document.querySelector('.water-level-label');
            if (levelLabel) {
                levelLabel.textContent = `${Math.round(percentage)}%`;
            }
            
            // Update water wave height
            const waterWave = waterJar.querySelector('.water-wave');
            if (waterWave) {
                waterWave.style.height = `${percentage}%`;
            }
        }
        
        // Update intake displays
        document.getElementById('currentIntake').textContent = `${currentIntake} ml`;
        document.getElementById('dailyGoal').textContent = `${dailyGoal} ml`;
        
        // Update yesterday's intake if available
        if (data.yesterday_intake !== undefined) {
            document.getElementById('yesterdayIntake').textContent = `${data.yesterday_intake} ml`;
        }
        
        // Update next refresh time if available
        if (data.next_refresh) {
            const nextRefresh = new Date(data.next_refresh);
            document.getElementById('nextRefresh').textContent = 
                nextRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    } catch (error) {
        console.error('Error updating water progress:', error);
        showErrorToast('Failed to update water progress');
    }
}

// Show success toast
function showSuccessToast(message) {
    showToast(message, 'success');
}

// Show error toast
function showErrorToast(message) {
    showToast(message, 'danger');
}

// Show toast notification
// Update profile and stats periodically
async function updateProfileAndStats() {
    try {
        await Promise.all([
            updateWaterProgress(),
            updateWeeklyStats()
        ]);
    } catch (error) {
        console.error('Error updating profile and stats:', error);
    }
}

// Update weekly statistics
async function updateWeeklyStats() {
    try {
        const response = await fetch('/api/water/weekly-stats');
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to load weekly stats');
        }
        
        const stats = result.data;
        
        // Update streak
        document.getElementById('currentStreak').textContent = stats.streak || 0;
        
        // Update weekly average
        document.getElementById('weeklyAverage').textContent = stats.weekly_average || 0;
        
        // Update best day
        document.getElementById('bestDay').textContent = stats.best_day || 0;
        
    } catch (error) {
        console.error('Error updating weekly stats:', error);
        showErrorToast('Failed to update weekly statistics');
    }
}

function showToast(message, type) {
    const toastContainer = document.createElement('div');
    toastContainer.style.position = 'fixed';
    toastContainer.style.top = '20px';
    toastContainer.style.right = '20px';
    toastContainer.style.zIndex = '1050';

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    document.body.appendChild(toastContainer);

    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toastContainer);
    });
}