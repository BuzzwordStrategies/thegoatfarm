// /src/components/ApiHealthDashboard.jsx
import React, { useEffect, useState } from 'react';
import ApiOrchestrator from '../core/ApiOrchestrator';
import './ApiHealthDashboard.css';

const ApiHealthDashboard = () => {
  const [apiStatuses, setApiStatuses] = useState({});
  const [wsConnections, setWsConnections] = useState({});
  const [metrics, setMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  
  useEffect(() => {
    const orchestrator = ApiOrchestrator.getInstance();
    
    // Listen to all health events
    orchestrator.on('health:check', (data) => {
      setApiStatuses(prev => ({
        ...prev,
        [data.api]: data.healthy
      }));
    });
    
    orchestrator.on('ws:connected', (data) => {
      setWsConnections(prev => ({
        ...prev,
        [data.api]: 'connected'
      }));
    });
    
    orchestrator.on('ws:message', (data) => {
      if (data.api === 'coinbase') {
        // Update real-time metrics
        updateMetrics(data.api, data.data);
      }
    });
    
    orchestrator.on('api:circuit:open', (data) => {
      // Critical alert - circuit breaker opened
      const alert = {
        id: Date.now(),
        type: 'critical',
        message: `CRITICAL: ${data.api} circuit breaker opened!`,
        timestamp: new Date().toISOString()
      };
      setAlerts(prev => [alert, ...prev.slice(0, 9)]);
    });
    
    orchestrator.on('api:down', (data) => {
      const alert = {
        id: Date.now(),
        type: 'warning',
        message: `WARNING: ${data.api} is down`,
        timestamp: new Date().toISOString()
      };
      setAlerts(prev => [alert, ...prev.slice(0, 9)]);
    });
    
    // Fetch initial status
    orchestrator.getAllApiStatuses().then(setApiStatuses);
    
    // Poll for metrics every 5 seconds
    const metricsInterval = setInterval(() => {
      fetchMetrics();
    }, 5000);
    
    return () => {
      clearInterval(metricsInterval);
      // Cleanup listeners
    };
  }, []);
  
  const updateMetrics = (api, data) => {
    setMetrics(prev => ({
      ...prev,
      [api]: {
        ...prev[api],
        lastUpdate: new Date().toISOString(),
        messageCount: (prev[api]?.messageCount || 0) + 1
      }
    }));
  };
  
  const fetchMetrics = async () => {
    // Fetch performance metrics from backend
    try {
      const response = await fetch('/api/metrics');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };
  
  const getStatusColor = (healthy) => {
    return healthy ? '#4CAF50' : '#F44336';
  };
  
  const getStatusIcon = (healthy) => {
    return healthy ? '✅' : '❌';
  };
  
  const apiDetails = {
    coinbase: { name: 'Coinbase', critical: true, description: 'Trading & Market Data' },
    taapi: { name: 'TAAPI', critical: false, description: 'Technical Indicators' },
    twitterapi: { name: 'TwitterAPI', critical: false, description: 'Social Sentiment' },
    scrapingbee: { name: 'ScrapingBee', critical: false, description: 'Web Scraping' },
    grok: { name: 'Grok (X AI)', critical: false, description: 'AI Analysis' },
    perplexity: { name: 'Perplexity', critical: false, description: 'Research & Insights' },
    anthropic: { name: 'Anthropic', critical: false, description: 'Claude AI' },
    coindesk: { name: 'CoinDesk', critical: false, description: 'News Feed' }
  };
  
  return (
    <div className="api-health-dashboard">
      <div className="dashboard-header">
        <h1>API Integration Status</h1>
        <div className="last-update">
          Last Update: {new Date().toLocaleTimeString()}
        </div>
      </div>
      
      <div className="alerts-section">
        {alerts.length > 0 && (
          <div className="alerts-container">
            <h3>Recent Alerts</h3>
            {alerts.map(alert => (
              <div key={alert.id} className={`alert alert-${alert.type}`}>
                <span className="alert-time">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </span>
                <span className="alert-message">{alert.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="status-grid">
        {Object.entries(apiDetails).map(([api, details]) => {
          const healthy = apiStatuses[api];
          const wsStatus = wsConnections[api];
          const apiMetrics = metrics[api] || {};
          
          return (
            <div 
              key={api} 
              className={`api-status-card ${healthy ? 'healthy' : 'unhealthy'} ${details.critical ? 'critical' : ''}`}
            >
              <div className="api-header">
                <h3>{details.name}</h3>
                <span className="status-indicator" style={{ color: getStatusColor(healthy) }}>
                  {getStatusIcon(healthy)}
                </span>
              </div>
              
              <div className="api-description">{details.description}</div>
              
              <div className="status-details">
                <div className="status-row">
                  <span className="label">Status:</span>
                  <span className={`value ${healthy ? 'text-success' : 'text-error'}`}>
                    {healthy ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                
                {wsStatus && (
                  <div className="status-row">
                    <span className="label">WebSocket:</span>
                    <span className="value text-success">{wsStatus}</span>
                  </div>
                )}
                
                {apiMetrics.responseTime && (
                  <div className="status-row">
                    <span className="label">Response Time:</span>
                    <span className="value">{apiMetrics.responseTime}ms</span>
                  </div>
                )}
                
                {apiMetrics.successRate !== undefined && (
                  <div className="status-row">
                    <span className="label">Success Rate:</span>
                    <span className="value">{apiMetrics.successRate.toFixed(1)}%</span>
                  </div>
                )}
                
                {apiMetrics.requestsToday && (
                  <div className="status-row">
                    <span className="label">Requests Today:</span>
                    <span className="value">{apiMetrics.requestsToday.toLocaleString()}</span>
                  </div>
                )}
              </div>
              
              {details.critical && !healthy && (
                <div className="critical-warning">
                  ⚠️ Critical service - trading affected
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      <div className="performance-section">
        <h2>System Performance</h2>
        <div className="performance-grid">
          <div className="metric-card">
            <h4>API Calls/Hour</h4>
            <div className="metric-value">
              {Object.values(metrics).reduce((sum, m) => sum + (m.requestsLastHour || 0), 0).toLocaleString()}
            </div>
          </div>
          
          <div className="metric-card">
            <h4>Average Response Time</h4>
            <div className="metric-value">
              {(() => {
                const times = Object.values(metrics).map(m => m.responseTime).filter(Boolean);
                const avg = times.length ? times.reduce((a, b) => a + b, 0) / times.length : 0;
                return `${avg.toFixed(0)}ms`;
              })()}
            </div>
          </div>
          
          <div className="metric-card">
            <h4>System Uptime</h4>
            <div className="metric-value">
              {(() => {
                const healthyCount = Object.values(apiStatuses).filter(Boolean).length;
                const totalCount = Object.keys(apiStatuses).length;
                const percentage = totalCount ? (healthyCount / totalCount * 100) : 0;
                return `${percentage.toFixed(1)}%`;
              })()}
            </div>
          </div>
          
          <div className="metric-card">
            <h4>Active WebSockets</h4>
            <div className="metric-value">
              {Object.keys(wsConnections).length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiHealthDashboard; 