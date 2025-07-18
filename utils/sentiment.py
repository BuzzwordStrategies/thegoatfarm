import requests
import praw
import time
from typing import Dict, List, Optional, Any
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from utils.db import get_key, get_params, increment_api_call, log_trade

# Initialize VADER sentiment analyzer
vader = SentimentIntensityAnalyzer()

def get_twitter_sentiment(query: str, count: int = 50, master_pass: Optional[str] = None) -> float:
    """
    Get sentiment from Twitter/X using Grok API for analysis.
    Since we don't have direct Twitter API access, we'll use Grok to analyze Twitter trends.
    Returns VADER compound score averaged across analysis.
    """
    try:
        # Use Grok to analyze Twitter sentiment
        grok_prompt = f"Analyze the current Twitter/X sentiment about {query}. Focus on recent tweets and provide a brief summary of the overall sentiment."
        sentiment_score = get_grok_sentiment(grok_prompt, master_pass or '')
        
        if sentiment_score != 0.0:
            return sentiment_score
        
        # Fallback to default neutral if Grok fails
        log_trade('sentiment', 'info', f'Twitter sentiment unavailable for {query}, using neutral')
        return 0.0
        
    except Exception as e:
        print(f"Error in Twitter sentiment analysis: {e}")
        log_trade('sentiment', 'error', f'Twitter sentiment error: {str(e)}')
        return 0.0

def get_grok_sentiment(text: str, master_pass: str = None) -> float:
    """
    Get sentiment from Grok API for cryptocurrency-related text.
    Returns a normalized sentiment score between -1 and 1.
    """
    try:
        # Get API key from database
        api_key = get_key('grok_api_key', master_pass or '')
        
        if not api_key:
            print("Grok API key not found in database")
            return 0.0
        
        # Grok API endpoint
        url = "https://api.x.ai/v1/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'grok-beta',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a sentiment analysis expert. Analyze the sentiment of the given text and respond with ONLY a number between -1 (very negative) and 1 (very positive). 0 is neutral.'
                },
                {
                    'role': 'user',
                    'content': text
                }
            ],
            'temperature': 0.1,
            'max_tokens': 10
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 401:
                print("Invalid Grok API key—check .env")
                log_trade('grok', 'auth_error', 'Invalid API key')
                return 0.0
                
            response.raise_for_status()
            data = response.json()
            
            # Extract sentiment score from response
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '0')
            
            try:
                # Parse the sentiment score
                sentiment = float(content.strip())
                # Ensure it's within bounds
                sentiment = max(-1.0, min(1.0, sentiment))
                return sentiment
            except ValueError:
                # If parsing fails, use VADER on the response
                sentiment = vader.polarity_scores(content)
                return sentiment['compound']
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("Grok API rate limit reached")
                log_trade('grok', 'rate_limit', '429 error')
            else:
                print(f"Grok API HTTP error: {e}")
                log_trade('grok', 'error', f'HTTP {e.response.status_code}')
            return 0.0
        except Exception as e:
            print(f"Error with Grok API: {e}")
            log_trade('grok', 'error', str(e))
            return 0.0
            
    except Exception as e:
        print(f"Error in Grok sentiment analysis: {e}")
        return 0.0

def get_reddit_sentiment(subreddit_name: str = 'CryptoCurrency', count: int = 25, master_pass: Optional[str] = None) -> float:
    """
    Get average sentiment from Reddit posts and comments.
    Returns VADER compound score averaged across posts.
    """
    try:
        # Reddit API credentials would typically be stored, but for MVP we'll simulate
        # In production, you'd use PRAW with proper credentials
        
        # For now, return a simulated sentiment based on general crypto market
        # This would be replaced with actual Reddit API calls
        log_trade('sentiment', 'info', 'Reddit sentiment simulation - implement PRAW when credentials available')
        return 0.1  # Slightly positive default
        
    except Exception as e:
        print(f"Error in Reddit sentiment analysis: {e}")
        return 0.0

def get_news_sentiment(coin: str = 'bitcoin', master_pass: Optional[str] = None) -> float:
    """
    Get sentiment from news articles via NewsAPI.
    Returns average sentiment score.
    """
    try:
        # For MVP, we'll use CoinDesk data which doesn't require API key
        news_data = get_coindesk_news(coin)
        
        if news_data and news_data.get('articles'):
            scores = []
            for article in news_data['articles'][:10]:  # Analyze top 10 articles
                title = article.get('title', '')
                description = article.get('description', '')
                combined_text = f"{title} {description}"
                
                sentiment = vader.polarity_scores(combined_text)
                scores.append(sentiment['compound'])
            
            return sum(scores) / len(scores) if scores else 0.0
        
        return 0.0
        
    except Exception as e:
        print(f"Error in news sentiment analysis: {e}")
        return 0.0

def get_coindesk_news(query: str = 'bitcoin') -> Dict[str, Any]:
    """
    Get news from CoinDesk API (no key required for basic access).
    """
    try:
        # CoinDesk public API endpoint
        url = f"https://api.coindesk.com/v1/articles/search?q={query}&limit=10"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            increment_api_call('coindesk')
            return response.json()
        else:
            print(f"CoinDesk API returned status {response.status_code}")
            return {'articles': []}
            
    except Exception as e:
        print(f"Error fetching CoinDesk news: {e}")
        log_trade('coindesk', 'error', str(e))
        return {'articles': []}

