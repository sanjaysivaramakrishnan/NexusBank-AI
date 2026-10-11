"""
Credit & Loan Tools
--------------------
Simulated APIs for loan eligibility, loan status, product catalog, and EMI calculations.
These tools are used by the Credit/Loan Agent.
"""

import json
import math
from langchain_core.tools import tool
from app.data.bank_data import (
    CUSTOMERS,
    LOANS,
    CUSTOMER_LOANS,
    LOAN_PRODUCTS,
)


@tool
def check_loan_eligibility(customer_id: str, loan_type: str, requested_amount: float) -> str:
    """Check whether a customer is eligible for a specific type of loan.
    Evaluates credit score, income, existing obligations, and risk profile.

    Args:
        customer_id: The unique customer identifier (e.g., CUST001)
        loan_type: Type of loan - one of: home_loan, personal_loan, car_loan, business_loan, education_loan
        requested_amount: The loan amount requested in INR
    """
    customer = CUSTOMERS.get(customer_id.upper())
    if not customer:
        return json.dumps({"error": f"Customer '{customer_id}' not found."})

    # Find the matching loan product
    product = None
    for p in LOAN_PRODUCTS:
        if p["type"] == loan_type:
            product = p
            break

    if not product:
        valid_types = [p["type"] for p in LOAN_PRODUCTS]
        return json.dumps({"error": f"Unknown loan type '{loan_type}'. Valid types: {', '.join(valid_types)}"})

    # Run eligibility checks
    checks = []
    eligible = True

    # 1. Credit score check
    if customer["credit_score"] >= product["min_credit_score"]:
        checks.append({"check": "Credit Score", "status": "PASS", "detail": f"Score {customer['credit_score']} >= minimum {product['min_credit_score']}"})
    else:
        checks.append({"check": "Credit Score", "status": "FAIL", "detail": f"Score {customer['credit_score']} < minimum {product['min_credit_score']}"})
        eligible = False

    # 2. Income check
    if customer["annual_income"] >= product["min_income"]:
        checks.append({"check": "Annual Income", "status": "PASS", "detail": f"₹{customer['annual_income']:,} >= minimum ₹{product['min_income']:,}"})
    else:
        checks.append({"check": "Annual Income", "status": "FAIL", "detail": f"₹{customer['annual_income']:,} < minimum ₹{product['min_income']:,}"})
        eligible = False

    # 3. Amount range check
    if product["min_amount"] <= requested_amount <= product["max_amount"]:
        checks.append({"check": "Loan Amount", "status": "PASS", "detail": f"₹{requested_amount:,.0f} is within range ₹{product['min_amount']:,} - ₹{product['max_amount']:,}"})
    else:
        checks.append({"check": "Loan Amount", "status": "FAIL", "detail": f"₹{requested_amount:,.0f} is outside range ₹{product['min_amount']:,} - ₹{product['max_amount']:,}"})
        eligible = False

    # 4. KYC check
    if customer["kyc_status"] == "verified":
        checks.append({"check": "KYC Status", "status": "PASS", "detail": "KYC verified"})
    else:
        checks.append({"check": "KYC Status", "status": "FAIL", "detail": f"KYC status is '{customer['kyc_status']}'. Must be verified."})
        eligible = False

    # 5. Existing obligation check (FOIR - Fixed Obligation to Income Ratio)
    existing_emi = sum(
        LOANS[lid]["emi"]
        for lid in CUSTOMER_LOANS.get(customer_id.upper(), [])
        if LOANS[lid]["status"] == "active"
    )
    monthly_income = customer["annual_income"] / 12
    foir = existing_emi / monthly_income if monthly_income > 0 else 1.0

    if foir <= 0.5:
        checks.append({"check": "Debt-to-Income Ratio", "status": "PASS", "detail": f"FOIR {foir:.1%} <= 50% threshold. Existing EMIs: ₹{existing_emi:,.0f}/month"})
    else:
        checks.append({"check": "Debt-to-Income Ratio", "status": "FAIL", "detail": f"FOIR {foir:.1%} > 50% threshold. Existing EMIs: ₹{existing_emi:,.0f}/month"})
        eligible = False

    # 6. Risk profile check
    if customer["risk_profile"] != "high":
        checks.append({"check": "Risk Profile", "status": "PASS", "detail": f"Risk profile '{customer['risk_profile']}' is acceptable"})
    else:
        checks.append({"check": "Risk Profile", "status": "WARNING", "detail": f"Risk profile is 'high'. Manual review required."})

    result = {
        "customer_id": customer_id.upper(),
        "customer_name": customer["name"],
        "loan_type": product["name"],
        "requested_amount": requested_amount,
        "eligible": eligible,
        "eligibility_checks": checks,
        "interest_rate_range": product["interest_rate_range"],
        "max_tenure": f"{product['max_tenure_months']} months",
        "processing_fee": product["processing_fee"],
    }

    if eligible:
        result["next_steps"] = [
            "Submit loan application with required documents",
            "Documents: ID proof, address proof, income proof, bank statements (6 months)",
            "Application will be processed within 3-5 business days",
        ]
    else:
        result["suggestions"] = [
            "Improve credit score by maintaining regular payments",
            "Reduce existing loan obligations",
            "Complete KYC verification if pending",
            "Consider a lower loan amount",
        ]

    return json.dumps(result, indent=2)


