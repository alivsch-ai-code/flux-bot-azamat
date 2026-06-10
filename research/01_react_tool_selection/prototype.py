"""ReAct tool selection — Phase 1 of the agentic roadmap.

The user states an intent in natural language; the agent reasons about which
model from the registry fits, asks for clarification when the intent is
ambiguous, and "calls" the chosen model. The loop follows ReAct
(Yao et al., 2022, arXiv:2210.03629): Thought -> Action -> Observation,
repeated until a final action is reached.

Run it:
    python research/01_react_tool_selection/prototype.py

No API keys needed: a deterministic MockLLM drives the loop so the agent
mechanics are reproducible. Swap in a real model by implementing BaseLLM.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# Tool registry — mirrors the production `ai_models` table (key, type, cost)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ModelTool:
    key: str
    model_type: str          # image | video | audio | text
    description: str
    cost_credits: int

    def as_prompt_line(self) -> str:
        return f"- {self.key} [{self.model_type}, {self.cost_credits} credits]: {self.description}"


REGISTRY: list[ModelTool] = [
    ModelTool("flux-pro", "image", "photorealistic text-to-image, best quality", 12),
    ModelTool("flux-schnell", "image", "fast text-to-image drafts", 4),
    ModelTool("sdxl-inpaint", "image", "edit/replace regions of an existing image", 8),
    ModelTool("kling-v2", "video", "text-to-video and image-to-video, 5-10s clips", 45),
    ModelTool("musicgen", "audio", "short music clips from a text description", 15),
    ModelTool("gemini-chat", "text", "conversational answers, no media output", 1),
]


# --------------------------------------------------------------------------
# LLM interface — MockLLM is deterministic; RealLLM would call UnifiedAIClient
# --------------------------------------------------------------------------

class BaseLLM:
    """One method: complete(prompt) -> str. Implement with any backend."""

    def complete(self, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class MockLLM(BaseLLM):
    """Deterministic stand-in so the ReAct loop is testable without tokens.

    It inspects the *user request* embedded in the prompt and emits the same
    Thought/Action JSON a tuned model would. Intent rules are intentionally
    simple — the point of the prototype is the loop, not the classifier.
    """

    INTENT_RULES: list[tuple[str, str]] = [
        (r"\b(video|clip|animate|animation)\b", "video"),
        (r"\b(music|song|jingle|melody|soundtrack)\b", "audio"),
        (r"\b(edit|inpaint|replace|remove .* from)\b", "image-edit"),
        (r"\b(draft|quick|fast|sketch)\b", "image-fast"),
        (r"\b(image|picture|photo|logo|poster|art)\b", "image"),
    ]

    def complete(self, prompt: str) -> str:
        request = prompt.rsplit("USER REQUEST:", 1)[-1].strip().lower()

        intent = next(
            (label for pattern, label in self.INTENT_RULES if re.search(pattern, request)),
            None,
        )
        if intent is None:
            return json.dumps({
                "thought": "The request names no medium I can map to a model type.",
                "action": "clarify",
                "input": "Should the result be an image, a video, music, or a text answer?",
            })

        choice = {
            "video": "kling-v2",
            "audio": "musicgen",
            "image-edit": "sdxl-inpaint",
            "image-fast": "flux-schnell",
            "image": "flux-pro",
        }[intent]
        return json.dumps({
            "thought": f"Intent maps to {intent}; best registry match is {choice}.",
            "action": "select_model",
            "input": choice,
        })


# --------------------------------------------------------------------------
# The ReAct loop
# --------------------------------------------------------------------------

@dataclass
class AgentResult:
    selected_model: str | None
    clarification: str | None
    trace: list[str] = field(default_factory=list)


class ToolSelectionAgent:
    """Thought -> Action -> Observation until select_model or clarify."""

    MAX_STEPS = 4

    def __init__(self, llm: BaseLLM, registry: list[ModelTool]):
        self.llm = llm
        self.registry = {tool.key: tool for tool in registry}

    def _build_prompt(self, request: str, observations: list[str]) -> str:
        tool_lines = "\n".join(t.as_prompt_line() for t in self.registry.values())
        history = "\n".join(observations) or "(none yet)"
        return (
            "You select exactly one model for a generation request.\n"
            f"AVAILABLE MODELS:\n{tool_lines}\n"
            f"OBSERVATIONS SO FAR:\n{history}\n"
            'Reply as JSON: {"thought": ..., "action": "select_model"|"clarify", "input": ...}\n'
            f"USER REQUEST: {request}"
        )

    def run(self, request: str) -> AgentResult:
        result = AgentResult(selected_model=None, clarification=None)
        observations: list[str] = []

        for step in range(1, self.MAX_STEPS + 1):
            raw = self.llm.complete(self._build_prompt(request, observations))
            decision = json.loads(raw)
            result.trace.append(f"step {step} | thought: {decision['thought']}")
            result.trace.append(f"step {step} | action:  {decision['action']}({decision['input']})")

            if decision["action"] == "clarify":
                result.clarification = decision["input"]
                return result

            if decision["action"] == "select_model":
                key = decision["input"]
                tool = self.registry.get(key)
                if tool is None:
                    observations.append(f"Observation: '{key}' is not in the registry.")
                    continue
                result.selected_model = tool.key
                result.trace.append(
                    f"step {step} | observe: {tool.key} ready ({tool.cost_credits} credits)"
                )
                return result

        result.clarification = "I could not settle on a model — can you rephrase?"
        return result


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------

def main() -> None:
    agent = ToolSelectionAgent(MockLLM(), REGISTRY)
    demos = [
        "a cinematic photo of a lighthouse in a storm",
        "animate my logo into a short clip",
        "a quick draft sketch of a robot mascot",
        "remove the car from this photo",
        "a jingle for my coffee shop ad",
        "help me with my project",          # ambiguous -> clarify
    ]
    for request in demos:
        print(f"\n>>> {request}")
        outcome = agent.run(request)
        for line in outcome.trace:
            print(f"    {line}")
        if outcome.selected_model:
            print(f"    => selected: {outcome.selected_model}")
        else:
            print(f"    => needs clarification: {outcome.clarification}")


if __name__ == "__main__":
    main()
