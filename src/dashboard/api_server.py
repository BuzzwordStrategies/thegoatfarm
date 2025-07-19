"""
Flask API Server for GOAT Farm Dashboard
Provides endpoints for bot status, API health, and risk management
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.base_api_connection import get_api_connection
from utils.db import init_db, get_params, set_param

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard

# Initialize database
init_db()

# Bot status cache
bot_status_cache = {
    'bot1': {'active': True, 'status': 'running', 'pl': 0},
    'bot2': {'active': True, 'status': 'running', 'pl': 0},
    'bot3': {'active': True, 'status': 'running', 'pl': 0},
    'bot4': {'active': True, 'status': 'running', 'pl': 0}
}

# API health cache
api_health_cache = {}

@app.route('/api/health')
def health_check():
    """General health check endpoint"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/bots/status')
def get_all_bots_status():
    """Get status of all bots"""
    try:
        # Get parameters from database
        bot_data = {}
        for bot_id in ['bot1', 'bot2', 'bot3', 'bot4']:
            params = get_params(bot_id)
            bot_data[bot_id] = {
                'active': params.get('active', '1') == '1',
                'risk': float(params.get('risk', '1.0')),
                'allocation': float(params.get('alloc', '25')),
                'frequency': int(params.get('freq', '60')),
                'status': bot_status_cache.get(bot_id, {}).get('status', 'stopped'),
                'pl': bot_status_cache.get(bot_id, {}).get('pl', 0),
                'last_trade': bot_status_cache.get(bot_id, {}).get('last_trade')
            }
        
        return jsonify({
            'success': True,
            'bots': bot_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bots/<bot_id>/performance')
def get_bot_performance(bot_id):
    """Get individual bot performance metrics"""
    try:
        # Connect to database
        conn = sqlite3.connect('data/app.db')
        cursor = conn.cursor()
        
        # Get recent trades
        cursor.execute("""
            SELECT timestamp, action, details 
            FROM logs 
            WHERE bot_id = ? AND action IN ('buy', 'sell')
            ORDER BY timestamp DESC
            LIMIT 50
        """, (bot_id,))
        
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'timestamp': row[0],
                'action': row[1],
                'details': row[2]
            })
        
        conn.close()
        
        # Calculate metrics
        params = get_params(bot_id)
        
        return jsonify({
            'success': True,
            'bot_id': bot_id,
            'metrics': {
                'total_trades': len(trades),
                'win_rate': 0,  # Calculate from trades
                'avg_profit': 0,  # Calculate from trades
                'max_drawdown': 0,  # Calculate from trades
                'sharpe_ratio': 0,  # Calculate from trades
                'current_pl': bot_status_cache.get(bot_id, {}).get('pl', 0)
            },
            'recent_trades': trades[:10],
            'parameters': {
                'risk': float(params.get('risk', '1.0')),
                'allocation': float(params.get('alloc', '25')),
                'frequency': int(params.get('freq', '60'))
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bots/<bot_id>/config', methods=['POST'])
def update_bot_config(bot_id):
    """Update bot risk parameters"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Update parameters
        if 'risk' in data:
            set_param(bot_id, 'risk', str(data['risk']))
        if 'allocation' in data:
            set_param(bot_id, 'alloc', str(data['allocation']))
        if 'frequency' in data:
            set_param(bot_id, 'freq', str(data['frequency']))
        if 'active' in data:
            set_param(bot_id, 'active', '1' if data['active'] else '0')
            
        return jsonify({
            'success': True,
            'message': f'Configuration updated for {bot_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bots/<bot_id>/allocation', methods=['POST'])
def update_bot_allocation(bot_id):
    """Update bot allocation percentage"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        new_allocation = data.get('allocation')
        
        if new_allocation is None:
            return jsonify({
                'success': False,
                'error': 'Allocation value required'
            }), 400
            
        # Ensure total allocation doesn't exceed 100%
        total = 0
        for bid in ['bot1', 'bot2', 'bot3', 'bot4']:
            if bid == bot_id:
                total += new_allocation
            else:
                params = get_params(bid)
                total += float(params.get('alloc', '25'))
                
        if total > 100:
            return jsonify({
                'success': False,
                'error': f'Total allocation would be {total}%, must not exceed 100%'
            }), 400
            
        set_param(bot_id, 'alloc', str(new_allocation))
        
        return jsonify({
            'success': True,
            'message': f'Allocation updated to {new_allocation}%'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/overview')
def get_portfolio_overview():
    """Get combined portfolio P&L and statistics"""
    try:
        total_pl = sum(bot_status_cache.get(f'bot{i}', {}).get('pl', 0) for i in range(1, 5))
        
        # Get allocations
        allocations = {}
        for bot_id in ['bot1', 'bot2', 'bot3', 'bot4']:
            params = get_params(bot_id)
            allocations[bot_id] = float(params.get('alloc', '25'))
            
        return jsonify({
            'success': True,
            'portfolio': {
                'total_pl': total_pl,
                'total_value': 10000 + total_pl,  # Starting capital + P&L
                'allocations': allocations,
                'daily_return': 0,  # Calculate from trades
                'weekly_return': 0,  # Calculate from trades
                'monthly_return': 0  # Calculate from trades
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API Health Endpoints
@app.route('/api/health/<api_name>')
def check_api_health(api_name):
    """Check health of specific API"""
    try:
        # Use cached status if recent (within 10 seconds)
        cache_key = f"{api_name}_health"
        cached = api_health_cache.get(cache_key)
        
        if cached and (datetime.now() - cached['timestamp']).total_seconds() < 10:
            return jsonify(cached['data'])
            
        # Check actual API status
        status = {'status': 'offline', 'error': None}
        
        if api_name == 'coinbase':
            conn = get_api_connection('COINBASE')
            if conn.is_connected:
                status = {'status': 'online'}
                
        elif api_name == 'taapi':
            conn = get_api_connection('TAAPI')
            if conn.is_connected:
                status = {'status': 'online'}
                
        elif api_name == 'twitter':
            conn = get_api_connection('TWITTER')
            if conn.is_connected:
                status = {'status': 'online'}
                
        elif api_name == 'scrapingbee':
            if os.getenv('SCRAPINGBEE_API_KEY'):
                status = {'status': 'online'}
                
        elif api_name == 'anthropic':
            if os.getenv('ANTHROPIC_API_KEY'):
                status = {'status': 'online'}
                
        elif api_name == 'perplexity':
            if os.getenv('PERPLEXITY_API_KEY'):
                status = {'status': 'online'}
                
        elif api_name == 'grok':
            if os.getenv('XAI_API_KEY'):
                status = {'status': 'online'}
                
        elif api_name == 'coindesk':
            # CoinDesk is free API, always online
            status = {'status': 'online'}
            
        # Cache the result
        api_health_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': status
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'status': 'offline',
            'error': str(e)
        })

@app.route('/api/reconnect/<api_name>', methods=['POST'])
def reconnect_api(api_name):
    """Attempt to reconnect to an API"""
    try:
        # Clear cache
        cache_key = f"{api_name}_health"
        if cache_key in api_health_cache:
            del api_health_cache[cache_key]
            
        # In a real implementation, we would restart the connection
        # For now, just return success
        return jsonify({
            'success': True,
            'message': f'Reconnection attempted for {api_name}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# WebSocket data endpoint (for real-time updates)
@app.route('/api/ws/data')
def get_websocket_data():
    """Get latest WebSocket data"""
    try:
        # In production, this would return actual WebSocket data
        return jsonify({
            'success': True,
            'data': {
                'prices': {
                    'BTC/USD': 43250.50,
                    'ETH/USD': 2350.75,
                    'SOL/USD': 98.30
                },
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 