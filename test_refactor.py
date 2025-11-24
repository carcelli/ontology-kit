
import sys
import os

sys.path.insert(0, os.getcwd() + "/src")

from agent_kit.agents.business_agents import ForecastAgent, OptimizerAgent
from agent_kit.agents.base import AgentTask, AgentActionResult

def test_forecast_agent():
    print("Testing ForecastAgent...")
    agent = ForecastAgent()
    task = AgentTask(prompt="Test forecast")
    result = agent.run(task)
    print(f"Result: {result.result}")
    print("Success!")

def test_optimizer_agent():
    print("\nTesting OptimizerAgent...")
    agent = OptimizerAgent()
    # Mock previous result for context if needed, but OptimizerAgent.observe uses task.parameters
    task = AgentTask(prompt="Test optimize", parameters={"previous_artifacts": {"forecast_values": [100, 110, 120]}})
    result = agent.run(task)
    print(f"Result: {result.result}")
    print("Success!")

if __name__ == "__main__":
    test_forecast_agent()
    test_optimizer_agent()

