"""
Core underwriting and lender matching engine.

The matching process for each lender:
  1. Build a flat dict of application fields from the ORM object.
  2. Filter the lender's programs to those applicable for this application
     (based on applicability_type: whether PayNet is present, whether it's
     corp-only, trucking, medical, etc.).
  3. Sort applicable programs by priority ascending (priority 1 = best tier).
  4. Evaluate each program's criteria in order. Stop at the first program
     where all hard-reject criteria pass — that's the matched program.
  5. If no program passes, collect failure reasons from the best (lowest
     priority) program that was attempted.
  6. For eligible matches, compute a fit score (0-100) as a weighted average
     of per-criterion scores. Numeric criteria (min/max) earn partial credit
     based on margin above the threshold; boolean/list criteria are 0 or 100.

Extending the engine:
  - New criterion type: add an elif branch in evaluate_criterion().
  - New applicability type: add an elif branch in get_applicable_programs().
  - New lender: insert rows into the database—no code change required.
"""
from app.models import LoanApplication, Lender, LenderProgram, LenderCriterion

TRUCKING_INDUSTRIES = {"trucking"}
TRUCKING_EQUIPMENT = {
    "class_8_truck", "trailer", "dump_truck",
    "medium_duty_truck", "light_duty_truck", "vocational_truck",
}
MEDICAL_INDUSTRIES = {"medical_dental", "veterinary"}


def app_to_dict(application: LoanApplication) -> dict:
    is_trucking = (
        application.business_industry in TRUCKING_INDUSTRIES
        or application.equipment_type in TRUCKING_EQUIPMENT
    )
    is_medical = application.business_industry in MEDICAL_INDUSTRIES

    return {
        "guarantor_fico": application.guarantor_fico,
        "paynet_score": application.paynet_score,
        "years_in_business": application.years_in_business,
        "annual_revenue": application.annual_revenue,
        "loan_amount": application.loan_amount,
        "loan_term_months": application.loan_term_months,
        "business_state": application.business_state,
        "business_industry": application.business_industry,
        "equipment_type": application.equipment_type,
        "equipment_age_years": application.equipment_age_years,
        "has_bankruptcy": application.has_bankruptcy,
        "years_since_bankruptcy": application.years_since_bankruptcy,
        "has_judgments": application.has_judgments,
        "has_foreclosures": application.has_foreclosures,
        "has_repossessions": application.has_repossessions,
        "has_tax_liens": application.has_tax_liens,
        "is_startup": application.is_startup,
        "is_us_citizen": application.is_us_citizen,
        "is_homeowner": application.is_homeowner,
        "years_at_current_residence": application.years_at_current_residence,
        "has_cdl": application.has_cdl,
        "num_trucks_operating": application.num_trucks_operating,
        "is_corp_only": application.is_corp_only,
        "personal_revolving_debt": application.personal_revolving_debt,
        "revolving_plus_unsecured_debt": application.revolving_plus_unsecured_debt,
        "is_private_party_sale": application.is_private_party_sale,
        "is_trucking": is_trucking,
        "is_medical": is_medical,
    }


def get_applicable_programs(
    programs: list[LenderProgram], app_dict: dict
) -> list[LenderProgram]:
    applicable = []
    for program in programs:
        at = program.applicability_type
        if at == "general":
            applicable.append(program)
        elif at == "with_paynet" and app_dict.get("paynet_score") is not None:
            applicable.append(program)
        elif at == "without_paynet" and app_dict.get("paynet_score") is None:
            applicable.append(program)
        elif at == "corp_only" and app_dict.get("is_corp_only"):
            applicable.append(program)
        elif at == "medical" and app_dict.get("is_medical"):
            applicable.append(program)
        elif at == "trucking" and app_dict.get("is_trucking"):
            applicable.append(program)
    return sorted(applicable, key=lambda p: p.priority)


def _format_number(value) -> str:
    if value is None:
        return "Not provided"
    try:
        n = float(value)
        if n == int(n):
            return f"{int(n):,}"
        return f"{n:,.1f}"
    except (ValueError, TypeError):
        return str(value)


