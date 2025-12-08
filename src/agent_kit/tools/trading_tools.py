"""
Trading data pipeline tools with circuit breaker protection.

Tools for fetching market data, calculating indicators, and executing trades.
Integrates with financial data APIs (Alpha Vantage, Polygon, Binance, etc.)

From first principles: External APIs are unreliable—circuit breakers prevent
cascading failures by failing fast when error rates spike.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
from agents import function_tool
from pydantic import BaseModel

from agent_kit.monitoring.circuit_breaker import with_circuit_breaker


class MarketData(BaseModel):
    """Market data for an asset."""

    model_config = {"extra": "forbid"}

    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class TechnicalIndicators(BaseModel):
    """Technical indicators for an asset."""

    model_config = {"extra": "forbid"}

    ticker: str
    timestamp: datetime
    rsi: float | None = None  # Relative Strength Index
    macd: float | None = None  # MACD value
    macd_signal: float | None = None  # MACD signal line
    ema_20: float | None = None  # 20-period EMA
    ema_50: float | None = None  # 50-period EMA
    bollinger_upper: float | None = None
    bollinger_middle: float | None = None
    bollinger_lower: float | None = None


@function_tool
@with_circuit_breaker(max_failures=5, reset_timeout=120)
def fetch_market_data(
    ticker: str, interval: str = "1day", limit: int = 100
) -> list[dict]:
    """
    Fetch historical market data for an asset.

    Args:
        ticker: Asset ticker symbol (e.g., "AAPL", "BTC-USD")
        interval: Time interval ("1min", "5min", "1hour", "1day")
        limit: Number of bars to fetch

    Returns:
        List of OHLCV data dictionaries

    Example:
        >>> data = fetch_market_data("AAPL", interval="1day", limit=50)
        >>> print(f"Latest close: ${data[-1]['close']}")

    Note:
        In production, integrates with:
        - Stocks: Alpha Vantage, Polygon, Yahoo Finance
        - Crypto: Binance, Coinbase, Kraken APIs
        - Futures: Interactive Brokers, TD Ameritrade
    """
    # TODO: Integrate with real APIs
    # Example with yfinance:
    # import yfinance as yf
    # ticker_obj = yf.Ticker(ticker)
    # df = ticker_obj.history(period="3mo", interval=interval)
    # return df.to_dict('records')

    # Mock data
    mock_data = []
    base_price = 150.0

    for _ in range(limit):
        # Simulate price movement
        price_change = np.random.randn() * 2
        base_price = max(base_price + price_change, 1.0)

        mock_data.append(
            {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "open": base_price - 1,
                "high": base_price + 2,
                "low": base_price - 2,
                "close": base_price,
                "volume": 1000000 + int(np.random.randn() * 100000),
            }
        )

    return mock_data


@function_tool
def calculate_rsi(prices: list[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        prices: List of closing prices
        period: RSI period (default 14)

    Returns:
        RSI value (0 to 100)

    Example:
        >>> data = fetch_market_data("AAPL")
        >>> prices = [bar['close'] for bar in data]
        >>> rsi = calculate_rsi(prices)
        >>> print(f"RSI: {rsi:.2f}")
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral if not enough data

    # Calculate price changes
    deltas = np.diff(prices)

    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # Calculate average gain and loss
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi)


@function_tool
def calculate_macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> dict[str, float]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: List of closing prices
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line period

    Returns:
        Dict with "macd", "signal", and "histogram" values

    Example:
        >>> data = fetch_market_data("AAPL")
        >>> prices = [bar['close'] for bar in data]
        >>> macd_data = calculate_macd(prices)
        >>> print(f"MACD: {macd_data['macd']:.2f}")
    """
    if len(prices) < slow_period + signal_period:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    prices_array = np.array(prices)

    # Calculate EMAs
    ema_fast = _calculate_ema(prices_array, fast_period)
    ema_slow = _calculate_ema(prices_array, slow_period)

    # MACD line
    macd_line = ema_fast - ema_slow

    # Signal line (EMA of MACD)
    signal_line = _calculate_ema(macd_line, signal_period)

    # Histogram
    histogram = macd_line - signal_line

    return {
        "macd": float(macd_line[-1]),
        "signal": float(signal_line[-1]),
        "histogram": float(histogram[-1]),
    }


def _calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    """Calculate Exponential Moving Average."""
    alpha = 2 / (period + 1)
    ema = np.zeros_like(data)
    ema[0] = data[0]

    for i in range(1, len(data)):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]

    return ema


@function_tool
def calculate_bollinger_bands(
    prices: list[float], period: int = 20, std_dev: float = 2.0
) -> dict[str, float]:
    """
    Calculate Bollinger Bands.

    Args:
        prices: List of closing prices
        period: Moving average period
        std_dev: Number of standard deviations

    Returns:
        Dict with "upper", "middle", and "lower" band values

    Example:
        >>> data = fetch_market_data("AAPL")
        >>> prices = [bar['close'] for bar in data]
        >>> bands = calculate_bollinger_bands(prices)
        >>> print(f"Upper: ${bands['upper']:.2f}, Lower: ${bands['lower']:.2f}")
    """
    if len(prices) < period:
        current_price = prices[-1] if prices else 100.0
        return {"upper": current_price, "middle": current_price, "lower": current_price}

    prices_array = np.array(prices[-period:])

    # Middle band (SMA)
    middle = np.mean(prices_array)

    # Standard deviation
    std = np.std(prices_array)

    # Upper and lower bands
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    return {"upper": float(upper), "middle": float(middle), "lower": float(lower)}


