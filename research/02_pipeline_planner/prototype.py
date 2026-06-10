"""Pipeline planner — Phases 2 + 6 of the agentic roadmap.

One natural-language goal ("make a logo, animate it, add a jingle") becomes an
executed multi-step plan: the planner decomposes the goal into chained
generation steps (Plan-and-Solve, Wang et al., 2023, arXiv:2305.04091),
passes intermediate outputs between steps, and enforces a hard credit budget
before anything runs — autonomy never surprises the user's wallet.

Run it:
    python research/02_pipeline_planner/prototype.py
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

CREDIT_COSTS = {"image": 12, "video": 45, "audio": 15}


# --------------------------------------------------------------------------
# Plan structure
# --------------------------------------------------------------------------

@dataclass
class Step:
    index: int
    kind: str                  # image | video | audio
    prompt: str
    needs_output_of: int | None = None   # chaining: e.g. video animates step 1's image

    @property
    def cost(self) -> int:
        return CREDIT_COSTS[self.kind]


@dataclass
class Plan:
    goal: str
    steps: list[Step] = field(default_factory=list)

    @property
    def total_cost(self) -> int:
        return sum(s.cost for s in self.steps)


# --------------------------------------------------------------------------
# Planner — decomposes a goal into ordered, chained steps.
# Deterministic keyword rules stand in for an LLM planning call; production
# would route this through UnifiedAIClient with the same output contract.
# --------------------------------------------------------------------------

class Planner:
    def decompose(self, goal: str) -> Plan:
        plan = Plan(goal=goal)
        lower = goal.lower()
        index = 0
        image_step: int | None = None

        if re.search(r"\b(logo|image|poster|picture|photo|art)\b", lower):
            index += 1
            image_step = index
            plan.steps.append(Step(index, "image", f"high-quality visual for: {goal}"))

        if re.search(r"\b(animate|animation|video|clip)\b", lower):
            index += 1
            plan.steps.append(Step(
                index, "video",
                "animate the generated visual" if image_step else f"video for: {goal}",
                needs_output_of=image_step,
            ))

        if re.search(r"\b(jingle|music|song|soundtrack|audio)\b", lower):
            index += 1
            plan.steps.append(Step(index, "audio", f"short jingle matching: {goal}"))

        return plan


# --------------------------------------------------------------------------
# Executor with budget guardrail
# --------------------------------------------------------------------------

@dataclass
class ExecutionReport:
    approved: bool
    reason: str
    artifacts: dict[int, str] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)


class BudgetedExecutor:
    """Refuses to run any plan that exceeds the user's credit budget.

    The guardrail runs BEFORE the first step — a half-executed pipeline that
    dies at step 3 of 3 would still have charged the user for steps 1 and 2.
    """

    def __init__(self, user_credits: int, confirm_above: int = 60):
        self.user_credits = user_credits
        self.confirm_above = confirm_above

    def execute(self, plan: Plan) -> ExecutionReport:
        if not plan.steps:
            return ExecutionReport(False, "Could not decompose the goal into steps.")

        if plan.total_cost > self.user_credits:
            return ExecutionReport(
                False,
                f"Plan costs {plan.total_cost} credits but only "
                f"{self.user_credits} are available. Nothing was charged.",
            )

        report = ExecutionReport(True, "within budget")
        if plan.total_cost > self.confirm_above:
            report.log.append(
                f"[guardrail] cost {plan.total_cost} > {self.confirm_above}: "
                "production flow would require an explicit user confirmation here"
            )

        for step in plan.steps:
            source = (
                f" (input: artifact #{step.needs_output_of})"
                if step.needs_output_of else ""
            )
            artifact = f"<{step.kind}-output-{step.index}>"
            report.artifacts[step.index] = artifact
            report.log.append(
                f"step {step.index}: {step.kind:<5} -{step.cost:>3} credits{source} -> {artifact}"
            )
        report.log.append(f"total charged: {plan.total_cost} credits")
        return report


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------

def main() -> None:
    planner = Planner()
    goals = [
        ("make a logo for my cafe, animate it, and add a jingle", 100),
        ("make a logo for my cafe, animate it, and add a jingle", 40),   # over budget
        ("a poster for our summer festival", 100),
    ]
    for goal, credits in goals:
        plan = planner.decompose(goal)
        print(f"\n>>> goal: {goal}  (budget: {credits} credits)")
        for step in plan.steps:
            chain = f" <- step {step.needs_output_of}" if step.needs_output_of else ""
            print(f"    plan  step {step.index}: {step.kind:<5} {step.cost:>3} credits{chain}")
        result = BudgetedExecutor(user_credits=credits).execute(plan)
        if not result.approved:
            print(f"    BLOCKED: {result.reason}")
            continue
        for line in result.log:
            print(f"    exec  {line}")


if __name__ == "__main__":
    main()
