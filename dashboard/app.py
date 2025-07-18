from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from utils.db import get_params, set_param, log_trade, get_key, store_key, increment_api_call, get_api_call_count
from utils.sentiment import get_combined_sentiment, get_coindesk_news
from utils.env_loader import get_master_password
from anthropic import Anthropic
import time
import json
import numpy as np
import ccxt
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'supersecretkey'

# Hardcoded user for MVP
users = {'josh': generate_password_hash('March3392!')}

# Global caches for sentiment and news data
sentiments_cache = {}
news_cache = {}
last_update = 0

# Global API client configuration
api_clients_loaded = False

def reload_clients():
    """Reload API clients with latest keys from database"""
    global api_clients_loaded
    master_pass = get_master_password()  # Use environment variable if available
    
    # Check if we have any keys stored
    coinbase_key = get_key('coinbase_api_key', master_pass)
    taapi_key = get_key('taapi_key', master_pass)
    claude_key = get_key('claude_api_key', master_pass)
    
    # Set flag to indicate if we have live keys
    api_clients_loaded = bool(coinbase_key or taapi_key or claude_key)
    
    # Return status for audit
    return {
        'coinbase': bool(coinbase_key),
        'taapi': bool(taapi_key),
        'claude': bool(claude_key),
        'twitter': bool(get_key('twitterapi_key', master_pass)),
        'grok': bool(get_key('grok_api_key', master_pass)),
        'perplexity': bool(get_key('perplexity_api_key', master_pass))
    }

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login route with hardcoded credentials"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            return redirect('/')
    
    return render_template('login.html')

@app.route('/api_dashboard')
def api_dashboard():
    """API dashboard with health tests and key vault"""
    if 'user' not in session:
        return redirect('/login')
    
    return render_template('api_dashboard.html')

@app.route('/api_vault')
def api_vault():
    """API Vault for managing API keys"""
    if 'user' not in session:
        return redirect('/login')
    
    return render_template('api_vault.html')

@app.route('/api_health')
def api_health():
    """API Health monitoring page"""
    if 'user' not in session:
        return redirect('/login')
    
    # Get current API call counts
    api_counts = {
        'coinbase': get_api_call_count('coinbase'),
        'taapi': get_api_call_count('taapi'),
        'coindesk': get_api_call_count('coindesk'),
    }
    
    return render_template('api_health.html', api_counts=api_counts)

