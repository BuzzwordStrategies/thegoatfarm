const EventEmitter = require('events');

class APIHealthMonitor extends EventEmitter {
  constructor() {
    super();
    this.healthStatus = new Map();
    this.monitoringIntervals = new Map();
    this.alertThresholds = {
      errorRate: 0.1, // 10% error rate
      responseTime: 5000, // 5 seconds
      consecutiveFailures: 3
    };
  }
  
  startMonitoring(apiName, checkFunction, intervalMs = 60000) {
    if (this.monitoringIntervals.has(apiName)) {
      console.warn(`⚠️  Already monitoring ${apiName}`);
      return;
    }
    
    // Initialize health status
    this.healthStatus.set(apiName, {
      status: 'unknown',
      lastCheck: null,
      consecutiveFailures: 0,
      totalChecks: 0,
      totalFailures: 0,
      averageResponseTime: 0,
      history: []
    });
    
    // Set up monitoring interval
    const interval = setInterval(async () => {
      await this.performHealthCheck(apiName, checkFunction);
    }, intervalMs);
    
    this.monitoringIntervals.set(apiName, interval);
    
    // Perform initial check
    this.performHealthCheck(apiName, checkFunction);
    
    console.log(`🏥 Started health monitoring for ${apiName} (interval: ${intervalMs}ms)`);
  }
  
  async performHealthCheck(apiName, checkFunction) {
    const startTime = Date.now();
    const health = this.healthStatus.get(apiName);
    
    try {
      const result = await checkFunction();
      const responseTime = Date.now() - startTime;
      
      // Update health metrics
      health.status = 'healthy';
      health.lastCheck = new Date().toISOString();
      health.consecutiveFailures = 0;
      health.totalChecks++;
      
      // Calculate average response time
      health.averageResponseTime = 
        (health.averageResponseTime * (health.totalChecks - 1) + responseTime) / health.totalChecks;
      
      // Add to history
      health.history.push({
        timestamp: new Date().toISOString(),
        status: 'success',
        responseTime,
        details: result
      });
      
      // Emit health update
      this.emit('health-update', {
        api: apiName,
        status: 'healthy',
        responseTime,
        details: result
      });
      
      // Check response time threshold
      if (responseTime > this.alertThresholds.responseTime) {
        this.emit('slow-response', {
          api: apiName,
          responseTime,
          threshold: this.alertThresholds.responseTime
        });
      }
      
    } catch (error) {
      const responseTime = Date.now() - startTime;
      
      // Update health metrics
      health.consecutiveFailures++;
      health.totalChecks++;
      health.totalFailures++;
      health.lastCheck = new Date().toISOString();
      
      // Determine status based on consecutive failures
      if (health.consecutiveFailures >= this.alertThresholds.consecutiveFailures) {
        health.status = 'critical';
      } else {
        health.status = 'degraded';
      }
      
      // Add to history
      health.history.push({
        timestamp: new Date().toISOString(),
        status: 'failure',
        responseTime,
        error: error.message
      });
      
      // Emit health update
      this.emit('health-update', {
        api: apiName,
        status: health.status,
        error: error.message,
        consecutiveFailures: health.consecutiveFailures
      });
      
      // Check error rate threshold
      const errorRate = health.totalFailures / health.totalChecks;
      if (errorRate > this.alertThresholds.errorRate) {
        this.emit('high-error-rate', {
          api: apiName,
          errorRate,
          threshold: this.alertThresholds.errorRate
        });
      }
      
      // Emit critical alert if needed
      if (health.status === 'critical') {
        this.emit('api-critical', {
          api: apiName,
          consecutiveFailures: health.consecutiveFailures,
          lastError: error.message
        });
      }
    }
    
    // Trim history to last 100 entries
    if (health.history.length > 100) {
      health.history = health.history.slice(-100);
    }
  }
  
  stopMonitoring(apiName) {
    const interval = this.monitoringIntervals.get(apiName);
    if (interval) {
      clearInterval(interval);
      this.monitoringIntervals.delete(apiName);
      console.log(`🛑 Stopped monitoring ${apiName}`);
    }
  }
  
  getHealthStatus(apiName) {
    if (apiName) {
      return this.healthStatus.get(apiName);
    }
    return Object.fromEntries(this.healthStatus);
  }
  
  getHealthSummary() {
    const summary = {
      healthy: 0,
      degraded: 0,
      critical: 0,
      unknown: 0,
      totalAPIs: this.healthStatus.size
    };
    
    for (const [api, health] of this.healthStatus) {
      summary[health.status]++;
    }
    
    return summary;
  }
  
  stopAllMonitoring() {
    for (const [apiName, interval] of this.monitoringIntervals) {
      clearInterval(interval);
    }
    this.monitoringIntervals.clear();
    console.log('🛑 Stopped all API monitoring');
  }
}

module.exports = APIHealthMonitor; 