import threading
import time
import getpass
import os
from datetime import datetime
from dotenv import load_dotenv
from bots.bot1 import Bot1
from bots.bot2 import Bot2
from bots.bot3 import Bot3
from bots.bot4 import Bot4
from dashboard.app import app
from utils.db import init_db, get_key
from utils.optimization import weekly_reallocate, check_bot_active
from utils.env_loader import get_master_password, has_env_keys, load_all_env_keys

# Load environment variables
load_dotenv()

# Global bot instances and threads
bot_instances = {}
bot_threads = {}
master_password = None

def start_bots(master_pass):
    """Initialize and start all trading bots in separate threads"""
    global bot_instances, bot_threads
    
    # Initialize bot instances with master password
    try:
        print("Initializing bots...")
        bot_instances['bot1'] = Bot1(master_pass)
        bot_instances['bot2'] = Bot2(master_pass)
        bot_instances['bot3'] = Bot3(master_pass)
        bot_instances['bot4'] = Bot4(master_pass)
        
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
        print("Make sure API keys are configured in the database")

def start_dashboard():
    """Start Flask dashboard"""
    # Import bot instances to make them available to dashboard
    app.config['BOT_INSTANCES'] = bot_instances
    app.config['BOT_THREADS'] = bot_threads
    # Run Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def check_api_keys(master_pass):
    """Check if API keys are configured"""
    required_keys = [
        'coinbase_api_key',
        'coinbase_secret',
        'taapi_key',  # Updated from twitterapi_io_key
        'grok_api_key',
        'coindesk_api_key',  # Optional - Coindesk may work without key
        'perplexity_api_key',
        'claude_api_key'
    ]
    
    missing_keys = []
    for key in required_keys:
        if not get_key(key, master_pass):
            missing_keys.append(key)
    
    return missing_keys

if __name__ == '__main__':
    print("=== Crypto Trading Platform MVP ===")
    print("Initializing...")
    
    # Initialize database
    init_db()
    print("Database initialized successfully")
    
    # Check if we have environment variables
    if has_env_keys():
        print("\nDetected API keys in environment variables (.env file)")
        env_keys = load_all_env_keys()
        print(f"Found {len(env_keys)} API keys in environment")
        master_password = get_master_password()
        print(f"Using master password from environment")
    else:
        # Get master password for encryption
        print("\nEnter master password for API key encryption:")
        master_password = getpass.getpass("Master password: ")
    
    # Check if API keys are configured
    missing_keys = check_api_keys(master_password)
    if missing_keys:
        print("\nWARNING: The following API keys are not configured:")
        for key in missing_keys:
            print(f"  - {key}")
        print("\nYou can configure them via:")
        print("1. The dashboard after logging in")
        print("2. Creating a .env file with your API keys")
        print("\nThe bots will not function properly without API keys.")
        
        # Ask if user wants to continue
        choice = input("\nDo you want to continue anyway? (y/n): ")
        if choice.lower() != 'y':
            print("Exiting...")
            exit(0)
    else:
        print("\n✓ All required API keys are configured!")
    
    # Start bots in background threads
    print("\nStarting trading bots...")
    start_bots(master_password)
    
    # Start weekly optimization thread
    def optimization_loop():
        """Run weekly portfolio optimization"""
        while True:
            try:
                # Check if it's Monday (0 = Monday)
                if datetime.now().weekday() == 0:
                    print("\nRunning weekly portfolio optimization...")
                    if master_password:
                        weekly_reallocate(master_password)
                    # Sleep for 24 hours to avoid running multiple times on Monday
                    time.sleep(86400)
                else:
                    # Check again in 1 hour
                    time.sleep(3600)
            except Exception as e:
                print(f"Error in optimization loop: {str(e)}")
                time.sleep(3600)  # Wait 1 hour before retrying
    
    optimization_thread = threading.Thread(target=optimization_loop, name="OptimizationThread")
    optimization_thread.daemon = True
    optimization_thread.start()
    print("Started portfolio optimization thread")
    
    # Give bots a moment to initialize
    time.sleep(2)
    
    # Start dashboard (this will block until the app is stopped)
    print("\nStarting dashboard on http://localhost:5000")
    print("Default login: josh / March3392!")
    print("\nPress Ctrl+C to stop the application")
    
    try:
        start_dashboard()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        # Stop all bots
        for bot_id, bot in bot_instances.items():
            bot.stop()
        print("Application stopped.")
