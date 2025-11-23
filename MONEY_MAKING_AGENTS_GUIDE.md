# 💰 Money-Making Agents: Production Deployment Guide

**Goal**: Deploy profit-generating agents for prop betting and algorithmic trading with enterprise-grade risk controls.

---

## 🎯 Overview

You now have:
1. **Domain Ontologies**: `betting.ttl`, `trading.ttl` with strategies, risk rules, agent specs
2. **Specialized Agents**: `PropBettingAgent`, `AlgoTradingAgent` with Kelly Criterion, risk management
3. **Data Pipelines**: Betting odds, market data tools (ready for real API integration)
4. **Backtesting Engine**: Unit economics, Sharpe ratio, break-even analysis
5. **Agent Factory**: Industry-agnostic pattern for spawning agents

---

## 🚀 Quick Start (Local MVP)

### 1. Install Dependencies

```bash
cd /home/orson-dev/projects/ontology-kit

# Install if uv not available
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --all-extras
```

### 2. Set Environment Variables

```bash
# .env file
export XAI_API_KEY="your_grok_api_key"  # For Grok reasoning
export ODDS_API_KEY="your_odds_api_key"  # For betting odds (theoddsapi.com)
export ALPHA_VANTAGE_KEY="your_av_key"  # For stock data
export BINANCE_API_KEY="your_binance_key"  # For crypto data (optional)
```

### 3. Run Example: Prop Betting Agent

```python
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.factories import AgentFactory
from agent_kit.tools.betting_tools import fetch_player_props
from agent_kit.agents.prop_betting_agent import PropBet

# Load ontology
loader = OntologyLoader('assets/ontologies/betting.ttl')
loader.load()

# Create agent via factory
factory = AgentFactory(loader)
agent = factory.create_agent(
    "bet:PropBettingAgent",
    bankroll=10000.0,
    strategy="ValueBetting"
)

# Fetch prop bets
props_data = fetch_player_props(sport="basketball_nba")

# Convert to PropBet objects
props = [PropBet(**prop) for prop in props_data]

# Agent analyzes and generates recommendations
# (Need to integrate true probability estimation via ML model or Grok)
true_probs = {"lebron_points_2025_11_23": 0.58}  # Example
confidence = {"lebron_points_2025_11_23": 0.75}

recommendations = agent.analyze_props(props, true_probs, confidence)

print(f"Found {len(recommendations.edges)} edges")
print(f"Expected ROI: ${recommendations.expected_roi:.2f}")
print(f"Passed risk checks: {recommendations.passed_risk_checks}")

for edge in recommendations.edges:
    print(f"  {edge.prop_bet.description}")
    print(f"    Edge: {edge.edge:.2%}, Kelly: {edge.kelly_fraction:.2%}")
```

### 4. Run Example: Algo Trading Agent

```python
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.factories import AgentFactory
from agent_kit.tools.trading_tools import fetch_market_data, calculate_indicators
from agent_kit.agents.algo_trading_agent import Asset

# Load ontology
loader = OntologyLoader('assets/ontologies/trading.ttl')
loader.load()

# Create agent
factory = AgentFactory(loader)
agent = factory.create_agent(
    "trade:AlgoTradingAgent",
    portfolio_value=100000.0,
    strategy="MeanReversion"
)

# Fetch market data
tickers = ["AAPL", "MSFT", "GOOGL"]
market_data = {}

for ticker in tickers:
    data = fetch_market_data(ticker, interval="1day", limit=50)
    indicators = calculate_indicators(ticker, data)
    market_data[ticker] = {"data": data, "indicators": indicators}

# Create Asset objects
assets = [
    Asset(ticker=ticker, current_price=data["data"][-1]["close"], volatility=0.25)
    for ticker, data in market_data.items()
]

# Generate signals
recommendations = agent.generate_signals(assets, market_data)

print(f"Generated {len(recommendations.signals)} signals")
print(f"Portfolio Sharpe: {recommendations.portfolio_metrics.sharpe_ratio:.2f}")
print(f"Passed risk checks: {recommendations.passed_risk_checks}")

if recommendations.circuit_breaker_triggered:
    print("⚠️  CIRCUIT BREAKER TRIGGERED - TRADING HALTED")

for signal in recommendations.signals:
    print(f"  {signal.asset.ticker}: {signal.signal_type}")
    print(f"    Position: {signal.position_size:.2%}, Entry: ${signal.asset.current_price:.2f}")
    print(f"    Stop: ${signal.stop_loss:.2f}, Target: ${signal.take_profit:.2f}")
```