@function_tool
def calculate_indicators(ticker: str, market_data: list[dict]) -> dict:
    """
    Calculate all technical indicators for an asset.

    Args:
        ticker: Asset ticker
        market_data: List of OHLCV data (from fetch_market_data)

    Returns:
        Dict with all indicators

    Example:
        >>> data = fetch_market_data("AAPL")
        >>> indicators = calculate_indicators("AAPL", data)
        >>> print(f"RSI: {indicators['RSI']:.2f}")
    """
    prices = [bar["close"] for bar in market_data]

    rsi = calculate_rsi(prices)
    macd_data = calculate_macd(prices)
    bollinger = calculate_bollinger_bands(prices)

    # EMAs
    ema_20 = float(_calculate_ema(np.array(prices), 20)[-1])
    ema_50 = (
        float(_calculate_ema(np.array(prices), 50)[-1]) if len(prices) >= 50 else ema_20
    )

    return {
        "ticker": ticker,
        "timestamp": market_data[-1]["timestamp"],
        "RSI": rsi,
        "MACD": macd_data["macd"],
        "MACD_Signal": macd_data["signal"],
        "MACD_Histogram": macd_data["histogram"],
        "EMA_20": ema_20,
        "EMA_50": ema_50,
        "Bollinger_Upper": bollinger["upper"],
        "Bollinger_Middle": bollinger["middle"],
        "Bollinger_Lower": bollinger["lower"],
    }


@function_tool
def calculate_volatility(
    prices: list[float], period: int = 20, annualize: bool = True
) -> float:
    """
    Calculate historical volatility.

    Args:
        prices: List of closing prices
        period: Lookback period
        annualize: If True, annualize volatility (multiply by sqrt(252))

    Returns:
        Volatility (standard deviation of returns)

    Example:
        >>> data = fetch_market_data("AAPL")
        >>> prices = [bar['close'] for bar in data]
        >>> vol = calculate_volatility(prices)
        >>> print(f"Annualized volatility: {vol:.2%}")
    """
    if len(prices) < period + 1:
        return 0.0

    prices_array = np.array(prices[-period - 1 :])
    returns = np.diff(prices_array) / prices_array[:-1]

    volatility = np.std(returns)

    if annualize:
        volatility *= np.sqrt(252)  # 252 trading days per year

    return float(volatility)


@function_tool
@with_circuit_breaker(max_failures=3, reset_timeout=300)  # Stricter for trades
def execute_trade(
    ticker: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    limit_price: float | None = None,
) -> dict:
    """
    Execute a trade (paper or live).

    Args:
        ticker: Asset ticker
        side: "buy" or "sell"
        quantity: Number of shares/contracts
        order_type: "market", "limit", "stop"
        limit_price: Limit price (for limit orders)

    Returns:
        Order execution details

    Example:
        >>> result = execute_trade("AAPL", "buy", 10, "market")
        >>> print(f"Order status: {result['status']}")

    Note:
        In production, integrates with broker APIs:
        - Alpaca, Interactive Brokers, TD Ameritrade (stocks)
        - Binance, Coinbase (crypto)
        For now, returns paper trading result.
    """
    # TODO: Integrate with broker API
    # Example with Alpaca:
    # from alpaca_trade_api import REST
    # api = REST(key_id, secret_key, base_url)
    # order = api.submit_order(
    #     symbol=ticker,
    #     qty=quantity,
    #     side=side,
    #     type=order_type,
    #     time_in_force='day'
    # )

    # Paper trading mock
    return {
        "order_id": f"order_{datetime.now().timestamp()}",
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        "limit_price": limit_price,
        "status": "filled",
        "filled_price": 150.0,  # Mock
        "timestamp": datetime.now().isoformat(),
    }


@function_tool
def calculate_sharpe_ratio(returns: list[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio.

    Args:
        returns: List of period returns
        risk_free_rate: Annual risk-free rate (default 2%)

    Returns:
        Sharpe ratio

    Example:
        >>> returns = [0.01, -0.02, 0.03, 0.01, -0.01]
        >>> sharpe = calculate_sharpe_ratio(returns)
        >>> print(f"Sharpe ratio: {sharpe:.2f}")
    """
    if len(returns) < 2:
        return 0.0

    returns_array = np.array(returns)

    mean_return = np.mean(returns_array)
    std_return = np.std(returns_array)

    if std_return == 0:
        return 0.0

    # Annualize
    annual_return = mean_return * 252  # 252 trading days
    annual_std = std_return * np.sqrt(252)

    sharpe = (annual_return - risk_free_rate) / annual_std

    return float(sharpe)


# Export all tools
__all__ = [
    "fetch_market_data",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "calculate_indicators",
    "calculate_volatility",
    "execute_trade",
    "calculate_sharpe_ratio",
]
