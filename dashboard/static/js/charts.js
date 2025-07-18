// The GOAT Farm Dashboard JavaScript

// Toggle Sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        sidebar.classList.toggle('show');
    } else {
        sidebar.classList.toggle('collapsed');
    }
}

// Initialize sidebar state
window.addEventListener('resize', function() {
    const sidebar = document.getElementById('sidebar');
    const isMobile = window.innerWidth <= 768;
    
    if (!isMobile) {
        sidebar.classList.remove('show');
    }
});

// Global chart instance
let plChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializePLChart();
    updateBotStatuses();
    startRealtimeUpdates();
    
    // Setup AJAX navigation for smooth page transitions
    setupAjaxNavigation();
});

// Setup AJAX navigation
function setupAjaxNavigation() {
    // Add AJAX navigation to sidebar links
    document.querySelectorAll('.sidebar a').forEach(link => {
        link.addEventListener('click', function(e) {
            // Allow logout and external links to work normally
            if (this.href.includes('/logout') || this.href.includes('http')) {
                return;
            }
            
            e.preventDefault();
            const url = this.href;
            
            // Update active state
            document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
            this.classList.add('active');
            
            // Fetch and load content
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    // Extract main content area
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newContent = doc.querySelector('.content') || doc.querySelector('main');
                    
                    if (newContent) {
                        const currentContent = document.querySelector('.content') || document.querySelector('main');
                        if (currentContent) {
                            currentContent.innerHTML = newContent.innerHTML;
                        }
                        
                        // Re-initialize charts and scripts if needed
                        if (url === '/' || url === '/dashboard') {
                            initializePLChart();
                            updateBotStatuses();
                        }
                    }
                    
                    // Update URL without page reload
                    history.pushState(null, '', url);
                })
                .catch(error => {
                    console.error('Navigation error:', error);
                    // Fallback to normal navigation
                    window.location.href = url;
                });
        });
    });
}