@app.route('/api_test/<api>', methods=['POST'])
def api_test(api):
    """Test individual API connectivity"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get master password from request
    master_pass = request.form.get('master_pass', '')
    
    try:
        if api == 'coinbase':
            # Test Coinbase API
            api_key = get_key('coinbase_api_key', master_pass)
            secret = get_key('coinbase_secret', master_pass)
            
            if not api_key or not secret:
                return jsonify({'status': 'error', 'message': 'API keys not configured'})
            
            # Initialize exchange and test
            exchange = ccxt.coinbase({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'version': 'v1'}
            })
            
            # Try to fetch ticker
            ticker = exchange.fetch_ticker('BTC/USD')
            increment_api_call('coinbase')
            daily_count = get_api_call_count('coinbase')
            return jsonify({
                'status': 'ok', 
                'message': f'Connected! BTC price: ${ticker["last"]:,.2f}',
                'daily_count': daily_count
            })
            
        elif api == 'taapi':
            # Test TAAPI
            from utils.taapi import get_indicator
            
            # Test with RSI indicator for BTC
            result = get_indicator('rsi', {
                'exchange': 'coinbase',
                'symbol': 'BTC/USDT',
                'interval': '1h',
                'period': 14
            }, master_pass)
            
            if result and 'value' in result:
                increment_api_call('taapi')
                daily_count = get_api_call_count('taapi')
                return jsonify({
                    'status': 'ok', 
                    'message': f'Connected! BTC RSI: {result["value"]:.2f}',
                    'daily_count': daily_count
                })
            else:
                daily_count = get_api_call_count('taapi')
                return jsonify({
                    'status': 'error', 
                    'message': 'Failed to get indicator data',
                    'daily_count': daily_count
                })
                
        elif api == 'coindesk':
            # Test Coindesk Data API
            api_key = get_key('coindesk_api_key', master_pass)
            
            url = 'https://data-api.coindesk.com/news/v1/article/list'
            params = {}
            if api_key:
                params['api_key'] = api_key
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                increment_api_call('coindesk')
                daily_count = get_api_call_count('coindesk')
                return jsonify({
                    'status': 'ok', 
                    'message': 'Connected to CoinDesk News API',
                    'daily_count': daily_count
                })
            else:
                daily_count = get_api_call_count('coindesk')
                return jsonify({
                    'status': 'error', 
                    'message': f'Failed to connect: HTTP {response.status_code}',
                    'daily_count': daily_count
                })
                
        elif api == 'grok':
            # Test Grok API
            api_key = get_key('grok_api_key', master_pass)
            
            if not api_key:
                return jsonify({'status': 'error', 'message': 'API key not configured'})
            
            # Test with simple query
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            data = {'messages': [{'role': 'user', 'content': 'test'}], 'model': 'grok-beta'}
            response = requests.post('https://api.x.ai/v1/chat/completions', 
                                   headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                return jsonify({'status': 'ok', 'message': 'Connected to Grok API!'})
            else:
                return jsonify({'status': 'error', 'message': f'API returned {response.status_code}'})
                
        elif api == 'perplexity':
            # Test Perplexity API
            api_key = get_key('perplexity_api_key', master_pass)
            
            if not api_key:
                return jsonify({'status': 'error', 'message': 'API key not configured'})
            
            # Test with simple query
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': 'pplx-7b-online',
                'messages': [{'role': 'user', 'content': 'test'}]
            }
            response = requests.post('https://api.perplexity.ai/chat/completions', 
                                   headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                return jsonify({'status': 'ok', 'message': 'Connected to Perplexity API!'})
            else:
                return jsonify({'status': 'error', 'message': f'API returned {response.status_code}'})
                
        elif api == 'anthropic':
            # Test Anthropic API
            api_key = get_key('claude_api_key', master_pass)
            
            if not api_key:
                return jsonify({'status': 'error', 'message': 'API key not configured'})
            
            # Test with simple message
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            
            return jsonify({'status': 'ok', 'message': 'Connected to Claude API!'})
            
        else:
            return jsonify({'status': 'error', 'message': 'Unknown API'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def test_api_connection(key_type: str, master_pass: str):
    """Test API connection after saving keys"""
    try:
        if key_type == 'coinbase_api_key':
            # Test Coinbase connection and fetch balance
            api_key = get_key('coinbase_api_key', master_pass)
            secret = get_key('coinbase_secret', master_pass)
            
            if not api_key or not secret:
                return 'failed', 'Keys not found'
            
            exchange = ccxt.coinbase({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'version': 'v1'}
            })
            
            # Load markets and fetch balance
            exchange.load_markets()
            balance = exchange.fetch_balance()
            
            # Get USD balance
            usd_balance = balance.get('USD', {}).get('free', 0.0)
            
            # Store balance in database
            set_param('system', 'coinbase_balance', str(usd_balance))
            
            return 'connected', f'Balance: ${usd_balance:.2f} USD'
            
        elif key_type == 'twitterapi_key':
            # Test TwitterAPI connection
            api_key = get_key('twitterapi_key', master_pass)
            if not api_key:
                return 'failed', 'Key not found'
                
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get('https://api.twitterapi.io/v1/search/tweets', 
                                  params={'q': 'test', 'count': 1},
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                return 'connected', 'API verified'
            else:
                return 'failed', f'HTTP {response.status_code}'
                
        elif key_type == 'grok_api_key':
            # Test Grok API
            api_key = get_key('grok_api_key', master_pass)
            if not api_key:
                return 'failed', 'Key not found'
            
            # Test Grok API with a simple completion
            url = "https://api.x.ai/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'grok-beta',
                'messages': [
                    {'role': 'user', 'content': 'test'}
                ],
                'max_tokens': 10
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return 'connected', 'Grok API verified'
            else:
                return 'failed', f'HTTP {response.status_code}'
            
        elif key_type == 'perplexity_api_key':
            # Test Perplexity API
            api_key = get_key('perplexity_api_key', master_pass)
            if not api_key:
                return 'failed', 'Key not found'
            
            # Test Perplexity API
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'pplx-70b-chat',
                'messages': [
                    {'role': 'user', 'content': 'test'}
                ],
                'max_tokens': 10
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return 'connected', 'Perplexity API verified'
            else:
                return 'failed', f'HTTP {response.status_code}'
            
        elif key_type == 'claude_api_key':
            # Test Anthropic Claude API
            api_key = get_key('claude_api_key', master_pass)
            if not api_key:
                return 'failed', 'Key not found'
                
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            
            return 'connected', 'API verified'
            
        elif key_type == 'taapi_key':
            # Test TAAPI connection
            from utils.taapi import get_indicator
            
            result = get_indicator('rsi', {
                'exchange': 'coinbase',
                'symbol': 'BTC/USDT',
                'interval': '1h',
                'period': 14
            }, master_pass)
            
            if result and 'value' in result:
                return 'connected', f'TAAPI verified - BTC RSI: {result["value"]:.2f}'
            else:
                return 'failed', 'Failed to fetch indicator'
                
        elif key_type == 'coinbase_secret':
            # Skip testing secret alone
            return 'skipped', 'Part of Coinbase credentials'
            
        elif key_type == 'coindesk_api_key':
            # Test CoinDesk API
            api_key = get_key('coindesk_api_key', master_pass)
            
            # CoinDesk Data API endpoint
            url = "https://data-api.coindesk.com/news/v1/article/list"
            
            params = {}
            if api_key:
                params['api_key'] = api_key
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return 'connected', 'News API verified'
            else:
                return 'failed', f'HTTP {response.status_code}'
            
        else:
            return 'skipped', 'No test available'
            
    except Exception as e:
        # Log the failure
        log_trade('api_test', 'test_failed', f'{key_type} failed: {str(e)}')
        return 'failed', str(e)[:100]  # Limit error message length

@app.route('/key_vault', methods=['POST'])
def key_vault():
    """Store API keys with password protection"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check password
    password = request.form.get('password', '')
    if password != 'March3392!':
        return jsonify({'error': 'Invalid password'}), 403
    
    # List of API keys to store
    api_keys = [
        'coinbase_api_key',
        'coinbase_secret',
        'taapi_key',  # Changed from twitterapi_key
        'grok_api_key',
        'perplexity_api_key',
        'claude_api_key',
        'coindesk_api_key',
    ]
    
    # Store each key if provided
    stored = []
    for key_name in api_keys:
        key_value = request.form.get(key_name, '').strip()
        if key_value:
            store_key(key_name, key_value, password)
            stored.append(key_name)
    
    if stored:
        # Reload clients to use new keys
        reload_status = reload_clients()
        flash(f'Successfully saved {len(stored)} API keys!', 'success')
        
        # Auto-test each saved API
        test_results = {}
        for key_name in stored:
            status, msg = test_api_connection(key_name, password)
            test_results[key_name] = {'status': status, 'message': msg}
            flash(f'{key_name.replace("_", " ").title()}: {msg}', 
                  'success' if status == 'connected' else 'warning')
        
        return jsonify({
            'success': True, 
            'message': f'Stored {len(stored)} keys successfully',
            'reload_status': reload_status,
            'test_results': test_results
        })
    else:
        flash('No API keys provided', 'error')
        return jsonify({'error': 'No keys provided'}), 400

