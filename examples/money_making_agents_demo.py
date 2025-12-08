"""
Money-Making Agents Demo - Complete System Integration

Demonstrates:
1. Prop betting agent with edge detection
2. Algo trading agent with risk management
3. Backtesting with unit economics
4. Tool organization and discovery
5. Circuit breakers and monitoring

Run: uv run python examples/money_making_agents_demo.py
"""

import os
from datetime import datetime

# Set up environment
os.environ.setdefault("OPENAI_API_KEY", "demo-key")
os.environ.setdefault("XAI_API_KEY", "demo-key")

from agent_kit.agents.algo_trading_agent import AlgoTradingAgent, Asset
from agent_kit.agents.prop_betting_agent import PropBet, PropBettingAgent
from agent_kit.backtesting import BacktestEngine
from agent_kit.factories import AgentFactory
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.tool_registry import ToolCategory, get_global_registry


def demo_tool_organization():
    """Demo: Tool organization and discovery."""
    print("=" * 70)
    print("TOOL ORGANIZATION DEMO")
    print("=" * 70)

    registry = get_global_registry()

    # List all tools
    print("\n📦 ALL REGISTERED TOOLS:")
    all_tools = registry.list_all_tools()
    for name, metadata in all_tools.items():
        print(
            f"  • {name:30} [{metadata['category']:15}] "
            f"${metadata['cost']:.4f}, {metadata['latency_ms']:4}ms"
        )

    # Get betting tools
    print("\n🎲 BETTING TOOLS:")
    betting_tools = registry.get_tools_by_category(ToolCategory.BETTING)
    print(f"  Found {len(betting_tools)} tools:")
    for tool in betting_tools:
        print(f"    - {tool.__name__}")

    # Get trading tools
    print("\n📈 TRADING TOOLS:")
    trading_tools = registry.get_tools_by_category(ToolCategory.TRADING)
    print(f"  Found {len(trading_tools)} tools:")
    for tool in trading_tools:
        print(f"    - {tool.__name__}")

    # Filter by cost
    print("\n💰 LOW-COST TOOLS (< $0.01):")
    cheap_tools = registry.filter_tools(max_cost=0.01)
    for tool in cheap_tools:
        print(f"    - {tool.__name__}")

    # Estimate costs
    print("\n💵 COST ESTIMATION:")
    betting_workflow = ["fetch_odds", "fetch_player_props", "detect_arbitrage"]
    cost = registry.estimate_cost(betting_workflow)
    print(f"  Betting workflow: ${cost:.4f}")

    trading_workflow = ["fetch_market_data", "calculate_indicators", "execute_trade"]
    cost = registry.estimate_cost(trading_workflow)
    print(f"  Trading workflow: ${cost:.4f}")


def demo_prop_betting_agent():
    """Demo: Prop betting agent with edge detection."""
    print("\n" + "=" * 70)
    print("PROP BETTING AGENT DEMO")
    print("=" * 70)

    # Load ontology
    loader = OntologyLoader("assets/ontologies/betting.ttl")
    loader.load()

    # Create agent
    agent = PropBettingAgent(ontology=loader, bankroll=10000.0, strategy="ValueBetting")

    print(f"\n✅ Created {agent.name}")
    print(f"  Bankroll: ${agent.bankroll:,.2f}")
    print(f"  Strategy: {agent.strategy}")
    print("  Risk Rules:")
    print(f"    - Max bet size: {agent.risk_rules['max_bet_size']:.1%}")
    print(f"    - Min edge: {agent.risk_rules['min_edge']:.1%}")
    print(f"    - Daily limit: {agent.risk_rules['daily_limit']} bets")

    # Mock prop bets
    print("\n📊 ANALYZING PROP BETS:")
    prop_bets = [
        PropBet(
            event_id="lebron_points",
            description="LeBron James Over 25.5 Points",
            bookmaker="DraftKings",
            odds=1.91,
        ),
        PropBet(
            event_id="curry_threes",
            description="Steph Curry Over 4.5 Three-Pointers",
            bookmaker="FanDuel",
            odds=2.10,
        ),
    ]

    # Agent's probability estimates (in production, from ML models)
    true_probabilities = {
        "lebron_points": 0.60,  # Agent thinks 60% chance
        "curry_threes": 0.55,
    }

    confidence_scores = {
        "lebron_points": 0.85,  # 85% confidence
        "curry_threes": 0.75,
    }

    # Analyze
    recommendations = agent.analyze_props(
        prop_bets, true_probabilities, confidence_scores
    )

    print(f"\n  Found {len(recommendations.edges)} edges:")
    for edge in recommendations.edges:
        print(f"    • {edge.prop_bet.description}")
        print(
            f"      Bookmaker odds: {edge.prop_bet.odds:.2f} "
            f"(implied prob: {edge.prop_bet.implied_probability:.2%})"
        )
        print(f"      Agent probability: {edge.true_probability:.2%}")
        print(f"      Edge: {edge.edge:.2%}")
        print(
            f"      Kelly bet size: {edge.kelly_fraction:.2%} of bankroll "
            f"(${edge.kelly_fraction * agent.bankroll:.2f})"
        )
        print(f"      Confidence: {edge.confidence:.1%}")

    print(f"\n  Total exposure: {recommendations.total_exposure:.2%} of bankroll")
    print(f"  Expected ROI: ${recommendations.expected_roi:.2f}")
    print(
        f"  Risk checks: {'✅ PASSED' if recommendations.passed_risk_checks else '❌ FAILED'}"
    )

    if not recommendations.passed_risk_checks:
        print("  Violations:")
        for violation in recommendations.risk_violations:
            print(f"    - {violation}")


