from anthropic import Anthropic
from datetime import datetime, timedelta
import json
from utils.db import get_key, get_params, set_param, log_trade
import sqlite3
import pandas as pd

def weekly_reallocate(master_pass: str = None):
    """
    Weekly portfolio reallocation using Claude API.
    Analyzes past 7 days performance and reallocates to winning bots.
    Shuts down bots with negative P&L for 2 weeks.
    """
    try:
        # Connect to database
        con = sqlite3.connect('data/app.db')
        cur = con.cursor()
        
        # Calculate timestamps
        now = datetime.now()
        week_ago = (now - timedelta(days=7)).isoformat()
        two_weeks_ago = (now - timedelta(days=14)).isoformat()
        
        # Get P&L for last 7 days per bot
        query = """
        SELECT bot_id, 
               SUM(CASE WHEN details LIKE '%profit%' 
                   THEN CAST(SUBSTR(details, 
                        INSTR(details, 'profit') + 8,
                        CASE 
                            WHEN INSTR(SUBSTR(details, INSTR(details, 'profit') + 8), ',') > 0
                            THEN INSTR(SUBSTR(details, INSTR(details, 'profit') + 8), ',') - 1
                            ELSE INSTR(SUBSTR(details, INSTR(details, 'profit') + 8), '}') - 1
                        END
                   ) AS REAL)
                   ELSE 0 END) as profit
        FROM trade_logs 
        WHERE timestamp > ? 
        GROUP BY bot_id
        """
        
        cur.execute(query, (week_ago,))
        weekly_pl = dict(cur.fetchall())
        
        # Get P&L for last 14 days to check for shutdown
        cur.execute(query, (two_weeks_ago,))
        two_week_pl = dict(cur.fetchall())
        
        # Calculate average P&L
        avg_pl = sum(weekly_pl.values()) / len(weekly_pl) if weekly_pl else 0
        
        # Get detailed trade logs for Claude
        logs_df = pd.read_sql(
            "SELECT * FROM trade_logs WHERE timestamp > ? ORDER BY timestamp DESC", 
            con, 
            params=(week_ago,)
        )
        logs_json = logs_df.to_json(orient='records')
        
        # Close database connection
        con.close()
        
        # Get Claude API key
        api_key = get_key('claude_api_key', master_pass)
        if not api_key:
            log_trade('optimization', 'error', 'Claude API key not found')
            return
        
        # Initialize Claude client
        client = Anthropic(api_key=api_key)
        
        # Prepare analysis data
        analysis = {
            'weekly_pl': weekly_pl,
            'two_week_pl': two_week_pl,
            'average_pl': avg_pl,
            'current_allocations': {
                'bot1': float(get_params('bot1').get('allocation', 10)),
                'bot2': float(get_params('bot2').get('allocation', 10)),
                'bot3': float(get_params('bot3').get('allocation', 8)),
                'bot4': float(get_params('bot4').get('allocation', 12))
            }
        }
        
        # Create prompt for Claude
        system_prompt = """You are a portfolio optimization expert for crypto trading bots. 
        Analyze the trading performance and suggest optimal portfolio allocations.
        Rules:
        1. Allocate more to bots with P&L > average
        2. Reduce allocation for bots with P&L < average
        3. Shutdown bots with negative P&L for 2 weeks
        4. Total allocations must equal 100%
        5. Min allocation: 5%, Max allocation: 40%
        
        Respond with JSON only:
        {
            "allocations": {"bot1": 25, "bot2": 30, "bot3": 20, "bot4": 25},
            "shutdown": ["bot3"],
            "reasoning": "Brief explanation"
        }"""
        
        user_prompt = f"""
        Weekly P&L by bot: {json.dumps(weekly_pl)}
        Two-week P&L by bot: {json.dumps(two_week_pl)}
        Average weekly P&L: ${avg_pl:.2f}
        Current allocations: {json.dumps(analysis['current_allocations'])}
        
        Recent trades:
        {logs_json}
        
        Suggest new allocations and any shutdowns.
        """
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku for efficiency
            max_tokens=500,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Parse Claude's response
        try:
            parsed = json.loads(response.content[0].text)
        except:
            # Try to extract JSON from response
            text = response.content[0].text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])
            else:
                raise ValueError("Could not parse Claude response")
        
        # Apply reallocations only if performance justifies it
        reallocate = False
        for bot, pl in weekly_pl.items():
            if pl > avg_pl * 1.2:  # 20% above average
                reallocate = True
                break
        
        if reallocate and 'allocations' in parsed:
            # Update allocations
            for bot, alloc in parsed['allocations'].items():
                if bot in ['bot1', 'bot2', 'bot3', 'bot4']:
                    set_param(bot, 'allocation', str(alloc))
                    log_trade(bot, 'info', f'Allocation updated to {alloc}%')
        
        # Process shutdowns
        if 'shutdown' in parsed:
            for bot in parsed['shutdown']:
                if bot in ['bot1', 'bot2', 'bot3', 'bot4']:
                    # Check if really negative for 2 weeks
                    if two_week_pl.get(bot, 0) < 0:
                        set_param(bot, 'active', 'False')
                        log_trade(bot, 'warning', f'Bot shutdown due to negative P&L for 2 weeks: ${two_week_pl.get(bot, 0):.2f}')
        
        # Log optimization results
        log_trade('optimization', 'info', json.dumps({
            'timestamp': now.isoformat(),
            'weekly_pl': weekly_pl,
            'avg_pl': avg_pl,
            'reallocated': reallocate,
            'allocations': parsed.get('allocations', {}),
            'shutdowns': parsed.get('shutdown', []),
            'reasoning': parsed.get('reasoning', '')
        }))
        
    except Exception as e:
        # Fallback to default allocations on error
        log_trade('optimization', 'error', f'Reallocation failed: {str(e)}')
        
        # Keep current allocations as fallback
        default_allocations = {
            'bot1': 25,
            'bot2': 25,
            'bot3': 25,
            'bot4': 25
        }
        
        for bot, alloc in default_allocations.items():
            current = float(get_params(bot).get('allocation', alloc))
            # Only update if significantly different
            if abs(current - alloc) > 5:
                set_param(bot, 'allocation', str(alloc))

# Additional helper function to check bot status
def check_bot_active(bot_id: str) -> bool:
    """Check if a bot is active"""
    params = get_params(bot_id)
    return params.get('active', 'True') == 'True' 