// API Configuration
const API_BASE_URL = 'https://nexero.onrender.com/api/v1';

// API Client
class NexeroAPI {
    async getSessions(days = 30) {
        try {
            const response = await fetch(`${API_BASE_URL}/sessions?days=${days}`);
            if (!response.ok) throw new Error('Failed to fetch sessions');
            return await response.json();
        } catch (error) {
            console.error('Error fetching sessions:', error);
            return [];
        }
    }

    async getAnalytics(days = 30) {
        try {
            const response = await fetch(`${API_BASE_URL}/analytics?days=${days}`);
            if (!response.ok) throw new Error('Failed to fetch analytics');
            return await response.json();
        } catch (error) {
            console.error('Error fetching analytics:', error);
            return this.getMockAnalytics();
        }
    }

    // Mock data for development
    getMockAnalytics() {
        return {
            totalSessions: 1247,
            avgSessionTime: '8m 32s',
            engagementRate: '87.3%',
            activeProperties: 24,
            sessionTrends: this.generateTrendData(),
            engagementMetrics: this.generateEngagementData(),
            recentSessions: this.generateMockSessions()
        };
    }

    generateTrendData() {
        const days = 30;
        const data = [];
        for (let i = days; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            data.push({
                date: date.toISOString().split('T')[0],
                sessions: Math.floor(Math.random() * 50) + 20
            });
        }
        return data;
    }

    generateEngagementData() {
        return [
            { zone: 'Living Room', visits: 892, avgTime: 45 },
            { zone: 'Kitchen', visits: 734, avgTime: 38 },
            { zone: 'Master Bedroom', visits: 678, avgTime: 52 },
            { zone: 'Bathroom', visits: 445, avgTime: 28 },
            { zone: 'Balcony', visits: 389, avgTime: 35 }
        ];
    }

    generateMockSessions() {
        const sessions = [];
        const statuses = ['completed', 'active', 'pending'];
        const properties = ['Skyline Tower A-401', 'Ocean View B-202', 'Garden Heights C-105', 'Metro Square D-304'];
        
        for (let i = 1; i <= 10; i++) {
            const startTime = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000);
            sessions.push({
                id: `SES${String(i).padStart(5, '0')}`,
                property: properties[Math.floor(Math.random() * properties.length)],
                startTime: startTime.toISOString(),
                duration: `${Math.floor(Math.random() * 15) + 3}m ${Math.floor(Math.random() * 60)}s`,
                status: statuses[Math.floor(Math.random() * statuses.length)]
            });
        }
        return sessions;
    }
}

// Initialize API client
const api = new NexeroAPI();

// Chart instances
let sessionTrendsChart = null;
let engagementChart = null;

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
    }
}

function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    const theme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
}

// Navigation
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class and reset colors
            navItems.forEach(nav => {
                nav.classList.remove('active');
                nav.classList.add('text-gray-400');
                nav.classList.remove('text-white');
            });
            
            // Add active class to clicked item
            item.classList.add('active');
            item.classList.remove('text-gray-400');
            item.classList.add('text-white');
            
            const page = item.getAttribute('data-page');
            updatePageTitle(page);
        });
    });
}

function updatePageTitle(page) {
    const titles = {
        overview: { title: 'Dashboard Overview', subtitle: 'Monitor your VR property tours in real-time' },
        sessions: { title: 'Session History', subtitle: 'View and analyze all VR tour sessions' },
        heatmaps: { title: 'Engagement Heatmaps', subtitle: 'Visualize user attention and movement patterns' },
        insights: { title: 'AI Insights', subtitle: 'Predictive analytics and recommendations' },
        properties: { title: 'Property Management', subtitle: 'Manage your VR property portfolio' }
    };
    
    const pageData = titles[page] || titles.overview;
    document.querySelector('.page-title').textContent = pageData.title;
    document.querySelector('.page-subtitle').textContent = pageData.subtitle;
}

