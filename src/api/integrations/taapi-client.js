const BaseAPIClient = require('../base/api-client');

class TaapiClient extends BaseAPIClient {
  constructor(keyManager) {
    super({
      name: 'TAAPI',
      baseURL: 'https://api.taapi.io',
      timeout: 15000,
      retries: 3
    });
    
    this.keyManager = keyManager;
    this.supportedExchanges = ['binance', 'coinbase', 'kraken', 'bitfinex'];
    this.supportedIntervals = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'];
  }
  
  async getAuthHeaders(config) {
    // TAAPI uses query parameter for auth
    return {};
  }
  
  async makeRequest(endpoint, params = {}) {
    const apiKey = await this.keyManager.getKey('taapi', 'TAAPI_API_KEY');
    const queryParams = {
      secret: apiKey,
      ...params
    };
    
    return this.get(endpoint, queryParams);
  }
  
  // Technical Indicators
  async getRSI(exchange, symbol, interval, period = 14) {
    return this.makeRequest('/rsi', {
      exchange,
      symbol,
      interval,
      period
    });
  }
  
  async getMACD(exchange, symbol, interval, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
    return this.makeRequest('/macd', {
      exchange,
      symbol,
      interval,
      optInFastPeriod: fastPeriod,
      optInSlowPeriod: slowPeriod,
      optInSignalPeriod: signalPeriod
    });
  }
  
  async getBollingerBands(exchange, symbol, interval, period = 20, stdDev = 2) {
    return this.makeRequest('/bbands', {
      exchange,
      symbol,
      interval,
      period,
      stddev: stdDev
    });
  }
  
  async getEMA(exchange, symbol, interval, period = 20) {
    return this.makeRequest('/ema', {
      exchange,
      symbol,
      interval,
      period
    });
  }
  
  async getSMA(exchange, symbol, interval, period = 20) {
    return this.makeRequest('/sma', {
      exchange,
      symbol,
      interval,
      period
    });
  }
  
  async getStochastic(exchange, symbol, interval, kPeriod = 14, dPeriod = 3) {
    return this.makeRequest('/stoch', {
      exchange,
      symbol,
      interval,
      kPeriod,
      dPeriod
    });
  }
  
  async getATR(exchange, symbol, interval, period = 14) {
    return this.makeRequest('/atr', {
      exchange,
      symbol,
      interval,
      period
    });
  }
  
  async getADX(exchange, symbol, interval, period = 14) {
    return this.makeRequest('/adx', {
      exchange,
      symbol,
      interval,
      period
    });
  }
  
  async getCCI(exchange, symbol, interval, period = 20) {
    return this.makeRequest('/cci', {
      exchange,
      symbol,
      interval,
      period
    });
  }
  
  async getIchimoku(exchange, symbol, interval) {
    return this.makeRequest('/ichimoku', {
      exchange,
      symbol,
      interval
    });
  }
  
  // Pattern Recognition
  async getCandles(exchange, symbol, interval, limit = 100) {
    return this.makeRequest('/candles', {
      exchange,
      symbol,
      interval,
      limit
    });
  }
  
  async detectPatterns(exchange, symbol, interval) {
    const patterns = [];
    
    // Check for various patterns
    const patternChecks = [
      { name: 'doji', endpoint: '/pattern/doji' },
      { name: 'hammer', endpoint: '/pattern/hammer' },
      { name: 'engulfing', endpoint: '/pattern/engulfing' },
      { name: 'morningstar', endpoint: '/pattern/morningstar' },
      { name: 'eveningstar', endpoint: '/pattern/eveningstar' }
    ];
    
    for (const pattern of patternChecks) {
      try {
        const result = await this.makeRequest(pattern.endpoint, {
          exchange,
          symbol,
          interval
        });
        
        if (result.value !== 0) {
          patterns.push({
            name: pattern.name,
            value: result.value,
            signal: result.value > 0 ? 'bullish' : 'bearish'
          });
        }
      } catch (error) {
        console.warn(`Pattern detection failed for ${pattern.name}:`, error.message);
      }
    }
    
    return patterns;
  }
  
  // Advanced Analysis
  async getMultipleIndicators(exchange, symbol, interval) {
    const indicators = {};
    
    // Fetch multiple indicators in parallel
    const indicatorPromises = [
      this.getRSI(exchange, symbol, interval).then(r => indicators.rsi = r),
      this.getMACD(exchange, symbol, interval).then(r => indicators.macd = r),
      this.getBollingerBands(exchange, symbol, interval).then(r => indicators.bbands = r),
      this.getEMA(exchange, symbol, interval, 50).then(r => indicators.ema50 = r),
      this.getEMA(exchange, symbol, interval, 200).then(r => indicators.ema200 = r),
      this.getATR(exchange, symbol, interval).then(r => indicators.atr = r),
      this.getADX(exchange, symbol, interval).then(r => indicators.adx = r)
    ];
    
    await Promise.allSettled(indicatorPromises);
    
    return indicators;
  }
  
  async getTradingSignal(exchange, symbol, interval) {
    const indicators = await this.getMultipleIndicators(exchange, symbol, interval);
    
    let bullishSignals = 0;
    let bearishSignals = 0;
    
    // RSI
    if (indicators.rsi) {
      if (indicators.rsi.value < 30) bullishSignals++;
      else if (indicators.rsi.value > 70) bearishSignals++;
    }
    
    // MACD
    if (indicators.macd) {
      if (indicators.macd.valueMACD > indicators.macd.valueMACDSignal) bullishSignals++;
      else bearishSignals++;
    }
    
    // Bollinger Bands
    if (indicators.bbands) {
      const price = indicators.bbands.value;
      if (price < indicators.bbands.valueLowerBand) bullishSignals++;
      else if (price > indicators.bbands.valueUpperBand) bearishSignals++;
    }
    
    // EMA Cross
    if (indicators.ema50 && indicators.ema200) {
      if (indicators.ema50.value > indicators.ema200.value) bullishSignals++;
      else bearishSignals++;
    }
    
    // ADX (trend strength)
    const trendStrength = indicators.adx ? 
      indicators.adx.value > 25 ? 'strong' : 'weak' : 'unknown';
    
    return {
      symbol,
      interval,
      timestamp: new Date().toISOString(),
      bullishSignals,
      bearishSignals,
      signal: bullishSignals > bearishSignals ? 'BUY' : 
             bearishSignals > bullishSignals ? 'SELL' : 'HOLD',
      confidence: Math.abs(bullishSignals - bearishSignals) / 
                (bullishSignals + bearishSignals) * 100,
      trendStrength,
      indicators
    };
  }
  
  // Backtesting Helper
  async getHistoricalIndicator(indicator, exchange, symbol, interval, params = {}) {
    const endpoint = `/${indicator}/backtest`;
    return this.makeRequest(endpoint, {
      exchange,
      symbol,
      interval,
      ...params
    });
  }
}

module.exports = TaapiClient; 