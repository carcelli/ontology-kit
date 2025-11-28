"""
Backtesting Engine with Unit Economics

Test agent strategies on historical data and calculate:
- Win rate, ROI, Sharpe ratio
- Unit economics (cost per trade, profit per customer)
- Risk metrics (max drawdown, VaR)
- Business viability (break-even analysis)
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from pydantic import BaseModel


class Trade(BaseModel):
    """Single trade executed during backtest."""
    timestamp: datetime
    ticker: str
    side: str  # "buy" or "sell"
    quantity: float
    entry_price: float
    exit_price: float | None = None
    exit_timestamp: datetime | None = None
    pnl: float = 0.0  # Profit/loss
    commission: float = 0.0

    def close_trade(self, exit_price: float, exit_timestamp: datetime, commission_rate: float = 0.001):
        """Close the trade and calculate P&L."""
        self.exit_price = exit_price
        self.exit_timestamp = exit_timestamp

        # Calculate raw P&L
        if self.side == "buy":
            raw_pnl = (exit_price - self.entry_price) * self.quantity
        else:  # sell (short)
            raw_pnl = (self.entry_price - exit_price) * self.quantity

        # Deduct commissions
        self.commission = (self.entry_price + exit_price) * self.quantity * commission_rate
        self.pnl = raw_pnl - self.commission


@dataclass
class BacktestMetrics:
    """Performance metrics from backtest."""
    # Returns
    total_return: float  # Total % return
    annualized_return: float

    # Risk
    sharpe_ratio: float
    max_drawdown: float
    var_95: float  # 95% Value at Risk

    # Trade stats
    num_trades: int
    win_rate: float  # % of profitable trades
    avg_win: float
    avg_loss: float
    profit_factor: float  # Total wins / total losses

    # Unit economics
    total_pnl: float
    total_commissions: float
    net_profit: float
    avg_pnl_per_trade: float
    cost_per_trade: float  # Including compute, data, commissions

    # Business metrics
    break_even_trades_per_month: int
    monthly_profit_potential: float
    roi_break_even_months: float


class BacktestEngine:
    """
    Backtest engine for agent strategies.

    Example:
        >>> from agent_kit.agents.algo_trading_agent import AlgoTradingAgent
        >>> agent = AlgoTradingAgent(...)
        >>> engine = BacktestEngine(initial_capital=100000, commission_rate=0.001)
        >>> metrics = engine.run_backtest(agent, historical_data, start_date, end_date)
        >>> print(f"Sharpe ratio: {metrics.sharpe_ratio:.2f}")
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,  # 0.1% per trade
        slippage: float = 0.0005,  # 0.05% slippage
        data_cost_per_month: float = 50.0,  # Data feed costs
        compute_cost_per_month: float = 100.0,  # Server costs
        api_cost_per_call: float = 0.001  # API costs (e.g., Grok)
    ):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Starting capital
            commission_rate: Commission per trade (as fraction)
            slippage: Slippage per trade (as fraction)
            data_cost_per_month: Monthly data costs
            compute_cost_per_month: Monthly compute costs
            api_cost_per_call: Cost per API call (e.g., LLM inference)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.data_cost_per_month = data_cost_per_month
        self.compute_cost_per_month = compute_cost_per_month
        self.api_cost_per_call = api_cost_per_call

        # State
        self.capital = initial_capital
        self.peak_capital = initial_capital
        self.trades: list[Trade] = []
        self.equity_curve: list[tuple[datetime, float]] = []

    def run_backtest(
        self,
        strategy_func: Callable[[dict], list[dict]],  # Function that generates signals
        historical_data: dict[str, list[dict]],  # ticker -> list of OHLCV bars
        start_date: datetime,
        end_date: datetime
    ) -> BacktestMetrics:
        """
        Run backtest on historical data.

        Args:
            strategy_func: Function that takes market data and returns signals
                          Example: lambda data: agent.generate_signals(data)
            historical_data: Dict of ticker -> OHLCV data
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            BacktestMetrics with performance statistics
        """
        # Reset state
        self.capital = self.initial_capital
        self.peak_capital = self.initial_capital
        self.trades = []
        self.equity_curve = [(start_date, self.capital)]

        # Track open positions
        open_positions: dict[str, Trade] = {}

        # Count API calls for cost calculation
        api_calls = 0

        # Simulate trading day by day
        # (In production, use proper event-driven backtester with bar-by-bar iteration)

        # Generate signals
        signals = strategy_func(historical_data)
        api_calls += 1  # One call to generate signals

        # Execute signals
        for signal in signals:
            ticker = signal.get("ticker") or signal.get("asset", {}).get("ticker")
            signal_type = signal.get("signal_type")
            position_size = signal.get("position_size", 0.0)

            if not ticker or not signal_type:
                continue

            # Get current price (use latest bar)
            if ticker not in historical_data:
                continue

            latest_bar = historical_data[ticker][-1]
            current_price = latest_bar["close"]

            # Apply slippage
            execution_price = current_price * (1 + self.slippage if signal_type == "BUY" else 1 - self.slippage)

            # Calculate quantity
            quantity = (self.capital * position_size) / execution_price

            if signal_type == "BUY" and ticker not in open_positions:
                # Open long position
                trade = Trade(
                    timestamp=datetime.now(),  # Use bar timestamp in production
                    ticker=ticker,
                    side="buy",
                    quantity=quantity,
                    entry_price=execution_price
                )
                open_positions[ticker] = trade

            elif signal_type == "SELL" and ticker in open_positions:
                # Close long position
                trade = open_positions[ticker]
                trade.close_trade(execution_price, datetime.now(), self.commission_rate)
                self.trades.append(trade)
                self.capital += trade.pnl
                del open_positions[ticker]

        # Close any remaining positions at end date
        for ticker, trade in open_positions.items():
            if ticker in historical_data:
                final_price = historical_data[ticker][-1]["close"]
                trade.close_trade(final_price, end_date, self.commission_rate)
                self.trades.append(trade)
                self.capital += trade.pnl

        # Calculate metrics
        return self._calculate_metrics(api_calls)

    def _calculate_metrics(self, api_calls: int) -> BacktestMetrics:
        """Calculate performance metrics."""
        if len(self.trades) == 0:
            return BacktestMetrics(
                total_return=0.0,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                var_95=0.0,
                num_trades=0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                total_pnl=0.0,
                total_commissions=0.0,
                net_profit=0.0,
                avg_pnl_per_trade=0.0,
                cost_per_trade=0.0,
                break_even_trades_per_month=0,
                monthly_profit_potential=0.0,
                roi_break_even_months=0.0
            )

        # Returns
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        annualized_return = total_return  # Simplified - assume 1 year backtest

        # Trade stats
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]

        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0.0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0.0
        avg_loss = np.mean([abs(t.pnl) for t in losing_trades]) if losing_trades else 0.0

        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = sum(abs(t.pnl) for t in losing_trades)
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        # P&L
        total_pnl = sum(t.pnl for t in self.trades)
        total_commissions = sum(t.commission for t in self.trades)

        # Unit economics
        api_costs = api_calls * self.api_cost_per_call
        monthly_overhead = self.data_cost_per_month + self.compute_cost_per_month

        # Assume backtest is 1 month for simplicity
        total_costs = total_commissions + api_costs + monthly_overhead
        net_profit = total_pnl - total_costs

        avg_pnl_per_trade = total_pnl / len(self.trades)
        cost_per_trade = total_costs / len(self.trades)

        # Business metrics
        # How many trades needed per month to break even?
        if avg_pnl_per_trade > cost_per_trade:
            break_even_trades = int(monthly_overhead / (avg_pnl_per_trade - cost_per_trade))
        else:
            break_even_trades = -1  # Not profitable

        # Monthly profit potential (assuming same win rate)
        trades_per_month = len(self.trades)  # Assume backtest is 1 month
        monthly_profit = (avg_pnl_per_trade - cost_per_trade) * trades_per_month

        # ROI break-even months (how long to recover initial capital)
        if monthly_profit > 0:
            roi_months = self.initial_capital / monthly_profit
        else:
            roi_months = float('inf')

        # Risk metrics
        returns = [t.pnl / self.initial_capital for t in self.trades]
        sharpe_ratio = self._calculate_sharpe(returns)
        max_drawdown = self._calculate_max_drawdown()
        var_95 = np.percentile(returns, 5) if returns else 0.0

        return BacktestMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            num_trades=len(self.trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_pnl=total_pnl,
            total_commissions=total_commissions,
            net_profit=net_profit,
            avg_pnl_per_trade=avg_pnl_per_trade,
            cost_per_trade=cost_per_trade,
            break_even_trades_per_month=break_even_trades,
            monthly_profit_potential=monthly_profit,
            roi_break_even_months=roi_months
        )

    def _calculate_sharpe(self, returns: list[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Annualize
        annual_return = mean_return * 252
        annual_std = std_return * np.sqrt(252)

        return (annual_return - risk_free_rate) / annual_std

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if not self.equity_curve:
            return 0.0

        equity_values = [eq[1] for eq in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0.0

        for value in equity_values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def print_summary(self, metrics: BacktestMetrics):
        """Print backtest summary."""
        print("=" * 60)
        print("BACKTEST SUMMARY")
        print("=" * 60)
        print("\n📊 PERFORMANCE METRICS")
        print(f"  Total Return: {metrics.total_return:.2%}")
        print(f"  Annualized Return: {metrics.annualized_return:.2%}")
        print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {metrics.max_drawdown:.2%}")
        print(f"  95% VaR: {metrics.var_95:.2%}")

        print("\n📈 TRADE STATISTICS")
        print(f"  Number of Trades: {metrics.num_trades}")
        print(f"  Win Rate: {metrics.win_rate:.2%}")
        print(f"  Avg Win: ${metrics.avg_win:.2f}")
        print(f"  Avg Loss: ${metrics.avg_loss:.2f}")
        print(f"  Profit Factor: {metrics.profit_factor:.2f}")

        print("\n💰 UNIT ECONOMICS")
        print(f"  Total P&L: ${metrics.total_pnl:.2f}")
        print(f"  Total Commissions: ${metrics.total_commissions:.2f}")
        print(f"  Net Profit: ${metrics.net_profit:.2f}")
        print(f"  Avg P&L per Trade: ${metrics.avg_pnl_per_trade:.2f}")
        print(f"  Cost per Trade: ${metrics.cost_per_trade:.2f}")

        print("\n🚀 BUSINESS VIABILITY")
        if metrics.break_even_trades_per_month > 0:
            print(f"  Break-Even Trades/Month: {metrics.break_even_trades_per_month}")
        else:
            print("  Break-Even: ⚠️  NOT PROFITABLE")
        print(f"  Monthly Profit Potential: ${metrics.monthly_profit_potential:.2f}")
        if metrics.roi_break_even_months < float('inf'):
            print(f"  ROI Break-Even: {metrics.roi_break_even_months:.1f} months")
        else:
            print("  ROI Break-Even: ⚠️  NEVER (negative ROI)")
        print("=" * 60)


# Example usage
if __name__ == "__main__":
    # Mock strategy function
    def mock_strategy(data: dict) -> list[dict]:
        """Generate random signals for testing."""
        signals = []
        for ticker in data.keys():
            signals.append({
                "ticker": ticker,
                "signal_type": "BUY",
                "position_size": 0.1
            })
        return signals

    # Mock historical data
    mock_data = {
        "AAPL": [
            {"timestamp": "2024-01-01", "open": 150, "high": 155, "low": 148, "close": 152, "volume": 1000000},
            {"timestamp": "2024-01-02", "open": 152, "high": 158, "low": 151, "close": 157, "volume": 1100000},
        ],
        "MSFT": [
            {"timestamp": "2024-01-01", "open": 300, "high": 305, "low": 298, "close": 302, "volume": 800000},
            {"timestamp": "2024-01-02", "open": 302, "high": 308, "low": 300, "close": 306, "volume": 850000},
        ]
    }

    # Run backtest
    engine = BacktestEngine(initial_capital=100000)
    metrics = engine.run_backtest(
        mock_strategy,
        mock_data,
        datetime(2024, 1, 1),
        datetime(2024, 1, 31)
    )

    engine.print_summary(metrics)


