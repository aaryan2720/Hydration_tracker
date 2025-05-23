// Water Tracker JavaScript

let currentIntake = 0;
let dailyGoal = 2500; // Default daily goal in ml

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
    loadWaterLog();
    updateWaterProgress();
    initWaterBackground();
});

// Initialize water background animation
function initWaterBackground() {
    const bg = document.getElementById('waterBackground');
    setInterval(() => {
        const drop = document.createElement('div');
        drop.className = 'water-drop';
        drop.style.left = Math.random() * 100 + '%';
        drop.style.top = Math.random() * 100 + '%';
        drop.style.width = Math.random() * 100 + 50 + 'px';
        drop.style.height = drop.style.width;
        bg.appendChild(drop);
        
        setTimeout(() => {
            bg.removeChild(drop);
        }, 4000);
    }, 2000);
}

// Quick add water intake
function quickAdd(amount) {
    document.getElementById('waterAmount').value = amount;
    addWaterIntake();
}

// Load user profile
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile');
        const data = await response.json();
        document.getElementById('profileName').textContent = data.name;
        document.getElementById('profilePhone').textContent = data.phone;
        dailyGoal = data.daily_goal || 2500;
        updateDailyGoal();
    } catch (error) {
        console.error('Error loading user profile:', error);
    }
}

// Add water intake
async function addWaterIntake() {
    const amount = parseInt(document.getElementById('waterAmount').value);
    if (!amount || amount <= 0) {
        alert('Please enter a valid amount');
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
            currentIntake += amount;
            updateWaterProgress();
            loadWaterLog();
            checkAchievements();
            showSuccessToast('Water intake added successfully!');
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addWaterModal'));
            modal.hide();
        } else {
            throw new Error('Failed to add water intake');
        }
    } catch (error) {
        console.error('Error adding water intake:', error);
        showErrorToast('Failed to add water intake');
    }
}

// Update water progress
function updateWaterProgress() {
    const waterLevel = document.getElementById('waterLevel');
    const currentIntakeSpan = document.getElementById('currentIntake');
    const dailyGoalSpan = document.getElementById('dailyGoal');

    const percentage = Math.min((currentIntake / dailyGoal) * 100, 100);
    
    waterLevel.style.height = `${percentage}%`;
    
    currentIntakeSpan.textContent = `${currentIntake} ml`;
    dailyGoalSpan.textContent = `${dailyGoal} ml`;

    // Add wave animation effect
    waterLevel.style.transform = `translateY(${Math.sin(Date.now() / 1000) * 5}px)`;
    requestAnimationFrame(updateWaterProgress);
}

// Load water log
async function loadWaterLog() {
    try {
        const response = await fetch('/api/water/log');
        const data = await response.json();
        const waterLogTable = document.getElementById('waterLogTable');
        
        waterLogTable.innerHTML = '';
        data.forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(entry.timestamp).toLocaleTimeString()}</td>
                <td>${entry.amount} ml</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteWaterEntry('${entry.id}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            waterLogTable.appendChild(row);
        });

        // Update current intake
        currentIntake = data.reduce((total, entry) => total + entry.amount, 0);
        updateWaterProgress();
    } catch (error) {
        console.error('Error loading water log:', error);
        showErrorToast('Failed to load water log');
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

// Check achievements
function checkAchievements() {
    const achievements = {
        firstDrop: currentIntake > 0,
        dailyGoal: currentIntake >= dailyGoal,
        hydrationMaster: currentIntake >= dailyGoal * 1.2
    };

    Object.entries(achievements).forEach(([achievement, achieved]) => {
        if (achieved) {
            const achievementElement = document.querySelector(`[data-achievement="${achievement}"]`);
            if (achievementElement && !achievementElement.classList.contains('achieved')) {
                achievementElement.classList.add('achieved');
                showSuccessToast(`Achievement unlocked: ${achievementElement.getAttribute('title')}`);
            }
        }
    });
}