### 5. Backtest Strategy

```python
from agent_kit.backtesting import BacktestEngine
from datetime import datetime

# Create backtest engine
engine = BacktestEngine(
    initial_capital=100000,
    commission_rate=0.001,
    data_cost_per_month=50,
    compute_cost_per_month=100,
    api_cost_per_call=0.001
)

# Define strategy function (wraps your agent)
def strategy_func(historical_data):
    # Agent generates signals from historical data
    # Return list of signal dicts
    return agent.generate_signals(assets, historical_data).signals

# Run backtest
metrics = engine.run_backtest(
    strategy_func,
    historical_data,  # Dict of ticker -> OHLCV bars
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Print results
engine.print_summary(metrics)

# Check viability
if metrics.break_even_trades_per_month > 0 and metrics.sharpe_ratio > 1.0:
    print("✅ Strategy is profitable and ready for deployment")
else:
    print("❌ Strategy needs improvement")
```

---

## 🔧 Production Deployment

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PRODUCTION STACK                        │
├─────────────────────────────────────────────────────────────┤
│  1. DATA LAYER                                               │
│     - Betting: The Odds API, Pinnacle API                   │
│     - Trading: Alpha Vantage, Polygon, Binance              │
│     - Cache: Redis (30s TTL for odds, 1min for prices)      │
│                                                              │
│  2. AGENT LAYER                                              │
│     - PropBettingAgent (Celery workers)                      │
│     - AlgoTradingAgent (Celery workers)                      │
│     - Grok API for reasoning (rate limited)                  │
│                                                              │
│  3. RISK LAYER                                               │
│     - Circuit Breakers (halt if drawdown > max)             │
│     - Position Sizing (Kelly Criterion with fractional)     │
│     - Correlation Checks (max correlation limit)            │
│                                                              │
│  4. EXECUTION LAYER                                          │
│     - Betting: Bookmaker APIs (DraftKings, FanDuel)         │
│     - Trading: Alpaca, Interactive Brokers, Binance         │
│     - Paper trading mode for testing                         │
│                                                              │
│  5. MONITORING LAYER                                         │
│     - Prometheus + Grafana (metrics)                         │
│     - Sentry (error tracking)                                │
│     - Custom dashboards (ROI, Sharpe, drawdown)             │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Steps

#### 1. Set Up Infrastructure

```bash
# Using Docker Compose
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: agent_kit
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  celery_worker:
    build: .
    command: celery -A agent_kit.tasks worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
      - XAI_API_KEY=${XAI_API_KEY}
      - ODDS_API_KEY=${ODDS_API_KEY}
    depends_on:
      - redis
      - postgres

  celery_beat:
    build: .
    command: celery -A agent_kit.tasks beat --loglevel=info
    depends_on:
      - redis

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

volumes:
  redis_data:
  postgres_data:
EOF

docker-compose up -d
```

#### 2. Implement Circuit Breakers

