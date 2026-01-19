// Telegram Web App initialization
const tg = window.Telegram.WebApp;
tg.expand();

// API Configuration
const API_BASE = window.location.origin + '/api';
let userData = null;
let authToken = null;

// Initialize app
async function initApp() {
    try {
        // Get init data from Telegram
        authToken = tg.initData;
        
        if (!authToken) {
            showError('Telegram verification failed');
            return;
        }

        // Load user data
        await loadUserData();
        await loadStats();
        await loadTasks();
        
    } catch (error) {
        console.error('Init error:', error);
        showError('Failed to initialize app');
    }
}

// API call helper
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': authToken,
        ...options.headers
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
    }

    return response.json();
}

// Load user data
async function loadUserData() {
    try {
        userData = await apiCall('/auth/me');
        updateUI();
    } catch (error) {
        console.error('Failed to load user data:', error);
    }
}

// Load statistics
async function loadStats() {
    try {
        const stats = await apiCall('/earning/stats');
        
        document.getElementById('balance').textContent = `${stats.balance}৳`;
        document.getElementById('today-earnings').textContent = `${stats.today_earnings}৳`;
        document.getElementById('total-earned').textContent = `${stats.total_earned}৳`;
        document.getElementById('ads-watched').textContent = `${stats.ads_watched_today}/10`;
        
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load tasks
async function loadTasks() {
    try {
        const response = await apiCall('/tasks/');
        const tasks = response.tasks;
        
        const container = document.getElementById('tasks-container');
        container.innerHTML = '';

        if (tasks.length === 0) {
            container.innerHTML = '<div class="glass-card" style="text-align: center; color: white;">কোনো টাস্ক নেই</div>';
            return;
        }

        tasks.forEach(task => {
            const taskCard = document.createElement('div');
            taskCard.className = 'glass-card feature-card';
            taskCard.innerHTML = `
                <div class="feature-icon">${getTaskIcon(task.type)}</div>
                <div class="feature-content">
                    <div class="feature-title">${task.title}</div>
                    <div class="feature-subtitle">${task.reward}৳ • ${task.description}</div>
                </div>
                ${task.completed ? 
                    '<div style="color: #4CAF50; font-size: 20px;">✓</div>' :
                    task.available ?
                        `<button class="btn" style="padding: 8px 15px; width: auto; margin: 0;" onclick="completeTask(${task.id}, '${task.url}')">করুন</button>` :
                        '<div style="color: #FFC107; font-size: 14px;">শেষ</div>'
                }
            `;
            container.appendChild(taskCard);
        });

    } catch (error) {
        console.error('Failed to load tasks:', error);
    }
}

// Get task icon
function getTaskIcon(type) {
    const icons = {
        'youtube': '▶️',
        'telegram': '✈️',
        'facebook': '👍',
        'instagram': '📷',
        'website': '🌐',
        'app_install': '📱'
    };
    return icons[type] || '📋';
}

// Watch ad
let adCooldown = null;
async function watchAd() {
    const btn = document.getElementById('watch-ad-btn');
    
    try {
        btn.disabled = true;
        btn.textContent = 'প্রসেস হচ্ছে...';

        const result = await apiCall('/earning/watch-ad', {
            method: 'POST'
        });

        // Show success message
        tg.showAlert(`✅ অভিনন্দন! আপনি ${result.earned}৳ আয় করেছেন!`);
        
        // Update UI
        await loadStats();

        // Start cooldown
        startAdCooldown(60);

    } catch (error) {
        tg.showAlert(`❌ ${error.message}`);
        btn.disabled = false;
        btn.textContent = 'বিজ্ঞাপন দেখুন';
    }
}

// Ad cooldown timer
function startAdCooldown(seconds) {
    const btn = document.getElementById('watch-ad-btn');
    const cooldownDiv = document.getElementById('ad-cooldown');
    
    let remaining = seconds;
    btn.disabled = true;

    const timer = setInterval(() => {
        remaining--;
        cooldownDiv.textContent = `পরবর্তী বিজ্ঞাপন: ${remaining}s`;
        btn.textContent = `অপেক্ষা করুন (${remaining}s)`;

        if (remaining <= 0) {
            clearInterval(timer);
            btn.disabled = false;
            btn.textContent = 'বিজ্ঞাপন দেখুন';
            cooldownDiv.textContent = '';
        }
    }, 1000);
}

// Complete task
async function completeTask(taskId, url) {
    try {
        // Open task URL
        tg.openLink(url);

        // Wait a moment then mark complete
        setTimeout(async () => {
            try {
                const result = await apiCall('/tasks/complete', {
                    method: 'POST',
                    body: JSON.stringify({ task_id: taskId })
                });

                tg.showAlert(`✅ ${result.earned}৳ আয় হয়েছে!`);
                await loadStats();
                await loadTasks();

            } catch (error) {
                tg.showAlert(`❌ ${error.message}`);
            }
        }, 3000);

    } catch (error) {
        console.error('Task error:', error);
    }
}

// Navigation
function navigateTo(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    
    // Show selected page
    document.getElementById(`${page}-page`).classList.add('active');
    
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    event.currentTarget.classList.add('active');

    // Load page-specific data
    if (page === 'referral') {
        loadReferralData();
    } else if (page === 'wallet') {
        loadWalletData();
    } else if (page === 'withdraw') {
        loadWithdrawPage();
    } else if (page === 'profile') {
        loadProfileData();
    }
}

// Load referral data
async function loadReferralData() {
    if (userData) {
        const referralLink = `https://t.me/EarnMoneyBD_bot?start=${userData.telegram_id}`;
        document.getElementById('referral-link').value = referralLink;
    }
}

// Copy referral link
function copyReferralLink() {
    const input = document.getElementById('referral-link');
    input.select();
    document.execCommand('copy');
    tg.showAlert('✅ লিংক কপি হয়েছে!');
}

// Update UI
function updateUI() {
    if (userData) {
        document.getElementById('balance').textContent = `${userData.balance}৳`;
    }
}

// Show error
function showError(message) {
    tg.showAlert(`❌ ${message}`);
}

// Initialize on load
window.addEventListener('load', initApp);
