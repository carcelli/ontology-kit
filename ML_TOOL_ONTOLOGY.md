# ML Tool Ontology — Architecture Plan

**Date**: 2025-11-09 • **Status**: Draft

## Philosophy

- Agents call **Tools**, not algorithms.  
- Tools are annotated with what they **consume/produce**, what they **implement** (algorithms), and the **Python identifier** to execute.  
- Long-running work uses the **Asynchronous Job Pattern**: tool returns a `job_id`; a separate tool polls status.

## Core classes

- `ml:MLTool` ⟵ `core:Tool`
- `ml:ModelTrainerTool`, `ml:CrossValidatorTool`, `ml:JobStatusTool`
- `ml:Dataset`, `ml:Model`, `ml:TrainedModel`, `ml:PerformanceMetric`, `ml:Hyperparameters`

## Core properties

- `ml:consumes` (Tool → Dataset/Model)  
- `ml:produces` (Tool → TrainedModel/PerformanceMetric)  
- `ml:implementsAlgorithm` (Tool → string)  
- `ml:hasPythonIdentifier` (Tool → string)

## OpenAI SDK flow

1) Agent goal → SPARQL to find a tool by class/IO.  
2) Read `ml:hasPythonIdentifier` (e.g., `"train_model"`) → map to Python function + Pydantic schema.  
3) Execute → returns `job_id`.  
4) Poll with `check_job_status` until `COMPLETED` → artifact URI.

## Ops constraints

- No synchronous training in tool calls. Schedule work; return immediately.  
- Persist artifacts as URIs; update graph when jobs complete.

## Next

- Implement `assets/ontologies/ml_tools.ttl`  
- Implement `src/agent_kit/tools/ml_training.py`  
- Implement minimal ontology loader + orchestrator