```python
# src/agent_kit/monitoring/circuit_breaker.py
from datetime import datetime, timedelta
from typing import Callable

class CircuitBreaker:
    """Circuit breaker to halt trading on excessive losses."""
    
    def __init__(
        self,
        max_drawdown: float = 0.15,  # 15% max drawdown
        error_rate_threshold: float = 0.05,  # 5% error rate
        check_window: timedelta = timedelta(minutes=5)
    ):
        self.max_drawdown = max_drawdown
        self.error_rate_threshold = error_rate_threshold
        self.check_window = check_window
        
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.errors = []
        self.peak_value = 0.0
        self.current_value = 0.0
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            raise Exception("Circuit breaker OPEN - trading halted")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_error()
            raise e
    
    def update_portfolio_value(self, value: float):
        """Update portfolio value and check drawdown."""
        self.current_value = value
        if value > self.peak_value:
            self.peak_value = value
        
        drawdown = 1 - (self.current_value / self.peak_value)
        
        if drawdown >= self.max_drawdown:
            self.state = "OPEN"
            self._alert(f"Circuit breaker OPEN: drawdown {drawdown:.2%} >= {self.max_drawdown:.2%}")
    
    def _record_error(self):
        """Record error and check threshold."""
        self.errors.append(datetime.now())
        
        # Remove old errors
        cutoff = datetime.now() - self.check_window
        self.errors = [e for e in self.errors if e > cutoff]
        
        # Check error rate
        error_rate = len(self.errors) / 100  # Assume 100 calls per window
        if error_rate >= self.error_rate_threshold:
            self.state = "OPEN"
            self._alert(f"Circuit breaker OPEN: error rate {error_rate:.2%}")
    
    def _record_success(self):
        """Record successful call."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
    
    def _alert(self, message: str):
        """Send alert (email, Slack, PagerDuty)."""
        print(f"🚨 ALERT: {message}")
        # TODO: Integrate with alerting system

# Usage in agent
breaker = CircuitBreaker(max_drawdown=0.15)

def protected_trade():
    recommendations = agent.generate_signals(...)
    
    # Update circuit breaker with portfolio value
    breaker.update_portfolio_value(agent.portfolio_value)
    
    # Execute with protection
    breaker.call(execute_trades, recommendations)
```

#### 3. Add Monitoring & Observability

```python
# src/agent_kit/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics
trades_executed = Counter('agent_trades_total', 'Total trades executed', ['agent_type', 'outcome'])
trade_latency = Histogram('agent_trade_latency_seconds', 'Trade execution latency')
portfolio_value = Gauge('agent_portfolio_value', 'Current portfolio value', ['agent_name'])
sharpe_ratio = Gauge('agent_sharpe_ratio', 'Current Sharpe ratio', ['agent_name'])
drawdown = Gauge('agent_drawdown', 'Current drawdown', ['agent_name'])
edge_detected = Counter('agent_edges_detected', 'Edges detected', ['agent_type'])

# Usage
trades_executed.labels(agent_type='betting', outcome='win').inc()
portfolio_value.labels(agent_name='AlgoTrader1').set(105000)
```

#### 4. Deploy to Cloud (AWS/GCP/Azure)

```bash
# Kubernetes deployment example
kubectl apply -f k8s/agent-deployment.yaml

# Or serverless with AWS Lambda
serverless deploy --stage prod
```

#### 5. Set Up Alerting

```yaml
# prometheus/alerts.yml
groups:
  - name: agent_alerts
    rules:
      - alert: HighDrawdown
        expr: agent_drawdown > 0.10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Agent {{ $labels.agent_name }} drawdown > 10%"
      
      - alert: LowSharpeRatio
        expr: agent_sharpe_ratio < 0.5
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Agent {{ $labels.agent_name }} Sharpe < 0.5"
      
      - alert: HighErrorRate
        expr: rate(agent_trades_total{outcome="error"}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Agent error rate > 5%"
```

---

## 💡 Business Model & Unit Economics

### Revenue Streams

1. **SaaS Subscriptions**
   - Tier 1 (Starter): $99/month - 100 bets/month, basic strategies
   - Tier 2 (Pro): $499/month - 500 bets/month, advanced strategies
   - Tier 3 (Enterprise): $2,999/month - Unlimited, custom strategies

