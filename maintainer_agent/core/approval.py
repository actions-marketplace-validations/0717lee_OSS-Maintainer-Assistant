"""Human-in-the-loop approval gate.

Nothing the agents propose ever reaches GitHub without passing through here.

* In ``DRY_RUN`` mode (the default) actions stay ``PROPOSED`` and are only logged.
* In ``APPLY`` mode each action is shown to an ``approver`` callback; only
  approved actions are handed to the ``writer`` that performs the side effect.

Both paths are fully audited.
"""
from __future__ import annotations

from enum import Enum
from typing import Callable, Optional

from .audit import AuditLog
from .models import Action, ActionStatus, Item

# Return True to approve the action.
Approver = Callable[[Action, Item], bool]
# Performs the real side effect (e.g. post a comment). Raises on failure.
Writer = Callable[[Action, Item], None]


class ApprovalMode(str, Enum):
    DRY_RUN = "dry_run"
    APPLY = "apply"


def auto_reject(action: Action, item: Item) -> bool:
    """Default approver used when none is supplied: approve nothing."""
    return False


class ApprovalGate:
    def __init__(
        self,
        mode: ApprovalMode = ApprovalMode.DRY_RUN,
        approver: Optional[Approver] = None,
        writer: Optional[Writer] = None,
        audit: Optional[AuditLog] = None,
    ):
        self.mode = mode
        self.approver = approver or auto_reject
        self.writer = writer
        self.audit = audit

    def _log(self, event: str, action: Action, item: Item, **extra) -> None:
        if self.audit is None:
            return
        self.audit.record(
            event,
            item=item.number,
            action_id=action.id,
            action_type=action.type.value,
            reason=action.reason,
            **extra,
        )

    def process(self, action: Action, item: Item) -> Action:
        """Run a single action through the gate, mutating and returning it."""
        if self.mode is ApprovalMode.DRY_RUN:
            action.status = ActionStatus.PROPOSED
            self._log("action_proposed", action, item, mode="dry_run")
            return action

        approved = bool(self.approver(action, item))
        if not approved:
            action.status = ActionStatus.REJECTED
            self._log("action_rejected", action, item, mode="apply")
            return action

        if self.writer is None:
            # Approved but no side-effect channel wired: record intent only.
            action.status = ActionStatus.APPROVED
            self._log("action_approved_no_writer", action, item, mode="apply")
            return action

        try:
            self.writer(action, item)
            action.status = ActionStatus.APPLIED
            self._log("action_applied", action, item, mode="apply")
        except Exception as exc:  # keep the run alive; surface the failure
            action.status = ActionStatus.APPROVED
            self._log("action_apply_failed", action, item, mode="apply", error=str(exc))
        return action

    def process_all(self, actions: list[Action], item: Item) -> list[Action]:
        return [self.process(a, item) for a in actions]
