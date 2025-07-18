# Project Context and Memory

## Project Overview
We are building a local-first crypto trading platform MVP that connects to Coinbase Advanced Trade API for live trading. It includes sentiment analysis from Twitter (X) and Reddit, a NewsAPI integration for one bot, and four parallel trading bots. The bots are:
- Bot 1: Trend-Following Momentum Bot with Sentiment Boost (uses moving averages, RSI, sentiment filter; targets 1-2% daily, low risk).
- Bot 2: Mean-Reversion Scalper with Volatility Filter (uses Bollinger Bands, ATR, sentiment; targets 0.8-1.5% daily).
- Bot 3: News-Driven Breakout Bot with Sentiment and Arbitrage Edge (uses NewsAPI, Donchian Channels, triangular arbitrage; targets 6-9% daily).
- Bot 4: Machine-Learning-Powered Range Scalper with Sentiment and Volume Surge (uses Random Forest ML model, RSI/MACD/volume, sentiment; targets 5-8% daily).
All bots aim for high returns (up to 5-10% daily combined) with max 5% drawdown, running in parallel as threads. Use Python 3, SQLite for database (storing API keys, trade logs, parameters), Flask for dashboard, CCXT or Coinbase SDK for trading, Tweepy for Twitter, PRAW for Reddit, NewsAPI for news, VADER/TextBlob for sentiment, Scikit-learn for ML in Bot 4. Deploy locally on a machine (e.g., PC/Raspberry Pi) with Docker for 24/7 operation. Dashboard: Web interface with sliders for risk/allocation, buttons for start/pause/stop, real-time P&L, sentiment/news displays, charts via Chart.js. Security: Encrypt API keys. Direct API connections (no MCP server for MVP). Prevent hallucinations: Only implement exactly as specified in prompts; no extra features.

## Key Constraints
- Local-first: All runs locally, no cloud dependencies except APIs.
- MVP Focus: Minimal viable product; no advanced UI polish beyond functional Flask app.
- Risk Management: Each bot has tight stop-loss (0.3-2%), position sizing (3-20% portfolio).
- Parallel Execution: Use threading for bots.
- Testing: Include backtesting with historical data from Coinbase/CCXT.
- APIs: Coinbase Advanced Trade (trading), Twitter v2 (sentiment), PRAW (Reddit sentiment), NewsAPI (Bot 3).
- Libraries: Install via requirements.txt: flask, sqlite3, tweepy, praw, vaderSentiment, textblob, requests, ccxt, scikit-learn, pandas, numpy, matplotlib, chart.js (via CDN for dashboard).
- Progress Logging: Always append to progress.md at the end of each task series with timestamped detailed logs.

## Progress Logging Protocol
At the end of every series of tasks in a prompt (after completing all code generation, file creation, or modifications), append a detailed log entry to a file named "progress.md" in the project root. The entry must be in this exact format:
Timestamp: [Current UTC Timestamp in YYYY-MM-DD HH:MM:SS format]
Actions Taken:
Bullet point list of every specific action completed, including files created/modified, code snippets added, and why.
Be detailed enough for full reproducibility and debugging; include key code excerpts if relevant.
Current Project State:
Summary of what's built so far.
Any pending issues or next steps noted.
End of Log Entry 