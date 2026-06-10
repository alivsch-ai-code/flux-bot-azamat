"""Hierarchical memory — Phase 3 of the agentic roadmap.

Extends the production idea behind `chat_sessions` (full history + periodic
summarization) into three tiers, following MemGPT (Packer et al., 2023,
arXiv:2310.08560):

  core     - small, always-in-context user profile (style, language, budget)
  recall   - recent raw exchanges, searchable, evicted to archival when full
  archival - compressed summaries of evicted history

The payoff: prompt enrichment. "another one like last time" works because the
agent retrieves what "last time" was — without carrying the entire history in
every request.

Run it:
    python research/03_hierarchical_memory/prototype.py
"""
from __future__ import annotations

from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# Memory tiers
# --------------------------------------------------------------------------

@dataclass
class CoreMemory:
    """Always in context. Mirrors what a `user_profile` table would hold."""
    language: str = "de"
    preferred_style: str | None = None
    last_model: str | None = None


@dataclass
class Exchange:
    user: str
    agent: str

    def keywords(self) -> set[str]:
        return {w for w in f"{self.user} {self.agent}".lower().split() if len(w) > 3}


class RecallMemory:
    """Bounded window of raw exchanges; oldest spill to archival on overflow."""

    def __init__(self, capacity: int = 4):
        self.capacity = capacity
        self.items: list[Exchange] = []

    def add(self, exchange: Exchange) -> Exchange | None:
        """Store an exchange; return the evicted one if the window overflowed."""
        self.items.append(exchange)
        if len(self.items) > self.capacity:
            return self.items.pop(0)
        return None

    def search(self, query: str) -> list[Exchange]:
        terms = {w for w in query.lower().split() if len(w) > 3}
        return [e for e in self.items if terms & e.keywords()]


class ArchivalMemory:
    """Compressed long-term store. Production: summaries table + embeddings."""

    def __init__(self):
        self.summaries: list[str] = []

    def archive(self, exchange: Exchange) -> None:
        self.summaries.append(
            f"user asked for '{exchange.user[:48]}' -> agent: '{exchange.agent[:48]}'"
        )

    def search(self, query: str) -> list[str]:
        terms = {w for w in query.lower().split() if len(w) > 3}
        return [s for s in self.summaries if terms & set(s.lower().split())]


# --------------------------------------------------------------------------
# The memory-augmented agent
# --------------------------------------------------------------------------

@dataclass
class MemoryAgent:
    core: CoreMemory = field(default_factory=CoreMemory)
    recall: RecallMemory = field(default_factory=RecallMemory)
    archival: ArchivalMemory = field(default_factory=ArchivalMemory)

    def observe(self, user_msg: str, agent_msg: str) -> None:
        """Record an exchange and maintain core/archival tiers."""
        if "watercolor" in user_msg.lower():
            self.core.preferred_style = "watercolor"
        evicted = self.recall.add(Exchange(user_msg, agent_msg))
        if evicted:
            self.archival.archive(evicted)

    def enrich_prompt(self, prompt: str) -> tuple[str, list[str]]:
        """Build the model-ready prompt from all three tiers."""
        notes: list[str] = []
        enriched = prompt

        if self.core.preferred_style and "style" not in prompt.lower():
            enriched += f", in {self.core.preferred_style} style"
            notes.append(f"core: applied preferred style '{self.core.preferred_style}'")

        for hit in self.recall.search(prompt):
            notes.append(f"recall: related exchange found -> '{hit.user[:40]}'")
        for hit in self.archival.search(prompt):
            notes.append(f"archival: {hit}")

        return enriched, notes


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------

def main() -> None:
    agent = MemoryAgent()

    history = [
        ("a watercolor painting of a lighthouse", "generated with flux-pro"),
        ("a lighthouse at night, same style", "generated with flux-pro"),
        ("a poster for my coffee shop", "generated with flux-pro"),
        ("animate the coffee shop poster", "rendered with kling-v2"),
        ("a quick robot sketch", "generated with flux-schnell"),
        ("a melody for a podcast intro", "generated with musicgen"),
    ]
    for user_msg, agent_msg in history:
        agent.observe(user_msg, agent_msg)

    print(f"core memory: style={agent.core.preferred_style!r}, "
          f"recall={len(agent.recall.items)} items, "
          f"archival={len(agent.archival.summaries)} summaries")

    for prompt in ["a sailboat in a storm", "another lighthouse please"]:
        enriched, notes = agent.enrich_prompt(prompt)
        print(f"\n>>> {prompt}")
        print(f"    enriched: {enriched}")
        for note in notes:
            print(f"    {note}")


if __name__ == "__main__":
    main()