// Initialize Combined P&L Chart (Robinhood Style)
function initializePLChart() {
    const ctx = document.getElementById('plGraph').getContext('2d');
    
    // Generate sample data for last 24 hours
    const labels = [];
    const data = [];
    let value = 10000;
    
    for (let i = 23; i >= 0; i--) {
        const time = new Date();
        time.setHours(time.getHours() - i);
        labels.push(time.getHours() + ':00');
        
        // Simulate P&L changes
        value += (Math.random() - 0.45) * 50;
        data.push(value);
    }
    
    // Determine if overall trend is positive
    const isPositive = data[data.length - 1] > data[0];
    
    // Set canvas height constraint
    ctx.canvas.style.height = '33vh';
    ctx.canvas.style.maxHeight = '300px';
    
    plChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value',
                data: data,
                borderColor: isPositive ? '#90ee90' : '#ffcccb',
                backgroundColor: isPositive ? 'rgba(144, 238, 144, 0.1)' : 'rgba(255, 204, 203, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointHoverBackgroundColor: isPositive ? '#90ee90' : '#ffcccb'
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
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#2a2a2a',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: '#3a3a3a',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return '$' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        color: '#2a2a2a'
                    },
                    ticks: {
                        color: '#666',
                        maxTicksLimit: 8
                    }
                },
                y: {
                    beginAtZero: true,
                    suggestedMax: Math.max(...data) * 1.1,
                    grid: {
                        color: '#2a2a2a'
                    },
                    ticks: {
                        color: '#666',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Update bot statuses based on P&L and win rate
function updateBotStatuses() {
    fetch('/get_status')
        .then(response => response.json())
        .then(data => {
            // Update each bot's status
            Object.keys(data.pnl).forEach(bot => {
                const statusElement = document.getElementById(`${bot}-status`);
                if (statusElement) {
                    // Determine status based on data
                    const pnl = data.pnl[bot];
                    const winRate = data.win_rates ? data.win_rates[bot] : 50;
                    const isActive = data.active_status ? data.active_status[bot] : true;
                    
                    // Set status color
                    statusElement.classList.remove('green', 'red', 'yellow');
                    
                    if (!isActive) {
                        statusElement.classList.add('red');
                    } else if (pnl < 0 || winRate < 50) {
                        statusElement.classList.add('yellow');
                    } else {
                        statusElement.classList.add('green');
                    }
                }
                
                // Update P&L display
                const pnlElement = document.getElementById(`${bot}-pnl`);
                if (pnlElement) {
                    const value = data.pnl[bot];
                    pnlElement.textContent = (value >= 0 ? '+' : '') + '$' + value.toFixed(2);
                    pnlElement.className = value >= 0 ? 'text-success' : 'text-danger';
                }
                
                // Update win rate
                const winRateElement = document.getElementById(`${bot}-winrate`);
                if (winRateElement && data.win_rates) {
                    winRateElement.textContent = data.win_rates[bot].toFixed(1) + '%';
                }
            });
            
            // Update portfolio value
            const portfolioElement = document.getElementById('portfolio-value');
            if (portfolioElement && data.portfolio) {
                portfolioElement.textContent = '$' + data.portfolio.toFixed(2);
            }
            
            // Update daily P&L
            const dailyPnlElement = document.getElementById('daily-pnl');
            if (dailyPnlElement) {
                const totalPnl = data.combined_pl || Object.values(data.pnl).reduce((a, b) => a + b, 0);
                dailyPnlElement.textContent = (totalPnl >= 0 ? '+' : '') + '$' + totalPnl.toFixed(2);
                dailyPnlElement.className = totalPnl >= 0 ? 'text-success' : 'text-danger';
            }
            
            // Update win rate
            const winRateElement = document.getElementById('win-rate');
            if (winRateElement && data.overall_win_rate) {
                winRateElement.textContent = data.overall_win_rate.toFixed(1) + '%';
            }
            
            // Update active bots count
            const activeBotsElement = document.getElementById('active-bots');
            if (activeBotsElement && data.active_count) {
                activeBotsElement.textContent = data.active_count + '/4';
            }
            
            // Update Coinbase balance
            const coinbaseBalanceElement = document.getElementById('coinbase-balance');
            if (coinbaseBalanceElement && data.coinbase_balance !== undefined) {
                if (data.coinbase_balance === 'Not connected') {
                    coinbaseBalanceElement.textContent = 'Not connected';
                } else {
                    const balance = parseFloat(data.coinbase_balance);
                    coinbaseBalanceElement.textContent = '$' + balance.toFixed(2);
                }
            }
            
            // Update chart with new data point
            if (plChart && data.portfolio) {
                // Add new data point
                plChart.data.datasets[0].data.push(data.portfolio);
                plChart.data.datasets[0].data.shift();
                
                // Update line color based on trend
                const chartData = plChart.data.datasets[0].data;
                const isPositive = chartData[chartData.length - 1] > chartData[0];
                plChart.data.datasets[0].borderColor = isPositive ? '#90ee90' : '#ffcccb';
                plChart.data.datasets[0].backgroundColor = isPositive ? 'rgba(144, 238, 144, 0.1)' : 'rgba(255, 204, 203, 0.1)';
                
                plChart.update('none');
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
        });
}

// Real-time updates
function startRealtimeUpdates() {
    // Update every 10 seconds
    setInterval(updateBotStatuses, 10000);
}

// Bot control functions
function startBot(botId) {
    updateBotControl(botId, 'start');
}

function pauseBot(botId) {
    updateBotControl(botId, 'pause');
}

function stopBot(botId) {
    updateBotControl(botId, 'stop');
}

function updateBotControl(botId, action) {
    fetch(`/${action}_bot/${botId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update status immediately
            updateBotStatuses();
            console.log(`Bot ${botId} ${action}ed successfully`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Make bot cards clickable
document.addEventListener('click', function(e) {
    const botCard = e.target.closest('.bot-card');
    if (botCard && botCard.dataset.botId) {
        window.location.href = `/bot/${botCard.dataset.botId}`;
    }
});

// Update parameter
function updateParam(bot, param, value) {
    fetch('/update_param', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `bot=${bot}&param=${param}&value=${value}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Parameter updated successfully');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
