const APIKeyAuditor = require('./utils/security/api-key-audit');
const SecureAPIKeyManager = require('./utils/security/api-key-manager');
const APIHealthMonitor = require('./utils/monitoring/api-health-monitor');
const fs = require('fs').promises;
const path = require('path');

class APIIntegrationDashboard {
  constructor() {
    this.auditor = new APIKeyAuditor();
    this.keyManager = new SecureAPIKeyManager();
    this.healthMonitor = new APIHealthMonitor();
    this.setupHealthMonitorListeners();
  }
  
  setupHealthMonitorListeners() {
    this.healthMonitor.on('health-update', (data) => {
      console.log(`\n💚 Health Update - ${data.api}: ${data.status}`);
      if (data.responseTime) {
        console.log(`   Response time: ${data.responseTime}ms`);
      }
    });
    
    this.healthMonitor.on('api-critical', (data) => {
      console.log(`\n🚨 CRITICAL ALERT - ${data.api}`);
      console.log(`   Consecutive failures: ${data.consecutiveFailures}`);
      console.log(`   Last error: ${data.lastError}`);
    });
    
    this.healthMonitor.on('high-error-rate', (data) => {
      console.log(`\n⚠️  High Error Rate - ${data.api}`);
      console.log(`   Error rate: ${(data.errorRate * 100).toFixed(2)}%`);
    });
    
    this.healthMonitor.on('slow-response', (data) => {
      console.log(`\n🐌 Slow Response - ${data.api}`);
      console.log(`   Response time: ${data.responseTime}ms (threshold: ${data.threshold}ms)`);
    });
  }
  
  async runComprehensiveDashboard() {
    console.log('╔═══════════════════════════════════════════════════════════╗');
    console.log('║     🚀 CRYPTO API INTEGRATION DASHBOARD                    ║');
    console.log('╚═══════════════════════════════════════════════════════════╝');
    console.log();
    
    // Phase 1: Run API Audit
    console.log('📊 PHASE 1: API KEY AUDIT');
    console.log('═'.repeat(60));
    
    const auditResults = await this.auditor.runFullAudit();
    
    // Phase 2: Initialize Secure Key Manager
    console.log('\n🔐 PHASE 2: SECURE KEY MANAGEMENT');
    console.log('═'.repeat(60));
    
    await this.keyManager.initializeFromEnv();
    const keyValidation = await this.keyManager.validateKeys();
    
    console.log('\nKey Validation Results:');
    for (const [service, keys] of Object.entries(keyValidation)) {
      console.log(`\n${service}:`);
      for (const [keyName, result] of Object.entries(keys)) {
        if (result.valid) {
          console.log(`  ✅ ${keyName} - Valid (${result.length} chars)`);
        } else {
          console.log(`  ❌ ${keyName} - Invalid: ${result.error}`);
        }
      }
    }
    
    // Phase 3: Start Health Monitoring
    console.log('\n🏥 PHASE 3: API HEALTH MONITORING');
    console.log('═'.repeat(60));
    
    // Define health check functions for each API
    const healthChecks = {
      coinbase: async () => {
        // Simplified health check - in production, use actual API call
        return { status: 'ok', timestamp: new Date().toISOString() };
      },
      coindesk: async () => {
        const fetch = require('node-fetch');
        const response = await fetch('https://api.coindesk.com/v1/bpi/currentprice.json');
        return { status: response.ok ? 'ok' : 'error', statusCode: response.status };
      },
      taapi: async () => {
        // Check if API key exists
        const key = process.env.TAAPI_API_KEY;
        if (!key) throw new Error('API key not configured');
        return { status: 'ok', hasKey: true };
      }
    };
    
    // Start monitoring critical APIs
    for (const [apiName, checkFn] of Object.entries(healthChecks)) {
      if (auditResults.keys[apiName]?.status === 'active' || 
          auditResults.keys[apiName]?.status === 'incomplete') {
        this.healthMonitor.startMonitoring(apiName, checkFn, 30000); // 30 second intervals
      }
    }
    
    // Phase 4: Generate Dashboard Report
    console.log('\n📈 PHASE 4: DASHBOARD REPORT');
    console.log('═'.repeat(60));
    
    await this.generateDashboardReport(auditResults, keyValidation);
    
    // Keep monitoring for 2 minutes then generate final report
    console.log('\n⏰ Monitoring APIs for 2 minutes...');
    console.log('   (Press Ctrl+C to stop)\n');
    
    setTimeout(async () => {
      console.log('\n📊 FINAL HEALTH REPORT');
      console.log('═'.repeat(60));
      
      const healthSummary = this.healthMonitor.getHealthSummary();
      console.log('\nAPI Health Summary:');
      console.log(`  ✅ Healthy: ${healthSummary.healthy}`);
      console.log(`  ⚠️  Degraded: ${healthSummary.degraded}`);
      console.log(`  🔥 Critical: ${healthSummary.critical}`);
      console.log(`  ❓ Unknown: ${healthSummary.unknown}`);
      
      // Stop monitoring
      this.healthMonitor.stopAllMonitoring();
      
      // Save final report
      await this.saveFinalReport(auditResults, healthSummary);
      
      console.log('\n✅ Dashboard execution complete!');
      process.exit(0);
    }, 120000); // 2 minutes
  }
  
  async generateDashboardReport(auditResults, keyValidation) {
    const report = {
      timestamp: new Date().toISOString(),
      audit: auditResults.summary,
      apis: {},
      recommendations: []
    };
    
    // Analyze each API
    for (const [apiName, result] of Object.entries(auditResults.keys)) {
      report.apis[apiName] = {
        status: result.status,
        missingKeys: result.missingKeys,
        errors: result.errors
      };
      
      // Generate recommendations
      if (result.status === 'incomplete') {
        report.recommendations.push({
          api: apiName,
          type: 'missing_keys',
          action: `Add missing keys: ${result.missingKeys.join(', ')}`
        });
      } else if (result.status === 'failed') {
        report.recommendations.push({
          api: apiName,
          type: 'connection_failed',
          action: 'Check API credentials and endpoint accessibility'
        });
      }
    }
    
    // Display recommendations
    if (report.recommendations.length > 0) {
      console.log('\n💡 RECOMMENDATIONS:');
      for (const rec of report.recommendations) {
        console.log(`\n  ${rec.api.toUpperCase()}:`);
        console.log(`    Action: ${rec.action}`);
      }
    }
    
    // Save report
    const reportPath = path.join(process.cwd(), 'dashboard-report.json');
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n📄 Report saved to: ${reportPath}`);
  }
  
  async saveFinalReport(auditResults, healthSummary) {
    const finalReport = {
      timestamp: new Date().toISOString(),
      duration: '2 minutes',
      auditSummary: auditResults.summary,
      healthSummary: healthSummary,
      detailedHealth: this.healthMonitor.getHealthStatus()
    };
    
    const reportPath = path.join(process.cwd(), 'final-health-report.json');
    await fs.writeFile(reportPath, JSON.stringify(finalReport, null, 2));
    console.log(`\n📄 Final health report saved to: ${reportPath}`);
  }
}

// Auto-run if executed directly
if (require.main === module) {
  require('dotenv').config({ path: path.join(__dirname, '.env') });
  
  const dashboard = new APIIntegrationDashboard();
  dashboard.runComprehensiveDashboard().catch(error => {
    console.error('❌ Dashboard error:', error);
    process.exit(1);
  });
}

module.exports = APIIntegrationDashboard; 