// KPI Updates
function updateKPIs(analytics) {
    document.getElementById('totalSessions').textContent = analytics.totalSessions.toLocaleString();
    document.getElementById('avgSessionTime').textContent = analytics.avgSessionTime;
    document.getElementById('engagementRate').textContent = analytics.engagementRate;
    document.getElementById('activeProperties').textContent = analytics.activeProperties;
}

// Charts
function initSessionTrendsChart(data) {
    const ctx = document.getElementById('sessionTrendsChart').getContext('2d');
    
    if (sessionTrendsChart) {
        sessionTrendsChart.destroy();
    }
    
    sessionTrendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => {
                const date = new Date(d.date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [{
                label: 'Sessions',
                data: data.map(d => d.sessions),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    borderRadius: 8,
                    titleFont: { size: 14, weight: '600' },
                    bodyFont: { size: 13 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        font: { size: 12 },
                        color: '#6b7280'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { size: 12 },
                        color: '#6b7280',
                        maxRotation: 0
                    }
                }
            }
        }
    });
}

function initEngagementChart(data) {
    const ctx = document.getElementById('engagementChart').getContext('2d');
    
    if (engagementChart) {
        engagementChart.destroy();
    }
    
    engagementChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.zone),
            datasets: [{
                label: 'Visits',
                data: data.map(d => d.visits),
                backgroundColor: '#3b82f6',
                borderRadius: 8,
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    borderRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const visits = data[index].visits;
                            const avgTime = data[index].avgTime;
                            return [
                                `Visits: ${visits}`,
                                `Avg Time: ${avgTime}s`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        font: { size: 12 },
                        color: '#6b7280'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { size: 12 },
                        color: '#6b7280'
                    }
                }
            }
        }
    });
}

// Sessions Table
function populateSessionsTable(sessions) {
    const tbody = document.getElementById('sessionsTableBody');
    
    if (sessions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                    No sessions found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = sessions.map(session => `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
            <td class="px-6 py-4 text-sm font-semibold text-gray-900 dark:text-white">${session.id}</td>
            <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">${session.property}</td>
            <td class="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">${formatDateTime(session.startTime)}</td>
            <td class="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">${session.duration}</td>
            <td class="px-6 py-4"><span class="status-badge ${session.status}">${session.status}</span></td>
            <td class="px-6 py-4"><button class="action-btn" onclick="viewSession('${session.id}')">View Details</button></td>
        </tr>
    `).join('');
}

function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function viewSession(sessionId) {
    alert(`Viewing details for session: ${sessionId}`);
    // Implement detailed session view
}

// Data Loading
async function loadDashboardData() {
    try {
        const analytics = await api.getAnalytics();
        
        updateKPIs(analytics);
        initSessionTrendsChart(analytics.sessionTrends);
        initEngagementChart(analytics.engagementMetrics);
        populateSessionsTable(analytics.recentSessions);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function refreshData() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.style.opacity = '0.5';
    refreshBtn.disabled = true;
    
    loadDashboardData().then(() => {
        setTimeout(() => {
            refreshBtn.style.opacity = '1';
            refreshBtn.disabled = false;
        }, 500);
    });
}

// Date Range Filter
function initDateRangeFilter() {
    const dateRange = document.getElementById('dateRange');
    dateRange.addEventListener('change', (e) => {
        const days = parseInt(e.target.value);
        console.log(`Loading data for last ${days} days`);
        loadDashboardData();
    });
}

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initTheme();
    
    // Setup event listeners
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('refreshBtn').addEventListener('click', refreshData);
    
    // Initialize navigation
    initNavigation();
    
    // Initialize date range filter
    initDateRangeFilter();
    
    // Load initial data
    loadDashboardData();
    
    console.log('🚀 Nexero Dashboard initialized');
});

// Auto-refresh every 5 minutes
setInterval(() => {
    console.log('Auto-refreshing dashboard data...');
    loadDashboardData();
}, 5 * 60 * 1000);
