# Quick Start Guide - API Integration Audit System

## 🚀 Run the Complete API Audit Dashboard

Follow these simple steps to audit and monitor your crypto API integrations:

### Step 1: Export Python Environment (First Time Only)
```bash
python src/export_env_for_audit.py
```
This exports your existing API keys from the Python environment.

### Step 2: Run the Dashboard
```bash
npm run dashboard
```

This will:
- ✅ Audit all API keys and test connections
- 🔐 Securely encrypt and store your keys
- 🏥 Start real-time health monitoring
- 📊 Generate comprehensive reports

### Step 3: Check Results

After running, you'll find:
- `audit-results.json` - Complete audit details
- `dashboard-report.json` - Summary and recommendations
- `final-health-report.json` - 2-minute health monitoring results

## Alternative Commands

### Just Run API Audit
```bash
npm run audit
```

### View Current Python API Keys
```bash
python test_env_keys.py
```

## Troubleshooting

If you see "API key not found":
1. Make sure your Python environment has the keys configured
2. Run `python src/export_env_for_audit.py` again
3. Check that `src/.env` file was created

## What the Dashboard Shows

- 🟢 **Active APIs**: Working perfectly
- 🟡 **Incomplete APIs**: Missing some keys
- 🔴 **Failed APIs**: Connection issues
- ⚫ **Critical APIs**: Multiple consecutive failures

The system will monitor for 2 minutes and then generate a final report with recommendations.

Press `Ctrl+C` to stop monitoring early. 