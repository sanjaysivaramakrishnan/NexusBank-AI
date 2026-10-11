"""Banking tools for specialized agents."""

from app.tools.customer_tools import (
    get_customer_profile,
    get_account_balance,
    get_account_details,
    get_transaction_history,
    search_customer_by_name,
)
from app.tools.risk_tools import (
    analyze_transaction_fraud,
    get_customer_risk_score,
    get_suspicious_transactions,
    report_suspicious_activity,
)
from app.tools.credit_tools import (
    check_loan_eligibility,
    get_loan_status,
    get_loan_products,
    calculate_emi,
)

CUSTOMER_TOOLS = [
    get_customer_profile,
    get_account_balance,
    get_account_details,
    get_transaction_history,
    search_customer_by_name,
]

RISK_TOOLS = [
    analyze_transaction_fraud,
    get_customer_risk_score,
    get_suspicious_transactions,
    report_suspicious_activity,
]

CREDIT_TOOLS = [
    check_loan_eligibility,
    get_loan_status,
    get_loan_products,
    calculate_emi,
]