def evaluate_criterion(criterion: LenderCriterion, app_dict: dict) -> dict:
    field = criterion.field_name
    ctype = criterion.criterion_type
    actual = app_dict.get(field)
    threshold = criterion.threshold_value
    values = criterion.allowed_values or []

    if actual is None and criterion.null_means_pass:
        return {
            "passed": True,
            "actual_value": "Not applicable",
            "required_value": _format_requirement(criterion),
            "explanation": "Not applicable — field not provided, criterion waived",
        }

    if ctype == "min_value":
        if actual is None:
            return {
                "passed": False,
                "actual_value": "Not provided",
                "required_value": f">= {_format_number(threshold)}",
                "explanation": f"{criterion.label}: value not provided, minimum {_format_number(threshold)} required",
            }
        passed = actual >= threshold
        return {
            "passed": passed,
            "actual_value": _format_number(actual),
            "required_value": f">= {_format_number(threshold)}",
            "explanation": (
                f"{criterion.label}: {_format_number(actual)} meets the minimum of {_format_number(threshold)}"
                if passed else
                f"{criterion.label}: {_format_number(actual)} is below the minimum required {_format_number(threshold)}"
            ),
        }

    if ctype == "max_value":
        if actual is None:
            passed = criterion.null_means_pass
            return {
                "passed": passed,
                "actual_value": "Not provided",
                "required_value": f"<= {_format_number(threshold)}",
                "explanation": f"{criterion.label}: value not provided",
            }
        passed = actual <= threshold
        return {
            "passed": passed,
            "actual_value": _format_number(actual),
            "required_value": f"<= {_format_number(threshold)}",
            "explanation": (
                f"{criterion.label}: {_format_number(actual)} is within the limit of {_format_number(threshold)}"
                if passed else
                f"{criterion.label}: {_format_number(actual)} exceeds the maximum of {_format_number(threshold)}"
            ),
        }

    if ctype == "required_true":
        passed = bool(actual)
        label_val = "Yes" if actual else "No"
        return {
            "passed": passed,
            "actual_value": label_val,
            "required_value": "Yes",
            "explanation": (
                f"{criterion.label}: confirmed"
                if passed else
                f"{criterion.label}: required but not met"
            ),
        }

    if ctype == "required_false":
        passed = not bool(actual)
        label_val = "Yes" if actual else "No"
        return {
            "passed": passed,
            "actual_value": label_val,
            "required_value": "No",
            "explanation": (
                f"{criterion.label}: confirmed clear"
                if passed else
                f"{criterion.label}: disqualifying condition present"
            ),
        }

    if ctype == "excluded_values":
        if actual is None:
            return {
                "passed": True,
                "actual_value": "Not provided",
                "required_value": "Not in restricted list",
                "explanation": f"{criterion.label}: not applicable",
            }
        passed = actual not in values
        preview = ", ".join(values[:4]) + ("..." if len(values) > 4 else "")
        return {
            "passed": passed,
            "actual_value": str(actual),
            "required_value": f"Not in: {preview}",
            "explanation": (
                f"{criterion.label}: '{actual}' is not in the restricted list"
                if passed else
                f"{criterion.label}: '{actual}' is on the restricted list"
            ),
        }

    if ctype == "allowed_values":
        if actual is None:
            return {
                "passed": False,
                "actual_value": "Not provided",
                "required_value": "Must be in approved list",
                "explanation": f"{criterion.label}: value not provided",
            }
        passed = actual in values
        preview = ", ".join(values[:4]) + ("..." if len(values) > 4 else "")
        return {
            "passed": passed,
            "actual_value": str(actual),
            "required_value": f"One of: {preview}",
            "explanation": (
                f"{criterion.label}: '{actual}' is in the approved list"
                if passed else
                f"{criterion.label}: '{actual}' is not in the approved list"
            ),
        }

    return {
        "passed": False,
        "actual_value": str(actual),
        "required_value": "Unknown",
        "explanation": f"Unknown criterion type: {ctype}",
    }