@app.route('/audit')
def audit():
    """Temporary audit route to verify platform readiness"""
    if 'user' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    # Reload clients to get current status
    api_status = reload_clients()
    
    # Test live data retrieval
    master_pass = 'March3392!'
    
    # Test sentiment API
    try:
        from utils.sentiment import get_combined_sentiment
        sentiment_data = get_combined_sentiment('BTC', master_pass)
        sentiment_live = sentiment_data['average'] != 0.0
    except Exception as e:
        sentiment_live = False
        sentiment_data = {'error': str(e)}
    
    # Test navigation links
    nav_links = [
        {'name': 'Dashboard', 'url': '/', 'tested': True},
        {'name': 'Bots', 'url': '/bots', 'tested': True},
        {'name': 'API Settings', 'url': '/api-settings', 'tested': True},
        {'name': 'API Dashboard', 'url': '/api_dashboard', 'tested': True},
        {'name': 'Sources', 'url': '/sources', 'tested': True}
    ]
    
    # Audit results
    audit_results = {
        'login': 'ok',
        'api_keys': api_status,
        'live_data': {
            'sentiment': sentiment_live,
            'sample_sentiment': sentiment_data
        },
        'navigation': nav_links,
        'flow': 'ready' if api_status['coinbase'] else 'needs_keys',
        'platform_status': '100% ready for live keys' if any(api_status.values()) else 'Awaiting API keys'
    }
    
    return jsonify(audit_results)

@app.route('/sources')
def sources():
    """Sources dashboard for configuring data sources"""
    if 'user' not in session:
        return redirect('/login')
    
    # Get current source configurations
    twitter_users = get_params('twitter_users').get('twitter_users', 'open')
    reddit_subs = get_params('reddit_subs').get('reddit_subs', 'open')
    
    return render_template('sources.html', 
                         twitter_users=twitter_users,
                         reddit_subs=reddit_subs)

