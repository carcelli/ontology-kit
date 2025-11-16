# src/agent_kit/tools/business.py

from agents import function_tool


@function_tool
def predict() -> dict:
    """Stub: Ontology-tied forecasting."""
    print("Forecasting...")
    return {'forecast': [100, 200]}

@function_tool
def optimize() -> dict:
    """Stub: Find leverage points."""
    print("Optimizing...")
    return {'action': 'Increase outreach'}
