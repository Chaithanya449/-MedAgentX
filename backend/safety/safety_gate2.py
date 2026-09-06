def safety_gate2(assessment, risk_result):

    if "you have" in str(assessment).lower():
        return {"safe": False}

    if "disclaimer" not in assessment:
        return {"safe": False}

    if risk_result["risk_level"] == "HIGH" and "low risk" in str(assessment).lower():
        return {"safe": False}

    return {
        "safe": True,
        "assessment": assessment,
        "risk": risk_result
    }