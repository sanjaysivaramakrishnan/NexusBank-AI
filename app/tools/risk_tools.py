"""
Risk & Fraud Detection Tools
------------------------------
Simulated APIs for fraud analysis, risk scoring, and suspicious activity monitoring.
These tools are used by the Risk/Fraud Agent.
"""

import json
from datetime import datetime
from langchain_core.tools import tool
from app.data.bank_data import (
    CUSTOMERS,
    ACCOUNTS,
    TRANSACTIONS,
    CUSTOMER_ACCOUNTS,
    FRAUD_RULES,
    FRAUD_REPORTS,
    get_transactions_for_account,
    get_transactions_for_customer,
)


def _compute_fraud_indicators(transaction: dict) -> list[str]:
    """Compute fraud indicators for a single transaction."""
    indicators = []

    # High amount
    if transaction["amount"] >= FRAUD_RULES["high_amount_threshold"]:
        indicators.append(f"HIGH_AMOUNT: ₹{transaction['amount']:,.2f} exceeds threshold of ₹{FRAUD_RULES['high_amount_threshold']:,}")

    # Unusual hours
    try:
        hour = int(transaction.get("time", "12:00:00").split(":")[0])
        if FRAUD_RULES["unusual_hours"]["start"] <= hour <= FRAUD_RULES["unusual_hours"]["end"]:
            indicators.append(f"UNUSUAL_HOURS: Transaction at {transaction['time']} (between midnight and 5 AM)")
    except (ValueError, IndexError):
        pass

    # High risk location
    if transaction.get("location") in FRAUD_RULES["high_risk_locations"]:
        indicators.append(f"HIGH_RISK_LOCATION: Transaction from {transaction['location']}")

    # High risk channel
    if transaction.get("channel") in FRAUD_RULES["high_risk_channels"]:
        indicators.append(f"HIGH_RISK_CHANNEL: Transaction via {transaction['channel']}")

    # Flagged status
    if transaction.get("status") in ("flagged", "under_review"):
        indicators.append(f"STATUS_FLAG: Transaction is currently '{transaction['status']}'")

    return indicators


@tool
def analyze_transaction_fraud(transaction_id: str) -> str:
    """Analyze a specific transaction for potential fraud indicators.
    Returns the fraud score, risk level, and detailed indicators.

    Args:
        transaction_id: The unique transaction identifier (e.g., TXN001)
    """
    transaction = None
    for t in TRANSACTIONS:
        if t["id"] == transaction_id.upper():
            transaction = t
            break

    if not transaction:
        valid_ids = [t["id"] for t in TRANSACTIONS]
        return json.dumps({"error": f"Transaction '{transaction_id}' not found. Valid IDs: {', '.join(valid_ids)}"})

    fraud_score = transaction["fraud_score"]
    indicators = _compute_fraud_indicators(transaction)

    # Determine risk level
    if fraud_score >= 0.8:
        risk_level = "CRITICAL"
        recommendation = "BLOCK transaction and escalate to fraud investigation team immediately."
    elif fraud_score >= 0.5:
        risk_level = "HIGH"
        recommendation = "Flag for manual review. Contact customer for verification."
    elif fraud_score >= 0.3:
        risk_level = "MEDIUM"
        recommendation = "Monitor closely. Add to watchlist."
    else:
        risk_level = "LOW"
        recommendation = "No action required. Transaction appears legitimate."

    result = {
        "transaction_id": transaction["id"],
        "amount": transaction["amount"],
        "merchant": transaction["merchant"],
        "date": transaction["date"],
        "time": transaction["time"],
        "location": transaction["location"],
        "channel": transaction["channel"],
        "status": transaction["status"],
        "fraud_score": fraud_score,
        "risk_level": risk_level,
        "indicators": indicators,
        "recommendation": recommendation,
    }
    return json.dumps(result, indent=2)