2. **Profit Sharing**
   - Take 20% of net profits generated by agents
   - Minimum $10k bankroll required

3. **White Label**
   - License agents to sportsbooks/hedge funds
   - $50k setup + $10k/month

### Cost Structure (Monthly)

```
Data Costs:           $200  (odds feeds, market data)
Compute (AWS):        $500  (EC2, Lambda, RDS)
LLM API (Grok):       $300  (assuming 100k calls/month @ $0.003/call)
Monitoring:           $100  (Datadog/Sentry)
---------------------------------------------------
Total Fixed Costs:   $1,100/month
```

### Break-Even Analysis

**Scenario 1: Prop Betting (Conservative)**
- Bankroll: $10,000
- Strategy: Value Betting (5% edge minimum)
- Kelly Criterion: 25% of full Kelly (conservative)
- Bets per day: 5
- Avg bet size: $200 (2% of bankroll)
- Expected edge: 6%
- Expected ROI per bet: $12
- Monthly revenue: $1,800 (5 bets/day × 30 days × $12)
- **Net profit: $700/month per customer**
- **Break-even: 2 customers**

**Scenario 2: Algo Trading (Moderate Risk)**
- Portfolio: $100,000
- Strategy: Mean Reversion
- Sharpe ratio: 1.5 (target)
- Annualized return: 15%
- Monthly return: 1.25%
- Expected profit: $1,250/month
- **After costs: $150/month per customer**
- **Break-even: 8 customers**

### Scalability

- **With 100 customers (50 betting, 50 trading)**
  - Revenue: $35,000 + $7,500 = $42,500/month
  - Costs: $1,100 + (compute scaling) = ~$2,500/month
  - **Net profit: $40,000/month**
  - **Annual: $480,000**

---

## ⚠️ Risk Management Checklist

Before deploying:

- [ ] **Backtest on 2+ years of data**
- [ ] **Walk-forward validation** (out-of-sample testing)
- [ ] **Set circuit breakers** (max drawdown, error rate)
- [ ] **Implement position sizing** (Kelly Criterion with fractional)
- [ ] **Add correlation limits** (max 0.5 for portfolio diversification)
- [ ] **Paper trade for 30 days** (no real money)
- [ ] **Set daily loss limits** (halt if lose > 5% in one day)
- [ ] **Monitor Sharpe ratio** (pause if < 0.5)
- [ ] **Log all decisions** (for audit and debugging)
- [ ] **Get legal review** (gambling laws vary by state)

---

## 🎓 Next Steps

### Immediate (Week 1)
1. Install `uv` and sync dependencies
2. Set up API keys (Grok, odds, market data)
3. Run local examples (betting and trading)
4. Backtest on mock data

### Short-term (Month 1)
1. Integrate real data APIs
2. Build ML models for probability estimation (betting)
3. Implement paper trading mode
4. Set up monitoring (Prometheus + Grafana)

### Medium-term (Month 2-3)
1. Deploy to cloud (AWS/GCP)
2. Launch MVP with 10 beta customers
3. Collect feedback and iterate
4. Build customer dashboard

### Long-term (Month 4-6)
1. Scale to 100+ customers
2. Add new industries (healthcare, logistics, etc.)
3. Build agent marketplace
4. Raise Series A 🚀

---

## 📚 Resources

- **Ontologies**: `assets/ontologies/betting.ttl`, `trading.ttl`
- **Agents**: `src/agent_kit/agents/prop_betting_agent.py`, `algo_trading_agent.py`
- **Tools**: `src/agent_kit/tools/betting_tools.py`, `trading_tools.py`
- **Factory**: `src/agent_kit/factories/agent_factory.py`
- **Backtesting**: `src/agent_kit/backtesting/backtest_engine.py`

---

## 🤝 Support

Questions? Open an issue or email support@agent-kit.io

**Let's make money with ontology-driven agents! 💰🚀**

