"""
Prop Betting Agent - Edge detection and Kelly Criterion betting.

Uses ontology to:
1. Query risk rules and strategies
2. Detect edges (true_prob > implied_prob)
3. Size bets with Kelly Criterion
4. Enforce bankroll management constraints
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agent_kit.agents.base import GrokAgent, GrokConfig
from agent_kit.ontology.loader import OntologyLoader


class PropBet(BaseModel):
    """Proposition bet with odds and metadata."""
    event_id: str
    description: str  # e.g., "LeBron James Over 25.5 Points"
    bookmaker: str
    odds: float  # Decimal odds (2.50 = +150 American)
    line: float | None = None  # Line value for over/under props

    @property
    def implied_probability(self) -> float:
        """Convert odds to implied probability."""
        return 1.0 / self.odds


class BettingEdge(BaseModel):
    """Detected edge with bet recommendation."""
    prop_bet: PropBet
    true_probability: float  # Agent's estimated probability
    edge: float  # true_prob - implied_prob
    kelly_fraction: float  # Optimal bet size (% of bankroll)
    confidence: float  # Agent confidence (0.0 to 1.0)
    strategy: str  # e.g., "ValueBetting"


class BettingRecommendation(BaseModel):
    """Final betting recommendation after risk checks."""
    edges: list[BettingEdge]
    total_exposure: float  # Sum of all bet sizes
    expected_roi: float  # Expected return on investment
    risk_adjusted_exposure: float  # After applying risk rules
    passed_risk_checks: bool
    risk_violations: list[str] = []


class PropBettingAgent(GrokAgent):
    """
    Ontology-driven prop betting agent with edge detection.

    Example:
        >>> loader = OntologyLoader('assets/ontologies/betting.ttl')
        >>> loader.load()
        >>> agent = PropBettingAgent(loader, bankroll=10000)
        >>> recommendations = agent.analyze_props(prop_bets)
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        bankroll: float = 10000.0,
        strategy: str = "ValueBetting",
        grok_config: GrokConfig | None = None,
        **kwargs
    ):
        """
        Initialize prop betting agent.

        Args:
            ontology: Loaded ontology with betting.ttl
            bankroll: Current bankroll in dollars
            strategy: Strategy IRI (e.g., "ValueBetting", "LineShopping")
            grok_config: Optional Grok configuration
            **kwargs: Additional BaseAgent arguments
        """
        self.ontology = ontology
        self.bankroll = bankroll
        self.strategy = strategy
        self.risk_rules = self._load_risk_rules()

        # Generate ontology-driven instructions
        instructions = self._generate_betting_instructions()

        super().__init__(
            name="PropBettingAgent",
            ontology=ontology,
            system_prompt=instructions,
            grok_config=grok_config or GrokConfig(),
            **kwargs
        )

    def _load_risk_rules(self) -> dict[str, Any]:
        """Query ontology for risk rules associated with strategy."""
        sparql = f"""
            PREFIX bet: <http://agent-kit.com/ontology/betting#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            SELECT ?maxBetSize ?minEdge ?dailyLimit
            WHERE {{
                bet:{self.strategy} bet:enforcesRule ?rule .
                ?rule bet:maxBetSize ?maxBetSize ;
                      bet:minEdgeThreshold ?minEdge ;
                      bet:dailyBetLimit ?dailyLimit .
            }}
        """
        results = list(self.ontology.graph.query(sparql))
        if not results:
            # Default to conservative if strategy not found
            return {
                "max_bet_size": 0.02,
                "min_edge": 0.05,
                "daily_limit": 10
            }

        row = results[0]
        return {
            "max_bet_size": float(row.maxBetSize),
            "min_edge": float(row.minEdge),
            "daily_limit": int(row.dailyLimit)
        }

    def _generate_betting_instructions(self) -> str:
        """Generate instructions from ontology."""
        sparql = """
            PREFIX bet: <http://agent-kit.com/ontology/betting#>
            PREFIX core: <http://agent-kit.com/ontology/core#>

            SELECT ?instructions
            WHERE {
                bet:PropBettingAgent core:hasInstructions ?instructions .
            }
        """
        results = list(self.ontology.graph.query(sparql))
        if results:
            return str(results[0].instructions)

        # Fallback instructions
        return """You are a professional sports betting analyst.
Analyze prop bets, detect edges, and recommend bets using Kelly Criterion."""

    def calculate_kelly_fraction(self, true_prob: float, odds: float) -> float:
        """
        Calculate optimal bet size using Kelly Criterion.

        Formula: f = (p*odds - 1) / (odds - 1)
        where:
            f = fraction of bankroll to bet
            p = true probability
            odds = decimal odds
        """
        if odds <= 1.0 or true_prob <= 0.0:
            return 0.0

        kelly = (true_prob * odds - 1) / (odds - 1)

        # Apply fractional Kelly (25% of full Kelly for safety)
        fractional_kelly = kelly * 0.25

        # Cap at max bet size from risk rules
        return min(fractional_kelly, self.risk_rules["max_bet_size"])

    def detect_edge(self, prop_bet: PropBet, true_probability: float, confidence: float) -> BettingEdge | None:
        """
        Detect if there's a betting edge.

        Args:
            prop_bet: The proposition bet
            true_probability: Agent's estimated probability
            confidence: Agent confidence in the estimate

        Returns:
            BettingEdge if edge exists, None otherwise
        """
        implied_prob = prop_bet.implied_probability
        edge = true_probability - implied_prob

        # Check if edge meets minimum threshold
        if edge < self.risk_rules["min_edge"]:
            return None

        kelly_fraction = self.calculate_kelly_fraction(true_probability, prop_bet.odds)

        # If Kelly is negative or zero, no bet
        if kelly_fraction <= 0:
            return None

        return BettingEdge(
            prop_bet=prop_bet,
            true_probability=true_probability,
            edge=edge,
            kelly_fraction=kelly_fraction,
            confidence=confidence,
            strategy=self.strategy
        )

    def validate_risk_constraints(self, edges: list[BettingEdge]) -> tuple[bool, list[str]]:
        """
        Validate betting recommendations against risk rules.

        Returns:
            (passed, violations)
        """
        violations = []

        # Check daily bet limit
        if len(edges) > self.risk_rules["daily_limit"]:
            violations.append(
                f"Exceeds daily limit: {len(edges)} bets > {self.risk_rules['daily_limit']}"
            )

        # Check total exposure
        total_exposure = sum(edge.kelly_fraction for edge in edges)
        if total_exposure > 0.25:  # Never risk more than 25% of bankroll in one session
            violations.append(
                f"Total exposure too high: {total_exposure:.2%} > 25%"
            )

        # Check individual bet sizes
        for edge in edges:
            if edge.kelly_fraction > self.risk_rules["max_bet_size"]:
                violations.append(
                    f"Bet size exceeds limit: {edge.kelly_fraction:.2%} > "
                    f"{self.risk_rules['max_bet_size']:.2%}"
                )

        return (len(violations) == 0, violations)

    def analyze_props(
        self,
        prop_bets: list[PropBet],
        true_probabilities: dict[str, float],
        confidence_scores: dict[str, float]
    ) -> BettingRecommendation:
        """
        Analyze a batch of prop bets and generate recommendations.

        Args:
            prop_bets: List of proposition bets
            true_probabilities: Dict mapping event_id -> agent's probability
            confidence_scores: Dict mapping event_id -> confidence

        Returns:
            BettingRecommendation with validated edges
        """
        edges = []

        for prop_bet in prop_bets:
            true_prob = true_probabilities.get(prop_bet.event_id)
            confidence = confidence_scores.get(prop_bet.event_id)

            if true_prob is None or confidence is None:
                continue

            edge = self.detect_edge(prop_bet, true_prob, confidence)
            if edge:
                edges.append(edge)

        # Sort by edge * confidence (best opportunities first)
        edges.sort(key=lambda e: e.edge * e.confidence, reverse=True)

        # Validate risk constraints
        passed_risk, violations = self.validate_risk_constraints(edges)

        # Calculate expected ROI
        expected_roi = sum(
            edge.edge * edge.kelly_fraction * self.bankroll
            for edge in edges
        )

        total_exposure = sum(edge.kelly_fraction for edge in edges)
        risk_adjusted_exposure = total_exposure if passed_risk else 0.0

        return BettingRecommendation(
            edges=edges,
            total_exposure=total_exposure,
            expected_roi=expected_roi,
            risk_adjusted_exposure=risk_adjusted_exposure,
            passed_risk_checks=passed_risk,
            risk_violations=violations
        )

    def execute_grok_analysis(self, task_description: str, prop_bets_data: dict) -> BettingRecommendation:
        """
        Use Grok to analyze props with full observe-plan-act-reflect loop.

        This leverages the GrokAgent's reasoning capabilities to:
        1. Observe: Query ontology for betting strategies and historical patterns
        2. Plan: Generate analysis plan (which models to use, features to extract)
        3. Act: Execute analysis and compute probabilities
        4. Reflect: Critique results and adjust confidence scores

        Args:
            task_description: Natural language task (e.g., "Analyze NBA player props for tonight")
            prop_bets_data: Raw prop bet data from sportsbooks

        Returns:
            BettingRecommendation after full Grok analysis
        """
        # This would call the parent GrokAgent's run() method
        # For now, stub implementation - you'd integrate with actual Grok API

        # Stub: Extract props from data
        prop_bets = [
            PropBet(**bet_dict) for bet_dict in prop_bets_data.get("props", [])
        ]

        # Stub: Use Grok to generate probabilities
        # In production, this calls Grok with:
        # - Historical data
        # - Player stats
        # - Injury reports
        # - Betting market movements

        true_probabilities = {}
        confidence_scores = {}

        for prop in prop_bets:
            # Placeholder - Grok would return these
            true_probabilities[prop.event_id] = 0.55  # Example
            confidence_scores[prop.event_id] = 0.75

        return self.analyze_props(prop_bets, true_probabilities, confidence_scores)