@tool
def get_loan_status(loan_id: str) -> str:
    """Retrieve the current status and details of an existing loan.

    Args:
        loan_id: The unique loan identifier (e.g., LOAN001)
    """
    loan = LOANS.get(loan_id.upper())
    if not loan:
        return json.dumps({"error": f"Loan '{loan_id}' not found. Valid IDs: {', '.join(LOANS.keys())}"})

    customer = CUSTOMERS.get(loan["customer_id"], {})

    result = {
        "loan_id": loan["id"],
        "customer_name": customer.get("name", "Unknown"),
        "type": loan["type"].replace("_", " ").title(),
        "status": loan["status"].upper(),
        "sanctioned_amount": f"₹{loan['amount']:,}",
        "outstanding_amount": f"₹{loan['outstanding']:,}",
        "interest_rate": f"{loan['interest_rate']}%",
        "monthly_emi": f"₹{loan['emi']:,}",
        "tenure": f"{loan['tenure_months']} months",
        "emi_paid": loan["emi_paid"],
        "emi_remaining": loan["emi_remaining"],
        "next_emi_date": loan["next_emi_date"],
        "disbursed_date": loan["disbursed_date"],
        "overdue_amount": f"₹{loan['overdue_amount']:,}" if loan["overdue_amount"] > 0 else "₹0",
        "collateral": loan["collateral"],
    }

    if loan["overdue_amount"] > 0:
        result["alert"] = f"⚠️ Overdue amount of ₹{loan['overdue_amount']:,} detected. Please clear dues to avoid penalties."

    return json.dumps(result, indent=2)


@tool
def get_loan_products() -> str:
    """Retrieve the catalog of all available loan products with their
    eligibility criteria, interest rates, and features."""
    products = []
    for p in LOAN_PRODUCTS:
        products.append(
            {
                "name": p["name"],
                "type": p["type"],
                "amount_range": f"₹{p['min_amount']:,} - ₹{p['max_amount']:,}",
                "interest_rate": p["interest_rate_range"],
                "max_tenure": f"{p['max_tenure_months']} months",
                "min_credit_score": p["min_credit_score"],
                "min_annual_income": f"₹{p['min_income']:,}",
                "processing_fee": p["processing_fee"],
                "features": p["features"],
            }
        )

    return json.dumps({"loan_products": products, "total": len(products)}, indent=2)


@tool
def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> str:
    """Calculate the Equated Monthly Installment (EMI) for a loan.

    Args:
        principal: The loan principal amount in INR
        annual_rate: Annual interest rate as a percentage (e.g., 10.5 for 10.5%)
        tenure_months: Loan tenure in months
    """
    if principal <= 0:
        return json.dumps({"error": "Principal must be greater than 0."})
    if annual_rate <= 0:
        return json.dumps({"error": "Interest rate must be greater than 0."})
    if tenure_months <= 0:
        return json.dumps({"error": "Tenure must be greater than 0 months."})

    monthly_rate = annual_rate / (12 * 100)
    emi = principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months) / (math.pow(1 + monthly_rate, tenure_months) - 1)
    total_payment = emi * tenure_months
    total_interest = total_payment - principal

    result = {
        "principal": f"₹{principal:,.2f}",
        "annual_interest_rate": f"{annual_rate}%",
        "tenure": f"{tenure_months} months ({tenure_months // 12} years {tenure_months % 12} months)",
        "monthly_emi": f"₹{emi:,.2f}",
        "total_payment": f"₹{total_payment:,.2f}",
        "total_interest": f"₹{total_interest:,.2f}",
        "interest_to_principal_ratio": f"{(total_interest / principal * 100):.1f}%",
    }
    return json.dumps(result, indent=2)
