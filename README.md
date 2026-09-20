

---

## Multi-model runtime

NENUX Core can route work across independent local model tiers while keeping
tool execution and permissions in the runtime:

- **FAST** — lightweight routing, semantic desktop intent and short interactions.
- **MAIN** — normal reasoning, retrieval and tool-use tasks.
- **HEAVY** — complex debugging, architecture and high-context reasoning.
- **PLANNER** and **EVALUATOR** remain independently configurable.

All tiers inherit the current main model by default, so the feature is
backward-compatible and does not require extra model downloads.

Environment overrides:

```text
NENUX_FAST_MODEL=<ollama-model>
NENUX_MODEL=<ollama-model>
NENUX_HEAVY_MODEL=<ollama-model>
NENUX_PLANNER_MODEL=<ollama-model>
NENUX_EVALUATOR_MODEL=<ollama-model>
NENUX_EMBED_MODEL=<ollama-model>
```

At runtime, model selection is visible in the console:

```text
[MODEL ROUTER] Tier: HEAVY | Model: <model> | Reason: complex reasoning/debugging request
```

The selector is intentionally deterministic and explainable. Dedicated
desktop actions still execute through whitelisted tools rather than asking a
larger model to perform the action itself.
