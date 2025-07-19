import threading
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils.db import init_db
from utils.env_loader import load_all_env_keys
from utils.optimization import weekly_reallocate, check_bot_active

# Import bots
from bots.bot1 import Bot1
from bots.bot2 import Bot2
from bots.bot3 import Bot3
from bots.bot4 import Bot4

# Import Flask app
from dashboard.app import app

# Bot instances
bot_instances = {}
bot_threads = {}

def start_bots():
    """Initialize and start all trading bots in separate threads"""
    global bot_instances, bot_threads
    
    # Initialize bot instances WITHOUT master password
    try:
        print("Initializing bots...")
        bot_instances['bot1'] = Bot1()
        bot_instances['bot2'] = Bot2()
        bot_instances['bot3'] = Bot3()
        bot_instances['bot4'] = Bot4()
        
        # Start each bot in its own thread only if active
        for bot_id, bot in bot_instances.items():
            if check_bot_active(bot_id):
                thread = threading.Thread(target=bot.run, name=f"Bot_{bot_id}")
                thread.daemon = True  # Daemon threads will exit when main program exits
                bot_threads[bot_id] = thread
                thread.start()
                print(f"Started {bot_id} in thread {thread.name}")
            else:
                print(f"Skipped {bot_id} - marked as inactive")
            
    except Exception as e:
        print(f"Error starting bots: {str(e)}")
        print("Make sure API keys are configured in .env file")

def start_dashboard():
    """Start Flask dashboard"""
    # Import bot instances to make them available to dashboard
    app.config['BOT_INSTANCES'] = bot_instances
    app.config['BOT_THREADS'] = bot_threads
    # Run Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def check_api_keys():
    """Check if API keys are configured"""
    required_keys = [
        ('COINBASE_API_KEY', 'COINBASE_API_KEY_NAME'),  # Either legacy or CDP
        'TAAPI_SECRET',
        ('TWITTER_API_KEY', 'TWITTERAPI_KEY'),  # Either name works
        'SCRAPINGBEE_API_KEY',
        'XAI_API_KEY',
        'PERPLEXITY_API_KEY',
        'ANTHROPIC_API_KEY'
    ]
    
    missing_keys = []
    for key in required_keys:
        if isinstance(key, tuple):
            # Check if any of the alternatives exist
            found = False
            for alt_key in key:
                if os.getenv(alt_key):
                    found = True
                    break
            if not found:
                missing_keys.append(' or '.join(key))
        else:
            # Single key check
            if not os.getenv(key):
                missing_keys.append(key)
    
    return missing_keys

def stop_bots():
    """Stop all running bot instances."""
    for bot_id, bot in bot_instances.items():
        bot.stop()
    print("All bots stopped.")

def main():
    """Main entry point for the trading bot system"""
    # Initialize database
    init_db()
    
    # Check environment
    print("Starting bot system...")
    print(f"Environment: {os.getenv('NODE_ENV', 'development')}")
    
    # Load all environment keys
    all_keys = load_all_env_keys()
    print(f"\n✓ Loaded {len(all_keys)} environment variables")
    
    # Check if we have required API keys
    missing_keys = check_api_keys()
    if missing_keys:
        print("\n⚠️  Missing API Keys:")
        for key in missing_keys:
            print(f"  - {key}")
        print("\nPlease add these keys to your .env file")
        return
    
    print("\n✓ All required API keys found")
    
    # Start WebSocket for real-time data
    print("\nStarting WebSocket connection...")
    try:
        from utils.websocket_client import start_websocket
        start_websocket()
        print("✓ WebSocket connected for real-time data")
    except Exception as e:
        print(f"Warning: WebSocket connection failed: {str(e)}")
        print("Bots will use API polling as fallback")
    
    # Start bots in background threads
    print("\nStarting trading bots...")
    start_bots()  # No master_pass needed
    
    # Start weekly optimization thread
    def optimization_loop():
        """Run weekly portfolio optimization"""
        while True:
            try:
                # Check if it's Monday (0 = Monday)
                if datetime.now().weekday() == 0:
                    print("\nRunning weekly portfolio optimization...")
                    weekly_reallocate()  # No master_pass needed
                    # Sleep for 24 hours to avoid running multiple times on Monday
                    time.sleep(86400)
                else:
                    # Check again in 1 hour
                    time.sleep(3600)
            except Exception as e:
                print(f"Optimization error: {str(e)}")
                time.sleep(3600)  # Wait an hour before retry
    
    opt_thread = threading.Thread(target=optimization_loop, name="Optimization")
    opt_thread.daemon = True
    opt_thread.start()
    print("✓ Weekly optimization scheduler started")
    
    # Keep main thread alive and handle shutdown
    print("\n" + "="*50)
    print("Bot system is running!")
    print("Press Ctrl+C to stop")
    print("="*50 + "\n")
    
    try:
        while True:
            time.sleep(60)  # Check every minute
            # You could add status checks here
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        stop_bots()
        from utils.websocket_client import stop_websocket
        stop_websocket()
        print("Goodbye!")

if __name__ == '__main__':
    main()