@tool
def get_customer_risk_score(customer_id: str) -> str:
    """Calculate an overall risk score for a customer based on their
    transaction patterns, profile, and account activity.

    Args:
        customer_id: The unique customer identifier (e.g., CUST001)
    """
    customer = CUSTOMERS.get(customer_id.upper())
    if not customer:
        return json.dumps({"error": f"Customer '{customer_id}' not found."})

    transactions = get_transactions_for_customer(customer_id.upper())

    # Calculate metrics
    total_transactions = len(transactions)
    flagged_count = sum(1 for t in transactions if t["status"] in ("flagged", "under_review"))
    high_risk_count = sum(1 for t in transactions if t["fraud_score"] >= 0.5)
    avg_fraud_score = sum(t["fraud_score"] for t in transactions) / max(total_transactions, 1)

    # Total amount by type
    total_debit = sum(t["amount"] for t in transactions if t["type"] == "debit")
    total_credit = sum(t["amount"] for t in transactions if t["type"] == "credit")

    # Overall risk calculation
    overall_risk = min(1.0, avg_fraud_score + (flagged_count * 0.15) + (high_risk_count * 0.1))

    if overall_risk >= 0.6:
        risk_category = "HIGH RISK"
        action = "Mandatory review required. Consider account restrictions."
    elif overall_risk >= 0.3:
        risk_category = "MEDIUM RISK"
        action = "Enhanced monitoring recommended. Review flagged transactions."
    else:
        risk_category = "LOW RISK"
        action = "Standard monitoring. No immediate action required."

    result = {
        "customer_id": customer_id.upper(),
        "customer_name": customer["name"],
        "profile_risk": customer["risk_profile"],
        "credit_score": customer["credit_score"],
        "overall_risk_score": round(overall_risk, 3),
        "risk_category": risk_category,
        "transaction_summary": {
            "total_transactions": total_transactions,
            "flagged_transactions": flagged_count,
            "high_risk_transactions": high_risk_count,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "average_fraud_score": round(avg_fraud_score, 3),
        },
        "recommended_action": action,
    }
    return json.dumps(result, indent=2)


@tool
def get_suspicious_transactions(account_id: str) -> str:
    """Retrieve all transactions flagged as suspicious or under review
    for a specific account, along with their fraud indicators.

    Args:
        account_id: The unique account identifier (e.g., ACC004)
    """
    account = ACCOUNTS.get(account_id.upper())
    if not account:
        return json.dumps({"error": f"Account '{account_id}' not found."})

    transactions = get_transactions_for_account(account_id.upper())

    suspicious = []
    for t in transactions:
        if t["fraud_score"] >= 0.3 or t["status"] in ("flagged", "under_review"):
            indicators = _compute_fraud_indicators(t)
            suspicious.append(
                {
                    "id": t["id"],
                    "date": t["date"],
                    "time": t["time"],
                    "amount": t["amount"],
                    "merchant": t["merchant"],
                    "location": t["location"],
                    "fraud_score": t["fraud_score"],
                    "status": t["status"],
                    "indicators": indicators,
                }
            )

    # Sort by fraud score descending
    suspicious.sort(key=lambda x: x["fraud_score"], reverse=True)

    result = {
        "account_id": account_id.upper(),
        "customer_id": account["customer_id"],
        "total_suspicious": len(suspicious),
        "suspicious_transactions": suspicious,
    }
    return json.dumps(result, indent=2)


@tool
def report_suspicious_activity(transaction_id: str, reason: str) -> str:
    """Report a transaction as suspicious / potentially fraudulent.
    This creates a fraud report entry for investigation.

    Args:
        transaction_id: The transaction ID to report (e.g., TXN008)
        reason: Description of why this transaction is suspicious
    """
    transaction = None
    for t in TRANSACTIONS:
        if t["id"] == transaction_id.upper():
            transaction = t
            break

    if not transaction:
        return json.dumps({"error": f"Transaction '{transaction_id}' not found."})

    report = {
        "report_id": f"FR{len(FRAUD_REPORTS) + 1:04d}",
        "transaction_id": transaction_id.upper(),
        "amount": transaction["amount"],
        "reported_at": datetime.now().isoformat(),
        "reason": reason,
        "status": "under_investigation",
        "assigned_to": "Fraud Investigation Unit",
    }

    FRAUD_REPORTS.append(report)

    return json.dumps(
        {
            "message": "Fraud report submitted successfully.",
            "report": report,
        },
        indent=2,
    )
