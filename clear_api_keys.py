import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'app.db')

def clear_all_api_keys():
    """Clear all API keys from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete all records from api_keys table
    cursor.execute('DELETE FROM api_keys')
    
    # Get the number of deleted rows
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"Successfully cleared {deleted_count} API keys from the database.")

if __name__ == '__main__':
    print("=== Clearing All API Keys ===")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print("Database does not exist. No keys to clear.")
    else:
        clear_all_api_keys()
        print("All API keys have been removed from the database.")
        print("You will need to re-enter them after relaunching the application.")
