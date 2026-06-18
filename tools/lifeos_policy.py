#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class PolicyRule:
    kind: str
    default_handling: str
    approval_required: bool
    examples: tuple[str, ...]


POLICY_RULES: tuple[PolicyRule, ...] = (
    PolicyRule("read", "auto", False, ("search_email", "list_calendar", "search_archive", "read_issue")),
    PolicyRule("draft/create preview", "stage", True, ("draft_email", "propose_event", "draft_reply", "create_preview")),
    PolicyRule("send/post/delete/payment", "approval required", True, ("send_email", "post_social", "delete_file", "create_payment")),
)

HIGH_RISK_ACTIONS = {"send", "post", "delete", "payment", "pay", "purchase", "transfer"}
DRAFT_ACTIONS = {"draft", "create", "reply", "propose", "schedule"}


def classify_action(action: str) -> PolicyRule:
    normalized = action.lower().replace("-", "_")
    parts = set(normalized.split("_"))
    if parts & HIGH_RISK_ACTIONS:
        return POLICY_RULES[2]
    if parts & DRAFT_ACTIONS:
        return POLICY_RULES[1]
    return POLICY_RULES[0]


def policy_summary() -> list[dict[str, object]]:
    return [asdict(rule) for rule in POLICY_RULES]
