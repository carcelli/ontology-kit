import asyncio

from .manager import main as run_manager


async def main() -> None:
    # Default to sample data
    csv_path = 'examples/ontology_ml/data/sample_invoices.csv'
    print(f'Running ontology-ML pipeline with: {csv_path}')
    await run_manager(csv_path)


if __name__ == '__main__':
    asyncio.run(main())