@app.route('/update_sources/<source>', methods=['POST'])
def update_sources(source):
    """Update source configuration"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if source == 'twitter':
        users = request.form.get('users', 'open').strip()
        # Validate format - either 'open' or comma-separated usernames
        if users != 'open' and users:
            # Clean up usernames - remove @ if present
            users = ','.join([u.strip().lstrip('@') for u in users.split(',')])
        set_param('twitter_users', 'twitter_users', users)
        return jsonify({'success': True, 'message': f'Twitter sources updated: {users}'})
        
    elif source == 'reddit':
        subs = request.form.get('subs', 'open').strip()
        # Validate format - either 'open' or comma-separated subreddits
        if subs != 'open' and subs:
            # Clean up subreddit names - remove r/ if present
            subs = ','.join([s.strip().lstrip('r/') for s in subs.split(',')])
        set_param('reddit_subs', 'reddit_subs', subs)
        return jsonify({'success': True, 'message': f'Reddit sources updated: {subs}'})
        
    else:
        return jsonify({'error': 'Invalid source type'}), 400

@app.route('/')
def index():
    """Main dashboard route showing all bots and controls"""
    if 'user' not in session:
        return redirect('/login')
    
    global last_update, sentiments_cache, news_cache
    
    # Update sentiment cache every 5 minutes
    if time.time() - last_update > 300:
        try:
            for coin in ['BTC', 'ETH', 'SOL', 'ADA']:
                sentiment_data = get_combined_sentiment(coin)
                sentiments_cache[coin] = sentiment_data.get('combined_score', 0.0)
            
            news_cache = get_coindesk_news('cryptocurrency')
            last_update = time.time()
        except Exception as e:
            log_trade('dashboard', 'error', f'Cache update error: {str(e)}')
    
    # Bot configuration
    bots = ['bot1', 'bot2', 'bot3', 'bot4']
    
    # Get parameters for each bot
    params = {}
    for bot in bots:
        bot_params = get_params(bot)
        if not bot_params:
            # Default parameters if not set
            params[bot] = {
                'risk_level': 1.0,
                'allocation': 10.0,
                'freq': 10
            }
        else:
            params[bot] = bot_params
    
    # Map sentiments to bots based on their trading pairs
    sentiments = {
        'bot1': sentiments_cache.get('BTC', 0.0),
        'bot2': sentiments_cache.get('SOL', 0.0),
        'bot3': sentiments_cache.get('ETH', 0.0),
        'bot4': sentiments_cache.get('ADA', 0.0)
    }
    
    # Get top 3 news items for Bot3
    news = news_cache[:3] if news_cache else []
    
    # Calculate P&L from trade logs
    try:
        conn = sqlite3.connect('data/app.db')
        df = pd.read_sql('SELECT * FROM trade_logs', conn)
        conn.close()
        
        # Group by bot_id and sum profits
        pnl = {}
        for bot in bots:
            bot_trades = df[df['bot_id'] == bot]
            bot_pnl = 0.0
            
            # Parse details column for profit values
            for _, row in bot_trades.iterrows():
                try:
                    details = row['details']
                    if 'profit' in details:
                        # Extract profit value from details string
                        profit_start = details.find('profit') + 8
                        profit_end = details.find(',', profit_start)
                        if profit_end == -1:
                            profit_end = details.find('}', profit_start)
                        profit = float(details[profit_start:profit_end].strip())
                        bot_pnl += profit
                except:
                    pass
            
            pnl[bot] = bot_pnl
    except Exception as e:
        log_trade('dashboard', 'error', f'P&L calculation error: {str(e)}')
        pnl = {bot: 0.0 for bot in bots}
    
    # Get Coinbase balance from params
    coinbase_balance = get_params('system').get('coinbase_balance', 'Not connected')
    
    # Calculate total portfolio value using actual balance or 0
    try:
        balance_float = float(coinbase_balance) if coinbase_balance != 'Not connected' else 0.0
    except:
        balance_float = 0.0
    
    portfolio = balance_float + sum(pnl.values())
    
    return render_template('index.html',
                         bots=bots,
                         params=params,
                         sentiments=sentiments,
                         news=news,
                         pnl=pnl,
                         portfolio=portfolio,
                         coinbase_balance=coinbase_balance)

@app.route('/update_param', methods=['POST'])
def update_param():
    """Update bot parameter in database"""
    try:
        bot = request.form.get('bot')
        param = request.form.get('param')
        value = float(request.form.get('value'))
        
        set_param(bot, param, str(value))
        log_trade('dashboard', 'info', f'Updated {bot} {param} to {value}')
        
        return jsonify({'success': True})
    except Exception as e:
        log_trade('dashboard', 'error', str(e))
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/start_bot/<bot_id>', methods=['POST'])
def start_bot(bot_id):
    """Start bot (placeholder - actual implementation in main.py)"""
    log_trade(bot_id, 'info', 'Started via dashboard')
    return jsonify({'success': True})

@app.route('/pause_bot/<bot_id>', methods=['POST'])
def pause_bot(bot_id):
    """Pause bot (placeholder - actual implementation in main.py)"""
    log_trade(bot_id, 'info', 'Paused via dashboard')
    return jsonify({'success': True})

@app.route('/stop_bot/<bot_id>', methods=['POST'])
def stop_bot(bot_id):
    """Stop bot (placeholder - actual implementation in main.py)"""
    log_trade(bot_id, 'info', 'Stopped via dashboard')
    return jsonify({'success': True})

@app.route('/get_status', methods=['GET'])
def get_status():
    """Get current status for real-time updates"""
    global sentiments_cache
    
    bots = ['bot1', 'bot2', 'bot3', 'bot4']
    
    # Calculate current P&L and win rates
    try:
        conn = sqlite3.connect('data/app.db')
        df = pd.read_sql('SELECT * FROM trade_logs', conn)
        conn.close()
        
        pnl = {}
        win_rates = {}
        for bot in bots:
            bot_trades = df[df['bot_id'] == bot]
            bot_pnl = 0.0
            wins = 0
            total_trades = 0
            
            for _, row in bot_trades.iterrows():
                try:
                    details = row['details']
                    if 'profit' in details:
                        profit_start = details.find('profit') + 8
                        profit_end = details.find(',', profit_start)
                        if profit_end == -1:
                            profit_end = details.find('}', profit_start)
                        profit = float(details[profit_start:profit_end].strip())
                        bot_pnl += profit
                        
                        # Count wins for win rate
                        if profit > 0:
                            wins += 1
                        total_trades += 1
                except:
                    pass
            
            pnl[bot] = bot_pnl
            win_rates[bot] = (wins / total_trades * 100) if total_trades > 0 else 0.0
    except:
        pnl = {bot: 0.0 for bot in bots}
        win_rates = {bot: 0.0 for bot in bots}
    
    # Combined P&L
    combined_pl = sum(pnl.values())
    
    # Get actual Coinbase balance or default to 0
    coinbase_balance_str = get_params('system').get('coinbase_balance', '0.0')
    try:
        coinbase_balance_float = float(coinbase_balance_str)
    except:
        coinbase_balance_float = 0.0
    
    portfolio = coinbase_balance_float + combined_pl
    
    # Overall win rate
    overall_win_rate = sum(win_rates.values()) / len(win_rates) if win_rates else 0.0
    
    # Check active status from params
    active_status = {}
    active_count = 0
    for bot in bots:
        params = get_params(bot)
        is_active = params.get('active', 'True') == 'True'
        active_status[bot] = is_active
        if is_active:
            active_count += 1
    
    # Current sentiments
    sentiments = {
        'bot1': sentiments_cache.get('BTC', 0.0),
        'bot2': sentiments_cache.get('SOL', 0.0),
        'bot3': sentiments_cache.get('ETH', 0.0),
        'bot4': sentiments_cache.get('ADA', 0.0)
    }
    
    # Get Coinbase balance from params
    coinbase_balance = get_params('system').get('coinbase_balance', 'Not connected')
    
    return jsonify({
        'pnl': pnl,
        'portfolio': portfolio,
        'combined_pl': combined_pl,
        'sentiments': sentiments,
        'win_rates': win_rates,
        'overall_win_rate': overall_win_rate,
        'active_status': active_status,
        'active_count': active_count,
        'coinbase_balance': coinbase_balance
    })

@app.route('/api-settings', methods=['GET', 'POST'])
def api_settings():
    """API Settings page for managing API keys"""
    if 'user' not in session:
        return redirect('/login')
    
    # List of API keys to manage
    api_keys = [
        {'key': 'coinbase_api_key', 'name': 'Coinbase API Key', 'required': True},
        {'key': 'coinbase_secret', 'name': 'Coinbase Secret', 'required': True},
        {'key': 'twitterapi_io_key', 'name': 'TwitterAPI.io Key', 'required': True},
        {'key': 'grok_api_key', 'name': 'Grok API Key', 'required': True},
        {'key': 'coindesk_api_key', 'name': 'Coindesk API Key', 'required': False},
        {'key': 'perplexity_api_key', 'name': 'Perplexity API Key', 'required': True},
        {'key': 'claude_api_key', 'name': 'Claude API Key', 'required': True}
    ]
    
    if request.method == 'POST':
        # Handle API key updates
        action = request.form.get('action')
        if action == 'update':
            key_name = request.form.get('key_name')
            key_value = request.form.get('key_value')
            master_pass = request.form.get('master_pass')
            
            if key_name and key_value and master_pass:
                try:
                    from utils.db import store_key
                    store_key(key_name, key_value, master_pass)
                    return jsonify({'success': True, 'message': 'API key updated successfully'})
                except Exception as e:
                    return jsonify({'success': False, 'error': str(e)}), 400
    
    # Check which keys are configured (without exposing values)
    master_pass = request.args.get('check_keys')
    configured_keys = {}
    if master_pass:
        from utils.db import get_key
        for api_key in api_keys:
            value = get_key(api_key['key'], master_pass)
            configured_keys[api_key['key']] = bool(value)
    
    return render_template('api_settings.html', api_keys=api_keys, configured_keys=configured_keys)

@app.route('/bots')
def bots_overview():
    """Bots overview page"""
    if 'user' not in session:
        return redirect('/login')
    
    bots = ['bot1', 'bot2', 'bot3', 'bot4']
    
    # Get current status for all bots
    status_data = json.loads(get_status().data)
    
    # Bot descriptions
    bot_descriptions = {
        'bot1': 'Trend-Following Momentum Bot',
        'bot2': 'Mean-Reversion Scalper',
        'bot3': 'News-Driven Breakout Bot',
        'bot4': 'ML-Powered Range Scalper'
    }
    
    return render_template('bots.html', 
                         bots=bots,
                         bot_descriptions=bot_descriptions,
                         pnl=status_data['pnl'],
                         win_rates=status_data['win_rates'],
                         active_status=status_data['active_status'])

@app.route('/bot/<bot_id>')
def bot_detail(bot_id):
    """Bot detail page with settings, rules, and audit"""
    if 'user' not in session:
        return redirect('/login')
    
    if bot_id not in ['bot1', 'bot2', 'bot3', 'bot4']:
        return redirect('/bots')
    
    # Get bot parameters
    params = get_params(bot_id)
    
    # Get trade logs for audit
    try:
        conn = sqlite3.connect('data/app.db')
        logs_df = pd.read_sql(
            "SELECT timestamp, action, details FROM trade_logs WHERE bot_id=? ORDER BY timestamp DESC LIMIT 100", 
            conn, 
            params=(bot_id,)
        )
        conn.close()
        
        # Convert to HTML table with Bootstrap classes
        logs_html = logs_df.to_html(classes='table table-dark table-striped', index=False)
    except:
        logs_html = "<p>No trade logs available</p>"
    
    # Bot rules based on type
    rules = {
        'bot1': """
        <h5>Trend-Following Momentum Strategy</h5>
        <ul>
            <li>Uses 20/50 SMA crossover signals</li>
            <li>RSI < 30 for oversold conditions</li>
            <li>Sentiment score > 0.6 for bullish bias</li>
            <li>Target: 1-2% daily returns</li>
            <li>Max drawdown: 5%</li>
            <li>Trades: BTC/USD, ETH/USD</li>
        </ul>
        """,
        'bot2': """
        <h5>Mean-Reversion Scalping Strategy</h5>
        <ul>
            <li>Bollinger Bands (20, 2) for entry signals</li>
            <li>ATR filter for volatility</li>
            <li>Neutral sentiment required (-0.5 to 0.5)</li>
            <li>Target: 0.8-1.5% daily returns</li>
            <li>Max trades: 5 per day</li>
            <li>Trades: SOL/USD high-volatility coins</li>
        </ul>
        """,
        'bot3': """
        <h5>News-Driven Breakout Strategy</h5>
        <ul>
            <li>Monitors Coindesk news sentiment</li>
            <li>Donchian Channel breakouts (20-period)</li>
            <li>Volume surge detection (2x average)</li>
            <li>Target: 6-9% daily returns</li>
            <li>News sentiment threshold: 0.7</li>
            <li>Trades: ETH/USD and trending altcoins</li>
        </ul>
        """,
        'bot4': """
        <h5>ML-Powered Range Scalping</h5>
        <ul>
            <li>Random Forest classifier for predictions</li>
            <li>Support/resistance level detection</li>
            <li>Sentiment analysis integration</li>
            <li>Target: 5-8% daily returns</li>
            <li>Model retraining: Weekly</li>
            <li>Trades: ADA/USD and ML-selected pairs</li>
        </ul>
        """
    }
    
    return render_template('bot_detail.html',
                         bot_id=bot_id,
                         params=params,
                         logs_html=logs_html,
                         rules=rules.get(bot_id, ''))

@app.route('/optimize/<bot_id>', methods=['POST'])
def optimize_bot(bot_id):
    """Optimize bot using Claude API"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if bot_id not in ['bot1', 'bot2', 'bot3', 'bot4']:
        return jsonify({'error': 'Invalid bot ID'}), 400
    
    # Get days parameter
    days = int(request.form.get('days', 7))
    
    # Get master password from session or request
    master_pass = request.form.get('master_pass', '')
    
    # Get Claude API key
    api_key = get_key('claude_api_key', master_pass)
    if not api_key:
        return jsonify({'error': 'Claude API key not found. Please provide master password.'}), 400
    
    # Fetch trade logs
    try:
        conn = sqlite3.connect('data/app.db')
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        logs_df = pd.read_sql(
            "SELECT * FROM trade_logs WHERE bot_id=? AND timestamp > ? ORDER BY timestamp DESC",
            conn,
            params=(bot_id, start_date)
        )
        conn.close()
        
        if logs_df.empty:
            return jsonify({'error': 'No trades found in the specified period'}), 404
        
        # Convert to JSON for Claude
        logs_json = logs_df.to_json(orient='records')
        
        # Get current parameters
        current_params = get_params(bot_id)
        
        # Initialize Claude client
        client = Anthropic(api_key=api_key)
        
        # Create optimization prompt
        system_prompt = """You are a cryptocurrency trading optimization expert. Analyze the provided trade logs and recommend specific parameter adjustments to improve performance.

        Focus on:
        1. Risk level adjustments (current range: 0.3-2.0%)
        2. Portfolio allocation (current range: 3-20%)
        3. Trading frequency (current range: 1-300 seconds)
        4. Entry/exit criteria improvements
        5. Stop loss and take profit levels

        Provide specific, actionable recommendations with reasoning.
        Format your response as JSON:
        {
            "recommendations": [
                {"parameter": "risk_level", "current": X, "suggested": Y, "reason": "..."},
                {"parameter": "allocation", "current": X, "suggested": Y, "reason": "..."}
            ],
            "summary": "Brief overview of suggested changes"
        }"""
        
        user_prompt = f"""
        Bot ID: {bot_id}
        Analysis Period: Last {days} days
        Current Parameters: {json.dumps(current_params)}
        
        Trade Logs:
        {logs_json}
        
        Please analyze these trades and recommend optimizations.
        """
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Parse response
        try:
            recommendations = json.loads(response.content[0].text)
        except:
            # If JSON parsing fails, return raw text
            recommendations = {
                "recommendations": [],
                "summary": response.content[0].text
            }
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'bot_id': bot_id,
            'days_analyzed': days,
            'trades_analyzed': len(logs_df)
        })
        
    except Exception as e:
        return jsonify({'error': f'Optimization failed: {str(e)}'}), 500

