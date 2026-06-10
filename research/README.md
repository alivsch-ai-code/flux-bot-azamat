# Research — Agentic AZAMAT Prototypes

Runnable prototypes for each phase of the [research roadmap](../README.md#research-roadmap--toward-an-agentic-azamat).
Every prototype is **standalone** (no API keys, no database) and runs in seconds:

```bash
python research/01_react_tool_selection/prototype.py
python research/02_pipeline_planner/prototype.py
python research/03_hierarchical_memory/prototype.py
```

Each one ships with a deterministic mock LLM so the agent loop itself can be studied,
tested and iterated on without spending tokens. Swapping the mock for a real model is a
one-class change (see `BaseLLM` in each prototype).

| Prototype | Roadmap phase | Research basis | Integration point in `src/` |
|-----------|--------------|----------------|------------------------------|
| [`01_react_tool_selection`](01_react_tool_selection/) | 1 — Autonomous tool selection | [ReAct (Yao et al., 2022)](https://arxiv.org/abs/2210.03629), [Toolformer (Schick et al., 2023)](https://arxiv.org/abs/2302.04761) | Replaces menu navigation in `presentation/telegram/handlers/gen/` — the agent picks the model from the `ai_models` registry |
| [`02_pipeline_planner`](02_pipeline_planner/) | 2 — Multi-step planning + 6 — Guardrails | [Plan-and-Solve (Wang et al., 2023)](https://arxiv.org/abs/2305.04091), [Tree of Thoughts (Yao et al., 2023)](https://arxiv.org/abs/2305.10601) | Sits in front of `GenerationService.process_request` — decomposes a goal into chained generation steps with a credit budget |
| [`03_hierarchical_memory`](03_hierarchical_memory/) | 3 — Long-term memory | [MemGPT (Packer et al., 2023)](https://arxiv.org/abs/2310.08560), [Generative Agents (Park et al., 2023)](https://arxiv.org/abs/2304.03442) | Extends `chat_sessions` (in `infrastructure/database.py`) with core / recall / archival tiers |

## Design constraints shared by all prototypes

1. **Budget-aware by construction.** Every autonomous action carries a credit cost; the agent
   must stop and ask when a plan exceeds the user's budget. Autonomy never surprises the wallet.
2. **Deterministic test mode.** The mock LLM makes agent behavior reproducible — the loop, not
   the model, is what's being engineered here.
3. **Registry-driven.** Tools are not hardcoded: they're derived from model metadata, exactly like
   the production `ai_models` table with its JSONB `input_schema`. New Replicate models become
   new tools without code changes.

## From prototype to production

The path for each prototype is the same: extract the agent loop into
`src/application/agent/`, feed it the live `ai_models` registry instead of the sample data,
and wire the LLM calls through the existing `UnifiedAIClient`. The Telegram layer only needs
one new entry point: free-text messages route to the agent instead of the menu tree.