def demo_algo_trading_agent():
    """Demo: Algo trading agent with risk management."""
    print("\n" + "=" * 70)
    print("ALGO TRADING AGENT DEMO")
    print("=" * 70)

    # Load ontology
    loader = OntologyLoader("assets/ontologies/trading.ttl")
    loader.load()

    # Create agent
    agent = AlgoTradingAgent(
        ontology=loader, portfolio_value=100000.0, strategy="MeanReversion"
    )

    print(f"\n✅ Created {agent.name}")
    print(f"  Portfolio: ${agent.portfolio_value:,.2f}")
    print(f"  Strategy: {agent.strategy}")
    print("  Risk Rules:")
    print(f"    - Max position size: {agent.risk_rules['max_position_size']:.1%}")
    print(f"    - Max drawdown: {agent.risk_rules['max_drawdown']:.1%}")
    print(f"    - Min Sharpe ratio: {agent.risk_rules['min_sharpe_ratio']:.2f}")
    print(f"    - Stop loss: {agent.risk_rules['stop_loss_percent']:.1%}")

    # Mock assets
    print("\n📊 ANALYZING ASSETS:")
    assets = [
        Asset(ticker="AAPL", current_price=150.0, volatility=0.25),
        Asset(ticker="MSFT", current_price=300.0, volatility=0.22),
    ]

    # Mock market data with indicators
    market_data = {
        "AAPL": {"indicators": {"RSI": 28, "MACD": -0.5}},  # Oversold
        "MSFT": {"indicators": {"RSI": 45, "MACD": 0.2}},  # Neutral
    }

    # Generate signals
    recommendations = agent.generate_signals(assets, market_data)

    print(f"\n  Generated {len(recommendations.signals)} signals:")
    for signal in recommendations.signals:
        print(f"    • {signal.asset.ticker} - {signal.signal_type}")
        print(f"      Entry: ${signal.asset.current_price:.2f}")
        print(f"      Stop loss: ${signal.stop_loss:.2f}")
        print(f"      Take profit: ${signal.take_profit:.2f}")
        print(
            f"      Position size: {signal.position_size:.2%} "
            f"(${signal.position_size * agent.portfolio_value:.2f})"
        )
        print(f"      Signal strength: {signal.signal_strength:.1%}")
        print(f"      Expected return: {signal.expected_return:+.2%}")

    print("\n  Portfolio Metrics:")
    print(
        f"    - Current drawdown: {recommendations.portfolio_metrics.current_drawdown:.2%}"
    )
    print(
        f"    - Total exposure: {recommendations.portfolio_metrics.total_exposure:.2%}"
    )
    print(
        f"    - Risk checks: {'✅ PASSED' if recommendations.passed_risk_checks else '❌ FAILED'}"
    )

    if recommendations.circuit_breaker_triggered:
        print("    - ⚠️  CIRCUIT BREAKER TRIGGERED - TRADING HALTED")