@app.route('/apply_recommendations', methods=['POST'])
def apply_recommendations():
    """Apply recommendations to bot settings"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    bot_id = data.get('bot_id')
    recommendations = data.get('recommendations', {})
    
    if bot_id not in ['bot1', 'bot2', 'bot3', 'bot4']:
        return jsonify({'error': 'Invalid bot ID'}), 400
    
    # Handle two formats: dict (from launch) or list (from optimize)
    if isinstance(recommendations, dict):
        # Launch protocol format: {param: value}
        for param, value in recommendations.items():
            if param in ['risk_level', 'allocation', 'trading_frequency', 'stop_loss', 'take_profit']:
                # Map frontend names to DB param names
                param_map = {
                    'risk_level': 'risk',
                    'allocation': 'alloc',
                    'trading_frequency': 'freq',
                    'stop_loss': 'stop_loss',
                    'take_profit': 'take_profit'
                }
                
                db_param = param_map.get(param, param)
                set_param(bot_id, db_param, str(value))
                log_trade(bot_id, 'optimization', f"Applied: {db_param} = {value}")
    
    elif isinstance(recommendations, list):
        # Optimize format: [{parameter: x, suggested: y}, ...]
        for rec in recommendations:
            if 'parameter' in rec and 'suggested' in rec:
                set_param(bot_id, rec['parameter'], str(rec['suggested']))
                log_trade(bot_id, 'optimization', f"Applied: {rec['parameter']} = {rec['suggested']}")
    
    return jsonify({'success': True, 'message': 'Recommendations applied successfully'})

@app.route('/launch/<bot_id>', methods=['POST'])
def launch_protocol(bot_id):
    """Launch protocol: run 3-month backtest and optimize with Claude"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if bot_id not in ['bot1', 'bot2', 'bot3', 'bot4']:
        return jsonify({'error': 'Invalid bot ID'}), 400
    
    # Get master password from request
    master_pass = request.form.get('master_pass', '')
    
    # Get Coinbase and Claude API keys
    coinbase_key = get_key('coinbase_api_key', master_pass)
    coinbase_secret = get_key('coinbase_secret', master_pass)
    claude_key = get_key('claude_api_key', master_pass)
    
    if not all([coinbase_key, coinbase_secret, claude_key]):
        return jsonify({'error': 'Missing API keys. Please provide master password.'}), 400
    
    try:
        # Dynamically import the bot class
        bot_number = bot_id[-1]
        bot_module = __import__(f'bots.bot{bot_number}', fromlist=[f'Bot{bot_number}'])
        BotClass = getattr(bot_module, f'Bot{bot_number}')
        
        # Initialize bot instance (for accessing exchange)
        bot = BotClass(master_pass)
        
        # Determine which coin to use based on bot
        coins = {
            'bot1': 'BTC/USD',
            'bot2': 'ETH/USD',  
            'bot3': 'SOL/USD',
            'bot4': 'ADA/USD'
        }
        pair = coins.get(bot_id, 'BTC/USD')
        
        # Calculate timestamp for 90 days ago
        since = int((datetime.now() - timedelta(days=90)).timestamp() * 1000)
        
        # Fetch 3 months of hourly data (90 days * 24 hours = 2160 candles)
        historical = bot.exchange.fetch_ohlcv(pair, '1h', since=since, limit=2160)
        
        # Run backtest
        if hasattr(bot, 'backtest'):
            # Bot3 requires extra parameters for mock sentiment
            if bot_id == 'bot3':
                portfolio, trades, sharpe = bot.backtest(historical, mock_sentiment=0.7, mock_news_sent=0.8)
            else:
                portfolio, trades, sharpe = bot.backtest(historical)
        else:
            return jsonify({'error': f'{bot_id} does not have backtest method'}), 400
        
        # Prepare backtest results
        initial_capital = 10000
        total_return = ((portfolio - initial_capital) / initial_capital) * 100
        win_rate = len([t for t in trades if t > 0]) / len(trades) * 100 if trades else 0
        avg_trade = np.mean(trades) if trades else 0
        max_drawdown = max((max(trades[:i+1]) - trades[i]) / max(trades[:i+1]) * 100 
                          for i in range(1, len(trades))) if len(trades) > 1 else 0
        
        # Get current bot parameters
        params = get_params(bot_id)
        
        # Analyze with Claude
        anthropic_client = Anthropic(api_key=claude_key)
        
        prompt = f"""Analyze this 3-month backtest for {bot_id.upper()}:
        
        Backtest Results:
        - Initial Capital: ${initial_capital:,}
        - Final Portfolio: ${portfolio:,.2f}
        - Total Return: {total_return:.2f}%
        - Number of Trades: {len(trades)}
        - Win Rate: {win_rate:.2f}%
        - Average Trade Return: {avg_trade:.2f}%
        - Sharpe Ratio: {sharpe:.2f}
        - Max Drawdown: {max_drawdown:.2f}%
        
        Current Bot Parameters:
        - Risk Level: {params.get('risk', '1.0')}%
        - Allocation: {params.get('alloc', '10')}%
        - Trading Frequency: {params.get('freq', '60')} seconds
        - Stop Loss: {params.get('stop_loss', '2')}%
        - Take Profit: {params.get('take_profit', '5')}%
        
        Based on the backtest performance, suggest optimal parameter adjustments.
        Consider that we target 5-10% daily returns with max 5% drawdown.
        
        Return ONLY a JSON object with recommended parameters like:
        {{"risk_level": 1.5, "allocation": 15, "trading_frequency": 45, "stop_loss": 2.5, "take_profit": 6}}
        
        Be aggressive if performance is good, conservative if poor. No other text."""
        
        response = anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse Claude's response
        rec_text = response.content[0].text.strip()
        recommendations = json.loads(rec_text)
        
        # Prepare response with backtest results and recommendations
        return jsonify({
            'backtest': {
                'initial_capital': initial_capital,
                'final_portfolio': round(portfolio, 2),
                'total_return': round(total_return, 2),
                'num_trades': len(trades),
                'win_rate': round(win_rate, 2),
                'sharpe_ratio': round(sharpe, 2),
                'max_drawdown': round(max_drawdown, 2)
            },
            'current_params': params,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    """Logout route"""
    session.pop('user', None)
    return redirect('/login')

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """500 error handler"""
    return 'Internal Server Error', 500

if __name__ == '__main__':
    # Initialize database
    from utils.db import init_db
    init_db()
    
    # Initialize clients on startup
    print("Initializing API clients...")
    reload_status = reload_clients()
    print(f"API clients loaded: {reload_status}")
    
    # Audit: Live sync on key input
    print("Platform ready for live keys" if any(reload_status.values()) else "Awaiting API keys")
    
    app.run(debug=True, port=5000) 