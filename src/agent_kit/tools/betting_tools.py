"""
Betting data pipeline tools with circuit breaker protection.

Tools for fetching odds, analyzing lines, and detecting arbitrage opportunities.
Integrates with sportsbook APIs (DraftKings, FanDuel, Pinnacle, etc.)

From first principles: Sportsbook APIs have rate limits—circuit breakers prevent
exhausting quotas and getting banned.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from agents import function_tool
from pydantic import BaseModel

from agent_kit.monitoring.circuit_breaker import with_circuit_breaker


class OddsData(BaseModel):
    """Odds data from sportsbook."""
    model_config = {'extra': 'forbid'}

    bookmaker: str
    event_id: str
    event_description: str
    market_type: str  # "moneyline", "spread", "total", "prop"
    selection: str  # "home", "away", "over", "under", player name
    odds: float  # Decimal odds
    line: float | None = None  # Line value for spreads/totals
    timestamp: datetime = datetime.now()


class ArbitrageOpportunity(BaseModel):
    """Arbitrage opportunity across bookmakers."""
    model_config = {'extra': 'forbid'}

    event_id: str
    event_description: str
    bookmaker1: str
    odds1: float
    selection1: str
    bookmaker2: str
    odds2: float
    selection2: str
    profit_margin: float  # % profit
    stake1: float  # $ to bet on side 1
    stake2: float  # $ to bet on side 2
    total_stake: float
    guaranteed_profit: float


@function_tool
@with_circuit_breaker(max_failures=5, reset_timeout=180)
def fetch_odds(
    sport: str = "basketball_nba",
    market: str = "h2h",
    bookmakers: str = "draftkings,fanduel,betmgm"
) -> list[dict]:
    """
    Fetch live odds from sportsbooks.

    Args:
        sport: Sport key (e.g., "basketball_nba", "soccer_epl", "americanfootball_nfl")
        market: Market type ("h2h" = moneyline, "spreads", "totals", "player_props")
        bookmakers: Comma-separated bookmaker keys

    Returns:
        List of odds data dictionaries

    Example:
        >>> odds = fetch_odds(sport="basketball_nba", market="h2h")
        >>> print(f"Found {len(odds)} games with odds")

    Note:
        In production, this integrates with The Odds API (theoddsapi.com)
        or direct bookmaker APIs. For now, returns mock data.
    """
    # TODO: Integrate with real API
    # import requests
    # api_key = os.getenv("ODDS_API_KEY")
    # response = requests.get(
    #     f"https://api.the-odds-api.com/v4/sports/{sport}/odds/",
    #     params={"apiKey": api_key, "regions": "us", "markets": market, "bookmakers": bookmakers}
    # )
    # return response.json()

    # Mock data for demo
    mock_odds = [
        {
            "bookmaker": "draftkings",
            "event_id": "lakers_vs_celtics_2025_11_23",
            "event_description": "Los Angeles Lakers vs Boston Celtics",
            "market_type": "moneyline",
            "selection": "Lakers",
            "odds": 2.10,
            "line": None,
            "timestamp": datetime.now().isoformat()
        },
        {
            "bookmaker": "fanduel",
            "event_id": "lakers_vs_celtics_2025_11_23",
            "event_description": "Los Angeles Lakers vs Boston Celtics",
            "market_type": "moneyline",
            "selection": "Lakers",
            "odds": 2.15,
            "line": None,
            "timestamp": datetime.now().isoformat()
        }
    ]

    return mock_odds


@function_tool
@with_circuit_breaker(max_failures=5, reset_timeout=180)
def fetch_player_props(
    sport: str = "basketball_nba",
    player_name: str | None = None
) -> list[dict]:
    """
    Fetch player proposition bets.

    Args:
        sport: Sport key
        player_name: Optional player name to filter (e.g., "LeBron James")

    Returns:
        List of player prop dictionaries

    Example:
        >>> props = fetch_player_props(sport="basketball_nba", player_name="LeBron James")
        >>> for prop in props:
        ...     print(f"{prop['description']}: {prop['odds']}")
    """
    # TODO: Integrate with Pinnacle, Betonline, or sportsbook APIs

    # Mock data
    mock_props = [
        {
            "bookmaker": "draftkings",
            "event_id": "lebron_points_2025_11_23",
            "event_description": "Lakers vs Celtics",
            "player": "LeBron James",
            "market_type": "player_points",
            "description": "LeBron James Over 25.5 Points",
            "selection": "over",
            "odds": 1.91,
            "line": 25.5,
            "timestamp": datetime.now().isoformat()
        },
        {
            "bookmaker": "fanduel",
            "event_id": "lebron_points_2025_11_23",
            "event_description": "Lakers vs Celtics",
            "player": "LeBron James",
            "market_type": "player_points",
            "description": "LeBron James Over 25.5 Points",
            "selection": "over",
            "odds": 1.95,
            "line": 25.5,
            "timestamp": datetime.now().isoformat()
        }
    ]

    if player_name:
        mock_props = [p for p in mock_props if player_name.lower()
                      in p["player"].lower()]

    return mock_props


@function_tool
def detect_arbitrage(
    odds_data: list[dict],
    min_profit_margin: float = 0.01
) -> list[dict]:
    """
    Detect arbitrage opportunities across bookmakers.

    Args:
        odds_data: List of odds data (from fetch_odds)
        min_profit_margin: Minimum profit margin to report (default 1%)

    Returns:
        List of arbitrage opportunities

    Example:
        >>> odds = fetch_odds()
        >>> arbs = detect_arbitrage(odds, min_profit_margin=0.02)
        >>> for arb in arbs:
        ...     print(f"Profit: {arb['profit_margin']:.2%}")

    Note:
        Arbitrage formula: 1/odds1 + 1/odds2 < 1 (profit exists)
    """
    arbitrage_ops = []

    # Group odds by event
    events: dict[str, list[dict]] = {}
    for odd in odds_data:
        event_id = odd.get("event_id")
        if event_id:
            if event_id not in events:
                events[event_id] = []
            events[event_id].append(odd)

    # Check for arbitrage within each event
    for event_id, event_odds in events.items():
        # Simple two-way arbitrage (home vs away, over vs under)
        for i, odd1 in enumerate(event_odds):
            for odd2 in event_odds[i+1:]:
                # Check if opposite sides (e.g., one home, one away)
                if odd1["selection"] != odd2["selection"]:
                    # Calculate arbitrage
                    implied1 = 1 / odd1["odds"]
                    implied2 = 1 / odd2["odds"]
                    total_implied = implied1 + implied2

                    if total_implied < 1.0:  # Arbitrage exists!
                        profit_margin = (1 / total_implied) - 1

                        if profit_margin >= min_profit_margin:
                            # Calculate stakes (assume $1000 total)
                            total_stake = 1000
                            stake1 = total_stake * implied1 / total_implied
                            stake2 = total_stake * implied2 / total_implied
                            guaranteed_profit = total_stake * profit_margin

                            arbitrage_ops.append({
                                "event_id": event_id,
                                "event_description": odd1.get("event_description", ""),
                                "bookmaker1": odd1["bookmaker"],
                                "odds1": odd1["odds"],
                                "selection1": odd1["selection"],
                                "bookmaker2": odd2["bookmaker"],
                                "odds2": odd2["odds"],
                                "selection2": odd2["selection"],
                                "profit_margin": profit_margin,
                                "stake1": stake1,
                                "stake2": stake2,
                                "total_stake": total_stake,
                                "guaranteed_profit": guaranteed_profit
                            })

    return arbitrage_ops


@function_tool
def calculate_implied_probability(odds: float, odds_format: str = "decimal") -> float:
    """
    Convert odds to implied probability.

    Args:
        odds: Odds value
        odds_format: "decimal", "american", or "fractional"

    Returns:
        Implied probability (0.0 to 1.0)

    Example:
        >>> prob = calculate_implied_probability(2.50, "decimal")
        >>> print(f"Implied probability: {prob:.2%}")
    """
    if odds_format == "decimal":
        return 1.0 / odds
    elif odds_format == "american":
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    elif odds_format == "fractional":
        # Parse fractional odds (e.g., "5/2")
        if isinstance(odds, str) and "/" in odds:
            num, denom = map(float, odds.split("/"))
            decimal_odds = 1 + (num / denom)
            return 1.0 / decimal_odds
        else:
            raise ValueError(f"Invalid fractional odds: {odds}")
    else:
        raise ValueError(f"Unknown odds format: {odds_format}")


@function_tool
def fetch_historical_betting_data(
    sport: str,
    start_date: str,
    end_date: str
) -> list[dict]:
    """
    Fetch historical betting data for backtesting.

    Args:
        sport: Sport key
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of historical game results with closing odds

    Example:
        >>> history = fetch_historical_betting_data("basketball_nba", "2024-01-01", "2024-12-31")
        >>> print(f"Fetched {len(history)} games")
    """
    # TODO: Integrate with historical odds providers (e.g., SportsBookReview, Pinnacle)

    # Mock data
    return [
        {
            "event_id": "game_123",
            "date": "2024-11-01",
            "home_team": "Lakers",
            "away_team": "Celtics",
            "home_score": 110,
            "away_score": 105,
            "closing_odds_home": 1.85,
            "closing_odds_away": 2.10
        }
    ]


# Export all tools
__all__ = [
    "fetch_odds",
    "fetch_player_props",
    "detect_arbitrage",
    "calculate_implied_probability",
    "fetch_historical_betting_data"
]