def _format_requirement(criterion: LenderCriterion) -> str:
    if criterion.criterion_type in ("min_value",):
        return f">= {_format_number(criterion.threshold_value)}"
    if criterion.criterion_type in ("max_value",):
        return f"<= {_format_number(criterion.threshold_value)}"
    if criterion.criterion_type == "required_true":
        return "Yes"
    if criterion.criterion_type == "required_false":
        return "No"
    return "See description"


def _criterion_score(criterion: LenderCriterion, result: dict) -> float:
    if not result["passed"]:
        return 0.0

    ctype = criterion.criterion_type
    threshold = criterion.threshold_value

    if ctype == "min_value" and threshold:
        try:
            actual = float(result["actual_value"].replace(",", ""))
        except (ValueError, AttributeError):
            return 100.0
        comfort = threshold * 0.15
        margin = actual - threshold
        score = 50 + min(50, (margin / comfort) * 50) if comfort > 0 else 100
        return round(max(50.0, min(100.0, score)), 1)

    if ctype == "max_value" and threshold:
        try:
            actual = float(result["actual_value"].replace(",", ""))
        except (ValueError, AttributeError):
            return 100.0
        if threshold == 0:
            return 100.0
        headroom_pct = (threshold - actual) / threshold
        score = 50 + headroom_pct * 50
        return round(max(50.0, min(100.0, score)), 1)

    return 100.0


def match_lender(application: LoanApplication, lender: Lender) -> dict:
    app_dict = app_to_dict(application)
    applicable = get_applicable_programs(lender.programs, app_dict)

    if not applicable:
        return {
            "lender_id": lender.id,
            "is_eligible": False,
            "fit_score": 0.0,
            "program_id": None,
            "matched_program_name": None,
            "criterion_results": [],
            "rejection_reasons": ["No programs available for this application type"],
        }

    for program in applicable:
        evals = [
            {
                "criterion": c,
                "result": evaluate_criterion(c, app_dict),
            }
            for c in program.criteria
        ]

        hard_rejects_pass = all(
            e["result"]["passed"] for e in evals if e["criterion"].is_hard_reject
        )

        if hard_rejects_pass:
            total_weight = sum(e["criterion"].weight for e in evals) or 1.0
            weighted_sum = sum(
                e["criterion"].weight * _criterion_score(e["criterion"], e["result"])
                for e in evals
            )
            fit_score = round(weighted_sum / total_weight, 1)

            return {
                "lender_id": lender.id,
                "is_eligible": True,
                "fit_score": fit_score,
                "program_id": program.id,
                "matched_program_name": program.name,
                "criterion_results": [
                    {
                        "criterion_id": e["criterion"].id,
                        "criterion_label": e["criterion"].label,
                        "passed": e["result"]["passed"],
                        "actual_value": e["result"]["actual_value"],
                        "required_value": e["result"]["required_value"],
                        "explanation": e["result"]["explanation"],
                        "is_hard_reject": e["criterion"].is_hard_reject,
                    }
                    for e in evals
                ],
                "rejection_reasons": [],
            }

    best = applicable[0]
    evals = [
        {"criterion": c, "result": evaluate_criterion(c, app_dict)}
        for c in best.criteria
    ]
    rejection_reasons = [
        e["result"]["explanation"]
        for e in evals
        if e["criterion"].is_hard_reject and not e["result"]["passed"]
    ]

    return {
        "lender_id": lender.id,
        "is_eligible": False,
        "fit_score": 0.0,
        "program_id": None,
        "matched_program_name": None,
        "criterion_results": [
            {
                "criterion_id": e["criterion"].id,
                "criterion_label": e["criterion"].label,
                "passed": e["result"]["passed"],
                "actual_value": e["result"]["actual_value"],
                "required_value": e["result"]["required_value"],
                "explanation": e["result"]["explanation"],
                "is_hard_reject": e["criterion"].is_hard_reject,
            }
            for e in evals
        ],
        "rejection_reasons": rejection_reasons,
    }


def run_underwriting(application: LoanApplication, lenders: list[Lender]) -> list[dict]:
    results = [match_lender(application, lender) for lender in lenders]
    results.sort(key=lambda r: (r["is_eligible"], r["fit_score"]), reverse=True)
    return results
