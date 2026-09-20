"""Deterministic model-tier routing for NENUX Core."""

from dataclasses import dataclass

from config import FAST_MODEL, CHAT_MODEL, HEAVY_MODEL


@dataclass(frozen=True)
class ModelDecision:
    tier: str
    model: str
    reason: str


HEAVY_HINTS = (
    "debug",
    "diagnose",
    "investigate",
    "root cause",
    "refactor",
    "architect",
    "architecture",
    "design system",
    "security audit",
    "threat model",
    "analyze deeply",
    "deep analysis",
    "complex",
    "multi-step",
    "compare approaches",
    "repair",
    "fix this code",
    "review this code",
)

FAST_HINTS = (
    "pause",
    "resume",
    "mute",
    "unmute",
    "volume",
    "next tab",
    "previous tab",
    "close tab",
    "close all tabs",
    "open chrome",
    "open gmail",
    "open vscode",
    "focus chrome",
)


def select_model(
    user_input: str,
    *,
    route: str | None = None,
    desktop_intent: str | None = None,
) -> ModelDecision:
    """Choose a model tier using cheap, explainable runtime rules."""
    text = str(user_input).strip().lower()

    if desktop_intent:
        return ModelDecision(
            tier="FAST",
            model=FAST_MODEL,
            reason="resolved desktop-control intent",
        )

    if any(hint in text for hint in FAST_HINTS):
        return ModelDecision(
            tier="FAST",
            model=FAST_MODEL,
            reason="short desktop/media control request",
        )

    if route == "conversation" and len(text) <= 120:
        return ModelDecision(
            tier="FAST",
            model=FAST_MODEL,
            reason="short conversational request",
        )

    heavy_hits = sum(hint in text for hint in HEAVY_HINTS)

    if heavy_hits >= 1 or len(text) >= 700:
        return ModelDecision(
            tier="HEAVY",
            model=HEAVY_MODEL,
            reason=(
                "complex reasoning/debugging request"
                if heavy_hits
                else "long high-context request"
            ),
        )

    return ModelDecision(
        tier="MAIN",
        model=CHAT_MODEL,
        reason="general reasoning and tool-use request",
    )


def format_model_decision(decision: ModelDecision) -> str:
    return (
        f"[MODEL ROUTER] Tier: {decision.tier} | "
        f"Model: {decision.model} | Reason: {decision.reason}"
    )
