"""
Example 5: Hybrid Orchestration (Custom + OpenAI SDK)

Demonstrates coexistence of:
1. Custom BaseAgent (ontology-driven routing, SPARQL queries)
2. OpenAI SDK Agent (structured outputs, handoffs)

Shows how to use each for their strengths:
- Custom: Complex reasoning with ontology context
- SDK: Structured data extraction, deterministic pipelines
"""

import asyncio

from agent_kit.adapters.openai_sdk import OPENAI_SDK_AVAILABLE
from agent_kit.agents.base import AgentTask
from agent_kit.agents.business_agents import ForecastAgent, OptimizerAgent
from agent_kit.ontology.loader import OntologyLoader

if OPENAI_SDK_AVAILABLE:
    from agents import Agent as SDKAgent

    from agent_kit.adapters.openai_sdk import OpenAISDKAdapter


async def main():
    print('=' * 70)
    print('Agent Kit - Example 5: Hybrid Orchestration')
    print('=' * 70)

    ontology_path = 'assets/ontologies/business.ttl'
    ontology_loader = OntologyLoader(ontology_path)
    ontology_loader.load()

    # 1. Custom BaseAgent for ontology-driven forecasting
    print('\n📈 Part 1: Custom BaseAgent (Ontology-Driven)')
    print('-' * 70)
    forecast_agent = ForecastAgent(
        name='ForecastAgent', description='Generates revenue forecasts using ARIMA', ontology_loader=ontology_loader
    )
    task1 = AgentTask(description='Forecast Q1-Q3 revenue for Sunshine Bakery', parameters={'business_name': 'Sunshine Bakery'})
    result1 = forecast_agent.run(task1)
    print(f'Agent: {forecast_agent.name}')
    print(f'Result: {result1.action_result.summary}')
    print(f'Artifacts: {result1.action_result.artifacts}')

    # 2. OpenAI SDK Agent for structured outputs (if available)
    if OPENAI_SDK_AVAILABLE:
        print('\n🤖 Part 2: OpenAI SDK Agent (Structured Outputs)')
        print('-' * 70)

        # Create SDK agent with structured output
        from pydantic import BaseModel

        class RevenueInsight(BaseModel):
            business: str
            quarter: str
            predicted_revenue: float
            confidence: str

        sdk_agent = SDKAgent(
            name='InsightExtractor',
            instructions='Extract structured revenue insights from text. Use reasonable estimates if exact data unavailable.',
            model='gpt-4.1',
            output_type=RevenueInsight,
        )

        # Wrap with ontology adapter
        adapter = OpenAISDKAdapter(sdk_agent=sdk_agent, ontology_loader=ontology_loader, enrich_instructions=True)

        # Run with ontology grounding
        task2_description = (
            f"Based on this forecast: '{result1.action_result.summary}', " "extract structured revenue insight for Q2."
        )
        result2 = await adapter.run(task2_description)
        print(f'Agent: {adapter.sdk_agent.name}')
        print(f'Result: {result2.action_result.summary}')
        print(f'Artifacts: {result2.action_result.artifacts}')

    else:
        print('\n⚠️  OpenAI SDK not available — skipping Part 2')
        print('Install via: pip install openai-agents>=0.5.0')

    # 3. Custom BaseAgent for optimization
    print('\n🎯 Part 3: Custom BaseAgent (Optimization)')
    print('-' * 70)
    optimizer_agent = OptimizerAgent(
        name='OptimizerAgent',
        description='Identifies leverage points for revenue optimization',
        ontology_loader=ontology_loader,
    )
    task3 = AgentTask(description='Optimize revenue based on forecast trends', parameters={})
    result3 = optimizer_agent.run(task3)
    print(f'Agent: {optimizer_agent.name}')
    print(f'Result: {result3.action_result.summary}')
    print(f'Artifacts: {result3.action_result.artifacts}')

    # 4. Summary
    print('\n' + '=' * 70)
    print('✅ Hybrid Orchestration Complete!')
    print('=' * 70)
    print('\nKey Takeaways:')
    print('  - Custom agents: Ontology routing, complex reasoning')
    print('  - SDK agents: Structured outputs, deterministic pipelines')
    print('  - Adapters: Bridge ontology context into SDK agents')
    print('  - Flexibility: Use each for its strengths')
    print('\nNext steps:')
    print('  - Add LangChain adapter for RAG + vector stores')
    print('  - Implement multi-SDK orchestrator')
    print('  - Benchmark custom vs. SDK performance')
    print('=' * 70)


if __name__ == '__main__':
    asyncio.run(main())