def demo_backtesting():
    """Demo: Backtesting with unit economics."""
    print("\n" + "=" * 70)
    print("BACKTESTING DEMO")
    print("=" * 70)

    # Create backtest engine
    engine = BacktestEngine(
        initial_capital=100000,
        commission_rate=0.001,
        data_cost_per_month=50,
        compute_cost_per_month=100,
        api_cost_per_call=0.001,
    )

    print("\n✅ Created BacktestEngine")
    print(f"  Initial capital: ${engine.initial_capital:,.2f}")
    print(f"  Commission rate: {engine.commission_rate:.2%}")
    print(
        f"  Monthly overhead: ${engine.data_cost_per_month + engine.compute_cost_per_month:.2f}"
    )

    # Mock strategy
    def mock_strategy(data):
        return [
            {"ticker": "AAPL", "signal_type": "BUY", "position_size": 0.1},
            {"ticker": "MSFT", "signal_type": "BUY", "position_size": 0.1},
        ]

    # Mock historical data
    mock_data = {
        "AAPL": [
            {"timestamp": "2024-01-01", "close": 150},
            {"timestamp": "2024-01-31", "close": 165},  # 10% gain
        ],
        "MSFT": [
            {"timestamp": "2024-01-01", "close": 300},
            {"timestamp": "2024-01-31", "close": 315},  # 5% gain
        ],
    }

    # Run backtest
    metrics = engine.run_backtest(
        mock_strategy, mock_data, datetime(2024, 1, 1), datetime(2024, 1, 31)
    )

    # Print results
    engine.print_summary(metrics)

    # Business decision
    print("\n📊 BUSINESS VIABILITY ANALYSIS:")
    if metrics.net_profit > 0 and metrics.sharpe_ratio > 1.0:
        print("  ✅ STRATEGY IS VIABLE")
        print(f"     - Net profit: ${metrics.net_profit:.2f}/month")
        print(f"     - ROI break-even: {metrics.roi_break_even_months:.1f} months")
        print(f"     - Sharpe ratio: {metrics.sharpe_ratio:.2f}")
    else:
        print("  ❌ STRATEGY NOT VIABLE")
        print("     - Needs optimization or different strategy")


def demo_agent_factory():
    """Demo: Agent factory with ontology-driven tool discovery."""
    print("\n" + "=" * 70)
    print("AGENT FACTORY DEMO")
    print("=" * 70)

    # Load betting ontology
    loader = OntologyLoader("assets/ontologies/betting.ttl")
    loader.load()

    factory = AgentFactory(loader)

    # List available agents
    print("\n🤖 AVAILABLE AGENTS:")
    agents = factory.list_available_agents()
    for iri, metadata in agents.items():
        print(f"  • {metadata.get('label', iri)}")

    # Create agent from factory
    print("\n✨ CREATING AGENT FROM FACTORY:")
    agent = factory.create_agent(
        "bet:PropBettingAgent", bankroll=25000, strategy="LineShopping"
    )
    print(f"  Created: {agent.name}")
    print(f"  Bankroll: ${agent.bankroll:,.2f}")
    print(f"  Strategy: {agent.strategy}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "MONEY-MAKING AGENTS DEMO" + " " * 29 + "║")
    print("║" + " " * 10 + "Prop Betting + Algo Trading + Ontologies" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")

    demo_tool_organization()
    demo_prop_betting_agent()
    demo_algo_trading_agent()
    demo_backtesting()
    demo_agent_factory()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE ✅")
    print("=" * 70)
    print("\n📚 Next Steps:")
    print("  1. Set up API keys (ODDS_API_KEY, ALPHAVANTAGE_API_KEY)")
    print("  2. Integrate real data pipelines")
    print("  3. Deploy agents with monitoring")
    print("  4. Scale across industries (add new ontologies)")
    print("\n💡 Create agents for ANY industry:")
    print("  - Supply chain optimization")
    print("  - Healthcare diagnosis")
    print("  - Real estate valuation")
    print("  - Energy trading")
    print("  - Just add a .ttl ontology and tools!")
    print()


if __name__ == "__main__":
    main()
