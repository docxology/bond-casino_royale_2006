"""Tests for network-level financial-crime analytics (laundering_network.py)."""

from __future__ import annotations

import pytest

from casino_royale_2006 import laundering_network as ln
from casino_royale_2006.laundering_detect import ChipTransaction, synthetic_flow


def _figures():
    return (
        ChipTransaction("cage", "a", 10000.0, 0, "cash_in"),
        ChipTransaction("a", "hub", 4000.0, 1, "transfer"),
        ChipTransaction("b", "hub", 4000.0, 2, "transfer"),
        ChipTransaction("hub", "cage", 9000.0, 3, "cash_out"),
    )


def test_concentration_hhi_single_counterparty_is_one():
    txns = _figures()
    assert ln.concentration_hhi(txns, "a") == pytest.approx(1.0)  # only flows to hub
    # hub has two player counterparties (a and b), 4000 each -> 2*(0.5)^2
    assert ln.concentration_hhi(txns, "hub") == pytest.approx(0.5)
    assert ln.concentration_hhi(txns, "missing") == 0.0


def test_concentration_hhi_balanced_split():
    txns = (
        ChipTransaction("cage", "p", 10000.0, 0, "cash_in"),
        ChipTransaction("p", "x", 1000.0, 1, "transfer"),
        ChipTransaction("p", "y", 1000.0, 2, "transfer"),
        ChipTransaction("p", "z", 1000.0, 3, "transfer"),
        ChipTransaction("p", "cage", 2000.0, 4, "cash_out"),
    )
    # Three equal player-to-player outflows -> HHI = 3*(1/3)^2 = 1/3.
    assert ln.concentration_hhi(txns, "p") == pytest.approx(1.0 / 3.0)


def test_page_rank_deterministic_and_normalised():
    txns = synthetic_flow(17, num_players=8)
    pr1 = ln.page_rank(txns)
    pr2 = ln.page_rank(txns)
    assert pr1 == pr2
    assert sum(pr1.values()) == pytest.approx(1.0)


def test_page_rank_collection_account_ranks_high():
    txns = _figures()
    pr = ln.page_rank(txns)
    # hub receives from both a and b (no outgoing to players), so it is the
    # collection node and should out-rank the pure senders.
    assert pr["hub"] > pr["a"]
    assert pr["hub"] > pr["b"]


def test_label_propagation_deterministic_partition():
    txns = synthetic_flow(3, num_players=6)
    c1, labels1 = ln.label_propagation(txns)
    c2, labels2 = ln.label_propagation(txns)
    assert (c1, labels1) == (c2, labels2)
    # Communities partition the player set exactly once, with consistent labels.
    flat = [p for com in c1 for p in com]
    assert len(flat) == len(set(flat))
    for community in c1:
        lbl = labels1[community[0]]
        assert all(labels1[p] == lbl for p in community)
    assert len(c1) >= 1


def test_label_propagation_empty():
    assert ln.label_propagation(()) == ((), {})


def test_conservation_imbalance():
    balanced = (
        ChipTransaction("cage", "w", 5000.0, 0, "cash_in"),
        ChipTransaction("w", "cage", 4000.0, 1, "cash_out"),
        ChipTransaction("w", "u", 1000.0, 2, "transfer"),
    )
    assert ln.conservation_imbalance(balanced, "w") == pytest.approx(0.0)
    assert ln.conservation_imbalance(balanced, "absent") == 1.0  # no cash in


def test_turnover_includes_both_directions():
    txns = _figures()
    # hub: in 4000 (a) + 4000 (b) + out 9000 (to cage) = 17000
    assert ln.turnover(txns, "hub") == pytest.approx(17000.0)


def test_network_risk_report_flags_launderer():
    flow = synthetic_flow(17, num_players=8)
    report = ln.network_risk_report(flow)
    assert "LeChiffre" in report.flagged
    assert report.risk["LeChiffre"] >= ln.RISK_THRESHOLD
    # Le Chiffre is the single top-risk account (value-neutral churn).
    assert report.flagged[0] == "LeChiffre"


def test_network_risk_report_as_dict():
    flow = synthetic_flow(17, num_players=8)
    d = ln.network_risk_report(flow).as_dict()
    assert set(d) >= {"num_players", "num_communities", "top_risk_player", "flagged"}
    assert d["any_flagged"] is True
    assert d["top_risk_player"] == "LeChiffre"


def test_as_dict_any_flagged_is_not_a_named_verdict():
    """``any_flagged`` must mean "somebody", never "the film's launderer".

    Negative control: a flow whose only flagged account is *not* LeChiffre must
    still report ``any_flagged`` True, while a caller asking about LeChiffre by
    name gets False. If this module ever hard-codes the film's suspect again,
    one of these two assertions fails.
    """
    # A lone value-neutral churner named "ghost": chips in == chips out.
    txns = (
        ChipTransaction("cage", "ghost", 10000.0, 0, "cash_in"),
        ChipTransaction("ghost", "cage", 10000.0, 1, "cash_out"),
    )
    report = ln.network_risk_report(txns)
    assert report.flagged == ("ghost",)
    assert "LeChiffre" not in report.flagged
    assert report.as_dict()["any_flagged"] is True
    assert "launderer_flagged" not in report.as_dict()


def test_as_dict_reports_nothing_flagged_when_nobody_qualifies():
    """The composite gate must be capable of flagging no one at all."""
    # A pure loser: cash in 10000, cash out 1000 -> imbalance 0.9 >> tolerance.
    txns = (
        ChipTransaction("cage", "mark", 10000.0, 0, "cash_in"),
        ChipTransaction("mark", "cage", 1000.0, 1, "cash_out"),
    )
    report = ln.network_risk_report(txns)
    assert report.flagged == ()
    d = report.as_dict()
    assert d["any_flagged"] is False
    assert d["top_risk_player"] == ""
    assert d["top_risk_score"] == 0.0
