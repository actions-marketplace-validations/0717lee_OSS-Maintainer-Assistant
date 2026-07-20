from maintainer_agent.core.approval import ApprovalGate, ApprovalMode
from maintainer_agent.core.models import Action, ActionStatus, ActionType, Item, ItemKind


def _item():
    return Item(number=1, kind=ItemKind.ISSUE, title="t")


def _action():
    return Action(id="a1", type=ActionType.COMMENT, payload={"body": "hi"})


def test_dry_run_keeps_proposed():
    gate = ApprovalGate(mode=ApprovalMode.DRY_RUN)
    assert gate.process(_action(), _item()).status == ActionStatus.PROPOSED


def test_apply_approved_calls_writer():
    calls = []
    gate = ApprovalGate(
        mode=ApprovalMode.APPLY,
        approver=lambda a, i: True,
        writer=lambda a, i: calls.append(a.id),
    )
    a = gate.process(_action(), _item())
    assert a.status == ActionStatus.APPLIED
    assert calls == ["a1"]


def test_apply_rejected_skips_writer():
    calls = []
    gate = ApprovalGate(
        mode=ApprovalMode.APPLY,
        approver=lambda a, i: False,
        writer=lambda a, i: calls.append(a.id),
    )
    a = gate.process(_action(), _item())
    assert a.status == ActionStatus.REJECTED
    assert calls == []


def test_apply_writer_failure_is_not_marked_applied():
    def boom(a, i):
        raise RuntimeError("nope")

    gate = ApprovalGate(mode=ApprovalMode.APPLY, approver=lambda a, i: True, writer=boom)
    a = gate.process(_action(), _item())
    assert a.status == ActionStatus.APPROVED  # approved but not applied
