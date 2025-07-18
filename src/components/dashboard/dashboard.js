// Dashboard JavaScript
class CryptoDashboard {
    constructor() {
        this.ws = null;
        this.notifications = [];
        this.marketData = {};
        this.news = [];
        this.socialData = { twitter: {}, reddit: {} };
        this.signals = [];
        this.apiStatus = {};
        this.priceChart = null;
        this.priceHistory = [];
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
        this.initializeChart();
    }
    
    connectWebSocket() {
        const wsUrl = window.location.hostname === 'localhost' 
            ? 'ws://localhost:3002' 
            : `ws://${window.location.hostname}:3002`;
            
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus('connected');
            this.ws.send(JSON.stringify({ type: 'subscribe', channels: ['all'] }));
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus('error');
            this.addNotification('Connection error', 'error');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus('disconnected');
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'api-status':
                this.updateAPIStatus(data.payload);
                break;
            case 'market-update':
                this.updateMarketData(data.payload);
                break;
            case 'news-update':
                this.updateNews(data.payload);
                break;
            case 'social-update':
                this.updateSocialData(data.payload);
                break;
            case 'signal':
                this.addSignal(data.payload);
                break;
            case 'alert':
                this.addNotification(data.payload.message, data.payload.type);
                break;
            case 'sentiment-update':
                this.updateSentiment(data.payload);
                break;
        }
    }
    
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchTab(tab);
            });
        });
        
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadInitialData();
        });
        
        // News search
        document.getElementById('newsSearch')?.addEventListener('input', (e) => {
            this.filterNews(e.target.value);
        });
        
        // News source filter
        document.getElementById('newsSource')?.addEventListener('change', (e) => {
            this.filterNewsBySource(e.target.value);
        });
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === tabName);
        });
    }
    
    async loadInitialData() {
        try {
            const response = await fetch('/api/dashboard/initial');
            const data = await response.json();
            
            if (data.apiStatus) this.updateAPIStatus(data.apiStatus);
            if (data.marketData) this.updateMarketData(data.marketData);
            if (data.news) this.updateNews(data.news);
            if (data.socialData) this.updateSocialData(data.socialData);
            if (data.signals) data.signals.forEach(signal => this.addSignal(signal));
            
            this.addNotification('Dashboard loaded', 'success');
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.addNotification('Failed to load dashboard data', 'error');
        }
    }
    
    updateConnectionStatus(status) {
        const statusEl = document.getElementById('connectionStatus');
        const statusClasses = {
            connected: 'bg-green-600',
            disconnected: 'bg-red-600',
            error: 'bg-red-600',
            connecting: 'bg-yellow-600'
        };
        
        statusEl.className = `px-3 py-1 rounded-full text-sm ${statusClasses[status] || statusClasses.connecting}`;
        statusEl.innerHTML = `<i class="fas fa-circle text-xs mr-1"></i> ${status.charAt(0).toUpperCase() + status.slice(1)}`;
    }
    
    addNotification(message, type = 'info') {
        const notification = {
            id: Date.now(),
            message,
            type,
            timestamp: new Date()
        };
        
        this.notifications.unshift(notification);
        this.renderNotifications();
        
        // Update badge
        const badge = document.getElementById('notificationBadge');
        badge.textContent = this.notifications.length;
        badge.classList.toggle('hidden', this.notifications.length === 0);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            this.notifications = this.notifications.filter(n => n.id !== notification.id);
            this.renderNotifications();
        }, 10000);
    }
    
    renderNotifications() {
        const container = document.getElementById('notifications');
        container.innerHTML = this.notifications.slice(0, 5).map(notif => {
            const bgColor = notif.type === 'error' ? 'bg-red-600' : 
                          notif.type === 'success' ? 'bg-green-600' : 'bg-blue-600';
            
            return `
                <div class="${bgColor} px-4 py-2 rounded-lg flex items-center justify-between">
                    <span>${notif.message}</span>
                    <button onclick="dashboard.removeNotification(${notif.id})" class="ml-4">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');
    }
    
    removeNotification(id) {
        this.notifications = this.notifications.filter(n => n.id !== id);
        this.renderNotifications();
    }
    
    updateMarketData(data) {
        this.marketData = data;
        
        // Update BTC price
        if (data.averagePrice) {
            document.getElementById('btcPrice').textContent = `$${data.averagePrice.toFixed(2)}`;
            
            // Add to price history for chart
            this.priceHistory.push({
                time: new Date(),
                price: data.averagePrice
            });
            
            // Keep only last 50 points
            if (this.priceHistory.length > 50) {
                this.priceHistory.shift();
            }
            
            this.updatePriceChart();
        }
        
        // Update sentiment
        if (data.sentiment) {
            this.updateSentiment(data.sentiment);
        }
    }
    
    updateSentiment(sentiment) {
        if (!sentiment) return;
        
        const sentimentEl = document.getElementById('sentiment');
        const sentimentBar = document.getElementById('sentimentBar');
        
        sentimentEl.textContent = sentiment.recommendation || 'NEUTRAL';
        sentimentEl.className = `text-2xl font-bold ${
            sentiment.recommendation === 'BULLISH' ? 'text-green-500' :
            sentiment.recommendation === 'BEARISH' ? 'text-red-500' : 'text-yellow-500'
        }`;
        
        const score = parseFloat(sentiment.score) || 0;
        const percentage = Math.max(0, Math.min(100, score + 50)); // Convert -50 to +50 score to 0-100%
        sentimentBar.style.width = `${percentage}%`;
        sentimentBar.className = `h-2 rounded-full ${
            score > 10 ? 'bg-green-500' :
            score < -10 ? 'bg-red-500' : 'bg-yellow-500'
        }`;
    }
    
    updateAPIStatus(status) {
        this.apiStatus = status;
        
        // Update overview metrics
        if (status.summary) {
            const activeApis = document.getElementById('activeApis');
            const systemHealth = document.getElementById('systemHealth');
            
            activeApis.textContent = `${status.summary.healthy}/${status.summary.totalAPIs}`;
            
            const healthPercentage = status.summary.totalAPIs > 0 
                ? (status.summary.healthy / status.summary.totalAPIs * 100).toFixed(0)
                : 0;
            
            systemHealth.textContent = `${healthPercentage}%`;
            systemHealth.className = healthPercentage >= 80 ? 'text-green-500' :
                                   healthPercentage >= 50 ? 'text-yellow-500' : 'text-red-500';
        }
        
        // Update API status grid
        if (status.apis) {
            this.renderAPIStatus(status.apis);
        }
    }
    
    renderAPIStatus(apis) {
        const grid = document.getElementById('apiStatusGrid');
        if (!grid) return;
        
        grid.innerHTML = apis.map(api => {
            const statusColor = api.status?.status === 'healthy' ? 'text-green-500' :
                              api.status?.status === 'degraded' ? 'text-yellow-500' :
                              api.status?.status === 'critical' ? 'text-red-500' : 'text-gray-500';
            
            const statusIcon = api.status?.status === 'healthy' ? 'fa-check-circle' :
                             api.status?.status === 'degraded' ? 'fa-exclamation-circle' :
                             api.status?.status === 'critical' ? 'fa-times-circle' : 'fa-question-circle';
            
            return `
                <div class="bg-gray-700 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-semibold">${api.name}</h4>
                        <i class="fas ${statusIcon} ${statusColor}"></i>
                    </div>
                    <div class="space-y-1 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Status:</span>
                            <span class="${statusColor}">${api.status?.status || 'unknown'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Success Rate:</span>
                            <span>${api.metrics?.successRate?.toFixed(1) || 0}%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Avg Response:</span>
                            <span>${api.metrics?.averageResponseTime?.toFixed(0) || 0}ms</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateNews(newsData) {
        this.news = newsData;
        this.renderNews();
        this.renderRecentNews();
        this.updateNewsSources();
    }
    
    renderNews() {
        const newsFeed = document.getElementById('newsFeed');
        if (!newsFeed) return;
        
        const filteredNews = this.getFilteredNews();
        
        newsFeed.innerHTML = filteredNews.length > 0 ? filteredNews.map(article => `
            <article class="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition-colors">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-2">
                            <span class="px-2 py-1 bg-blue-600 text-xs rounded">${article.source}</span>
                            <span class="text-xs text-gray-400">${this.formatTimeAgo(article.publishedAt)}</span>
                            ${this.getSentimentBadge(article.title)}
                        </div>
                        <h3 class="font-semibold mb-2">
                            <a href="${article.link}" target="_blank" rel="noopener noreferrer" 
                               class="hover:text-blue-400 transition-colors">
                                ${article.title}
                            </a>
                        </h3>
                        ${article.summary ? `<p class="text-sm text-gray-300">${article.summary}</p>` : ''}
                    </div>
                    <a href="${article.link}" target="_blank" rel="noopener noreferrer" 
                       class="ml-4 text-gray-400 hover:text-gray-200">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </div>
            </article>
        `).join('') : '<p class="text-gray-400 text-center py-8">No news articles found</p>';
    }
    
    renderRecentNews() {
        const recentNews = document.getElementById('recentNews');
        if (!recentNews) return;
        
        const latest = this.news.slice(0, 5);
        
        recentNews.innerHTML = latest.length > 0 ? latest.map(article => `
            <div class="border-b border-gray-700 pb-2 last:border-0">
                <a href="${article.link}" target="_blank" rel="noopener noreferrer" 
                   class="text-sm hover:text-blue-400 transition-colors">
                    ${article.title}
                </a>
                <div class="flex items-center space-x-2 mt-1">
                    <span class="text-xs text-gray-400">${article.source}</span>
                    <span class="text-xs text-gray-400">${this.formatTimeAgo(article.publishedAt)}</span>
                </div>
            </div>
        `).join('') : '<p class="text-gray-400">No recent news</p>';
    }
    
    updateNewsSources() {
        const sourceSelect = document.getElementById('newsSource');
        if (!sourceSelect) return;
        
        const sources = [...new Set(this.news.map(n => n.source))];
        sourceSelect.innerHTML = '<option value="all">All Sources</option>' +
            sources.map(source => `<option value="${source}">${source}</option>`).join('');
    }
    
    getFilteredNews() {
        let filtered = this.news;
        
        const searchTerm = document.getElementById('newsSearch')?.value.toLowerCase();
        if (searchTerm) {
            filtered = filtered.filter(article => 
                article.title.toLowerCase().includes(searchTerm) ||
                (article.summary && article.summary.toLowerCase().includes(searchTerm))
            );
        }
        
        const selectedSource = document.getElementById('newsSource')?.value;
        if (selectedSource && selectedSource !== 'all') {
            filtered = filtered.filter(article => article.source === selectedSource);
        }
        
        return filtered;
    }
    
    filterNews(searchTerm) {
        this.renderNews();
    }
    
    filterNewsBySource(source) {
        this.renderNews();
    }
    
    updateSocialData(data) {
        this.socialData = data;
        this.renderTwitterFeeds();
        this.renderRedditFeeds();
    }
    
    renderTwitterFeeds() {
        const container = document.getElementById('twitterFeeds');
        if (!container) return;
        
        const accounts = Object.keys(this.socialData.twitter || {});
        
        container.innerHTML = accounts.length > 0 ? accounts.map(account => `
            <div class="bg-gray-700 rounded-lg p-3">
                <div class="flex items-center justify-between mb-2">
                    <a href="https://twitter.com/${account}" target="_blank" rel="noopener noreferrer" 
                       class="font-semibold hover:text-blue-400">@${account}</a>
                    <button onclick="dashboard.removeTwitterAccount('${account}')" 
                            class="text-red-400 hover:text-red-300">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="space-y-2 max-h-48 overflow-y-auto">
                    ${(this.socialData.twitter[account] || []).map(tweet => `
                        <div class="border-t border-gray-600 pt-2">
                            <p class="text-sm">${tweet.text}</p>
                            <div class="flex items-center space-x-3 mt-1 text-xs text-gray-400">
                                <span>${this.formatTimeAgo(tweet.created_at)}</span>
                                <span><i class="fas fa-heart"></i> ${this.formatNumber(tweet.likes)}</span>
                                <span><i class="fas fa-retweet"></i> ${this.formatNumber(tweet.retweets)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('') : '<p class="text-gray-400">No Twitter accounts added</p>';
    }
    
    renderRedditFeeds() {
        const container = document.getElementById('redditFeeds');
        if (!container) return;
        
        const subreddits = Object.keys(this.socialData.reddit || {});
        
        container.innerHTML = subreddits.length > 0 ? subreddits.map(subreddit => `
            <div class="bg-gray-700 rounded-lg p-3">
                <div class="flex items-center justify-between mb-2">
                    <a href="https://reddit.com/r/${subreddit}" target="_blank" rel="noopener noreferrer" 
                       class="font-semibold hover:text-orange-400">r/${subreddit}</a>
                    <button onclick="dashboard.removeSubreddit('${subreddit}')" 
                            class="text-red-400 hover:text-red-300">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="space-y-2 max-h-48 overflow-y-auto">
                    ${(this.socialData.reddit[subreddit]?.posts || []).map(post => `
                        <div class="border-t border-gray-600 pt-2">
                            <a href="${post.link}" target="_blank" rel="noopener noreferrer" 
                               class="text-sm hover:text-blue-400">${post.title}</a>
                            <div class="flex items-center space-x-3 mt-1 text-xs text-gray-400">
                                <span><i class="fas fa-arrow-up"></i> ${post.score}</span>
                                <span><i class="fas fa-comments"></i> ${post.commentCount}</span>
                                <span>by u/${post.author}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('') : '<p class="text-gray-400">No subreddits added</p>';
    }
    
    addSignal(signal) {
        this.signals.unshift(signal);
        this.signals = this.signals.slice(0, 50); // Keep last 50 signals
        
        // Update latest signal display
        const latestSignalEl = document.getElementById('latestSignal');
        const signalConfidenceEl = document.getElementById('signalConfidence');
        
        if (latestSignalEl && signal) {
            latestSignalEl.textContent = signal.signal || '-';
            latestSignalEl.className = `text-2xl font-bold ${
                signal.signal === 'STRONG_BUY' || signal.signal === 'BUY' ? 'text-green-500' :
                signal.signal === 'STRONG_SELL' || signal.signal === 'SELL' ? 'text-red-500' : 'text-yellow-500'
            }`;
            
            if (signalConfidenceEl) {
                signalConfidenceEl.textContent = signal.confidence ? `${signal.confidence.toFixed(1)}%` : '-';
            }
        }
        
        this.renderSignals();
        
        // Add notification for strong signals
        if (signal.signal === 'STRONG_BUY' || signal.signal === 'STRONG_SELL') {
            this.addNotification(`Strong ${signal.signal} signal for ${signal.symbol}`, 'signal');
        }
    }
    
    renderSignals() {
        const signalsList = document.getElementById('signalsList');
        if (!signalsList) return;
        
        signalsList.innerHTML = this.signals.length > 0 ? this.signals.map(signal => {
            const signalColor = signal.signal === 'STRONG_BUY' || signal.signal === 'BUY' ? 'text-green-500' :
                              signal.signal === 'STRONG_SELL' || signal.signal === 'SELL' ? 'text-red-500' : 
                              'text-yellow-500';
            
            return `
                <div class="bg-gray-700 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                        <div>
                            <span class="font-semibold">${signal.symbol}</span>
                            <span class="text-sm text-gray-400 ml-2">${signal.timeframe}</span>
                        </div>
                        <span class="font-bold ${signalColor}">${signal.signal}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="text-gray-400">Confidence:</span>
                            <span class="ml-2">${signal.confidence?.toFixed(1) || 0}%</span>
                        </div>
                        <div>
                            <span class="text-gray-400">Price:</span>
                            <span class="ml-2">$${signal.price?.toFixed(2) || 0}</span>
                        </div>
                    </div>
                    ${signal.recommendation ? `
                        <p class="text-xs text-gray-300 mt-2 border-t border-gray-600 pt-2">
                            ${signal.recommendation}
                        </p>
                    ` : ''}
                    <div class="text-xs text-gray-400 mt-2">
                        ${new Date(signal.timestamp).toLocaleString()}
                    </div>
                </div>
            `;
        }).join('') : '<p class="text-gray-400">No trading signals yet</p>';
    }
    
    initializeChart() {
        const ctx = document.getElementById('priceChart');
        if (!ctx) return;
        
        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'BTC/USD',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    }
    
    updatePriceChart() {
        if (!this.priceChart) return;
        
        const labels = this.priceHistory.map(p => 
            new Date(p.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        );
        const data = this.priceHistory.map(p => p.price);
        
        this.priceChart.data.labels = labels;
        this.priceChart.data.datasets[0].data = data;
        this.priceChart.update();
    }
    
    formatTimeAgo(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }
    
    formatNumber(num) {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    }
    
    getSentimentBadge(title) {
        const positive = ['surge', 'rally', 'gain', 'bullish', 'rise', 'high', 'breakthrough'];
        const negative = ['crash', 'drop', 'fall', 'bearish', 'low', 'concern', 'warning'];
        
        const titleLower = title.toLowerCase();
        
        if (positive.some(word => titleLower.includes(word))) {
            return '<span class="px-2 py-1 bg-green-600 text-xs rounded">Bullish</span>';
        }
        if (negative.some(word => titleLower.includes(word))) {
            return '<span class="px-2 py-1 bg-red-600 text-xs rounded">Bearish</span>';
        }
        return '';
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new CryptoDashboard();
});

// Global functions for onclick handlers
function addTwitterAccount() {
    const username = prompt('Enter Twitter username (without @):');
    if (username) {
        fetch('/api/social/twitter/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
    }
}

function addSubreddit() {
    const subreddit = prompt('Enter subreddit name (without r/):');
    if (subreddit) {
        fetch('/api/social/reddit/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subreddit })
        });
    }
} 