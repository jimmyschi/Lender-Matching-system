"""
Tests for the core matching engine logic in app/services/matching.py.

Run from the backend/ directory:
    python -m pytest tests/ -v
"""
from types import SimpleNamespace

from app.services.matching import evaluate_criterion, get_applicable_programs


def _criterion(**kwargs):
    defaults = {
        "label": "Test Criterion",
        "field_name": "guarantor_fico",
        "criterion_type": "min_value",
        "threshold_value": 700,
        "allowed_values": None,
        "null_means_pass": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_min_value_passes_when_at_or_above_threshold():
    c = _criterion(field_name="guarantor_fico", criterion_type="min_value", threshold_value=700)
    assert evaluate_criterion(c, {"guarantor_fico": 715})["passed"] is True
    assert evaluate_criterion(c, {"guarantor_fico": 700})["passed"] is True


def test_min_value_fails_when_below_threshold():
    c = _criterion(field_name="guarantor_fico", criterion_type="min_value", threshold_value=700)
    result = evaluate_criterion(c, {"guarantor_fico": 680})
    assert result["passed"] is False
    assert "680" in result["explanation"]


def test_null_means_pass_for_bankruptcy_field():
    c = _criterion(
        label="No Bankruptcy in Last 7 Years",
        field_name="years_since_bankruptcy",
        criterion_type="min_value",
        threshold_value=7,
        null_means_pass=True,
    )
    assert evaluate_criterion(c, {"years_since_bankruptcy": None})["passed"] is True
    assert evaluate_criterion(c, {"years_since_bankruptcy": 3})["passed"] is False
    assert evaluate_criterion(c, {"years_since_bankruptcy": 8})["passed"] is True


def _program(**kwargs):
    return SimpleNamespace(**kwargs)


def test_applicable_programs_filters_by_paynet():
    programs = [
        _program(applicability_type="with_paynet", priority=1),
        _program(applicability_type="without_paynet", priority=2),
        _program(applicability_type="general", priority=3),
    ]
    with_paynet = get_applicable_programs(programs, {"paynet_score": 680})
    without_paynet = get_applicable_programs(programs, {"paynet_score": None})

    types_with = {p.applicability_type for p in with_paynet}
    types_without = {p.applicability_type for p in without_paynet}

    assert "with_paynet" in types_with
    assert "general" in types_with
    assert "without_paynet" not in types_with

    assert "without_paynet" in types_without
    assert "general" in types_without
    assert "with_paynet" not in types_without
