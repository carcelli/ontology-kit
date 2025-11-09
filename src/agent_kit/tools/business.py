# src/agent_kit/tools/business.py
from agents import function_tool
from typing import Dict

@function_tool
def predict() -> Dict:
    """Stub: Ontology-tied forecasting."""
    print("Forecasting...")
    return {'forecast': [100, 200]}

@function_tool
def optimize() -> Dict:
    """Stub: Find leverage points."""
    print("Optimizing...")
    return {'action': 'Increase outreach'}
