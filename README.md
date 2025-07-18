# The GOAT Farm - Crypto Trading Platform

A sophisticated cryptocurrency trading platform featuring 4 parallel trading bots targeting 5-10% daily returns.

## Features

- **4 Parallel Trading Bots**: Each bot implements different trading strategies
  - Bot1: Momentum trading with BTC/ETH focus
  - Bot2: Scalping strategy for quick trades
  - Bot3: Technical analysis-based trading
  - Bot4: Diversified portfolio approach

- **Web Dashboard**: Real-time monitoring at http://localhost:5000
- **API Integrations**: Coinbase, TAAPI.io, Grok, Perplexity, Claude, CoinDesk
- **Secure Storage**: SQLite database with encrypted API key storage
- **Portfolio Optimization**: Automatic portfolio rebalancing

## Setup Instructions

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/BuzzwordStrategies/thegoatfarm.git
cd thegoatfarm
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```env
# Trading API
COINBASE_API_KEY=your_key_here
COINBASE_SECRET=your_secret_here

# Technical Analysis
TAAPI_KEY=your_key_here

# AI & Sentiment
GROK_API_KEY=your_key_here
CLAUDE_API_KEY=your_key_here

# Research & News
PERPLEXITY_API_KEY=your_key_here
COINDESK_API_KEY=your_key_here

# Master Password
MASTER_PASSWORD=your_secure_password
```

### Running the Platform

1. Verify your setup:
```bash
python test_env_keys.py
```

2. Start the platform:
```bash
python main.py
```

3. Access the dashboard at http://localhost:5000
   - Default login: josh / March3392! (change this in production)

## Security Notice

- Never commit your `.env` file or API keys
- The `.gitignore` file is configured to exclude sensitive data
- Database files in `data/` directory are also excluded from version control

## Project Structure

```
The GOAT Farm/
├── bots/              # Trading bot implementations
├── dashboard/         # Flask web interface
├── utils/             # Utility modules
├── data/             # Database storage (gitignored)
├── .env              # Environment variables (gitignored)
├── main.py           # Application entry point
├── requirements.txt  # Python dependencies
└── test_env_keys.py  # Environment verification script
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes (ensure no API keys are included)
4. Push to the branch
5. Create a Pull Request

## License

This project is proprietary software. All rights reserved.