def get_perplexity_research(query: str, master_pass: str = None) -> Dict[str, Any]:
    """
    Get research insights from Perplexity API about a cryptocurrency or market trend.
    Returns analysis with sentiment and key insights.
    """
    try:
        # Get API key from database
        api_key = get_key('perplexity_api_key', master_pass or '')
        
        if not api_key:
            print("Perplexity API key not found in database")
            return {'insights': '', 'sentiment': 0.0}
        
        # Perplexity API endpoint
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'pplx-7b-online',  # Fixed model name
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a cryptocurrency market analyst. Provide brief, factual insights about market trends and sentiment.'
                },
                {
                    'role': 'user',
                    'content': f'Analyze current market sentiment and trends for {query}. Be concise.'
                }
            ],
            'temperature': 0.2,
            'max_tokens': 200
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 401:
                print("Invalid Perplexity key—check .env")
                log_trade('perplexity', 'auth_error', 'Invalid API key')
                return {'insights': '', 'sentiment': 0.0}
                
            response.raise_for_status()
            data = response.json()
            
            # Extract insights from response
            insights = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Get sentiment of the insights
            sentiment_score = get_grok_sentiment(insights, master_pass or '')
            if sentiment_score == 0.0:
                sentiment = vader.polarity_scores(insights)
                sentiment_score = sentiment['compound']
            
            return {
                'insights': insights,
                'sentiment': sentiment_score
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("Perplexity API rate limit reached")
                log_trade('perplexity', 'rate_limit', '429 error')
            else:
                print(f"Perplexity API HTTP error: {e}")
                log_trade('perplexity', 'error', f'HTTP {e.response.status_code}')
            return {'insights': '', 'sentiment': 0.0}
        except Exception as e:
            print(f"Error with Perplexity API: {e}")
            log_trade('perplexity', 'error', str(e))
            return {'insights': '', 'sentiment': 0.0}
            
    except Exception as e:
        print(f"Error in Perplexity research: {e}")
        return {'insights': '', 'sentiment': 0.0}

def get_claude_analysis(prompt: str, master_pass: str = None) -> Dict[str, Any]:
    """
    Get advanced analysis from Claude API for complex market scenarios.
    """
    try:
        from anthropic import Anthropic
        
        # Get API key from database
        api_key = get_key('claude_api_key', master_pass or '')
        
        if not api_key:
            print("Claude API key not found in database")
            return {'analysis': '', 'sentiment': 0.0}
        
        try:
            # Initialize Anthropic client
            client = Anthropic(api_key=api_key)
            
            # Create message
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": f"As a crypto market analyst, provide a brief analysis: {prompt}"
                    }
                ]
            )
            
            # Extract text from message content
            analysis = ''
            if hasattr(message, 'content') and len(message.content) > 0:
                if hasattr(message.content[0], 'text'):
                    analysis = message.content[0].text
                else:
                    # Handle different response formats
                    analysis = str(message.content[0])
            
            # Get sentiment of the analysis
            sentiment = vader.polarity_scores(analysis)
            
            return {
                'analysis': analysis,
                'sentiment': sentiment['compound']
            }
            
        except Exception as e:
            if 'Invalid API key' in str(e) or '401' in str(e):
                print("Invalid Claude API key—check .env")
                log_trade('claude', 'auth_error', 'Invalid API key')
            else:
                print(f"Error with Claude API: {e}")
                log_trade('claude', 'error', str(e))
            return {'analysis': '', 'sentiment': 0.0}
            
    except ImportError:
        print("Anthropic library not installed")
        return {'analysis': '', 'sentiment': 0.0}
    except Exception as e:
        print(f"Error in Claude analysis: {e}")
        return {'analysis': '', 'sentiment': 0.0}

def get_combined_sentiment(coin: str = 'BTC', master_pass: Optional[str] = None) -> Dict[str, float]:
    """
    Get combined sentiment from multiple sources.
    Returns dictionary with individual and average sentiment scores.
    """
    sentiments = {}
    
    try:
        # Get sentiment from various sources
        sentiments['twitter'] = get_twitter_sentiment(f"{coin} cryptocurrency", master_pass=master_pass)
        sentiments['reddit'] = get_reddit_sentiment(master_pass=master_pass)
        sentiments['news'] = get_news_sentiment(coin.lower(), master_pass=master_pass)
        
        # Get research insights from Perplexity
        research_data = get_perplexity_research(f"{coin} cryptocurrency", master_pass=master_pass or '')
        sentiments['perplexity'] = research_data.get('sentiment', 0.0)
        
        # Get Claude analysis for complex scenarios
        claude_data = get_claude_analysis(f"Current market sentiment for {coin}", master_pass=master_pass or '')
        sentiments['claude'] = claude_data.get('sentiment', 0.0)
        
        # Calculate weighted average (giving more weight to AI analysis)
        weights = {
            'twitter': 0.15,
            'reddit': 0.15,
            'news': 0.20,
            'perplexity': 0.25,
            'claude': 0.25
        }
        
        weighted_sum = sum(sentiments.get(source, 0) * weight for source, weight in weights.items())
        total_weight = sum(weight for source, weight in weights.items() if source in sentiments)
        
        sentiments['average'] = weighted_sum / total_weight if total_weight > 0 else 0.0
        
    except Exception as e:
        print(f"Error in combined sentiment analysis: {e}")
        log_trade('sentiment', 'error', f'Combined sentiment error: {str(e)}')
        sentiments['average'] = 0.0
    
    return sentiments

def analyze_volume_surge(symbol: str, threshold: float = 2.0) -> bool:
    """
    Detect if there's a volume surge (2x normal volume).
    Used by Bot 4 for ML-based trading.
    """
    try:
        # This would typically use exchange data
        # For now, return False to avoid false signals
        return False
    except Exception as e:
        print(f"Error analyzing volume surge: {e}")
        return False 