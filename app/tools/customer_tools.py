"""
Customer Banking Tools
-----------------------
Simulated APIs for customer profile, account, and transaction queries.
These tools are used by the Customer Agent.
"""

import json
from langchain_core.tools import tool
from app.data.bank_data import (
    CUSTOMERS,
    ACCOUNTS,
    CUSTOMER_ACCOUNTS,
    get_transactions_for_account,
    get_transactions_for_customer,
)


@tool
def get_customer_profile(customer_id: str) -> str:
    """Retrieve a customer's profile information including personal details,
    KYC status, segment, and relationship history.

    Args:
        customer_id: The unique customer identifier (e.g., CUST001)
    """
    customer = CUSTOMERS.get(customer_id.upper())
    if not customer:
        return json.dumps({"error": f"Customer '{customer_id}' not found. Valid IDs: {', '.join(CUSTOMERS.keys())}"})

    # Build a summary view (exclude sensitive fields)
    profile = {
        "id": customer["id"],
        "name": customer["name"],
        "email": customer["email"],
        "phone": customer["phone"],
        "kyc_status": customer["kyc_status"],
        "segment": customer["segment"],
        "risk_profile": customer["risk_profile"],
        "relationship_since": customer["relationship_since"],
        "occupation": customer["occupation"],
        "employer": customer["employer"],
        "credit_score": customer["credit_score"],
        "accounts": CUSTOMER_ACCOUNTS.get(customer_id.upper(), []),
    }
    return json.dumps(profile, indent=2)


@tool
def get_account_balance(account_id: str) -> str:
    """Retrieve the current balance and basic details for a specific bank account.

    Args:
        account_id: The unique account identifier (e.g., ACC001)
    """
    account = ACCOUNTS.get(account_id.upper())
    if not account:
        return json.dumps({"error": f"Account '{account_id}' not found. Valid IDs: {', '.join(ACCOUNTS.keys())}"})

    return json.dumps(
        {
            "account_id": account["id"],
            "type": account["type"],
            "balance": account["balance"],
            "currency": account["currency"],
            "status": account["status"],
        },
        indent=2,
    )


@tool
def get_account_details(account_id: str) -> str:
    """Retrieve full details of a bank account including branch info,
    interest rate, and minimum balance requirements.

    Args:
        account_id: The unique account identifier (e.g., ACC001)
    """
    account = ACCOUNTS.get(account_id.upper())
    if not account:
        return json.dumps({"error": f"Account '{account_id}' not found. Valid IDs: {', '.join(ACCOUNTS.keys())}"})

    return json.dumps(account, indent=2)


@tool
def get_transaction_history(account_id: str, limit: int = 10) -> str:
    """Retrieve recent transaction history for a specific account.

    Args:
        account_id: The unique account identifier (e.g., ACC001)
        limit: Maximum number of transactions to return (default: 10)
    """
    account = ACCOUNTS.get(account_id.upper())
    if not account:
        return json.dumps({"error": f"Account '{account_id}' not found."})

    transactions = get_transactions_for_account(account_id.upper())

    if not transactions:
        return json.dumps({"message": f"No transactions found for account {account_id}.", "transactions": []})

    # Sort by date descending and limit
    transactions = sorted(transactions, key=lambda t: t["date"], reverse=True)[:limit]

    summary = {
        "account_id": account_id.upper(),
        "total_transactions": len(transactions),
        "transactions": [
            {
                "id": t["id"],
                "date": t["date"],
                "type": t["type"],
                "amount": t["amount"],
                "description": t["description"],
                "category": t["category"],
                "status": t["status"],
                "channel": t["channel"],
            }
            for t in transactions
        ],
    }
    return json.dumps(summary, indent=2)


@tool
def search_customer_by_name(name: str) -> str:
    """Search for customers by name (partial match, case-insensitive).
    Useful when the customer ID is unknown.

    Args:
        name: The customer name to search for (partial match supported)
    """
    results = []
    for cid, customer in CUSTOMERS.items():
        if name.lower() in customer["name"].lower():
            results.append(
                {
                    "id": customer["id"],
                    "name": customer["name"],
                    "segment": customer["segment"],
                    "accounts": CUSTOMER_ACCOUNTS.get(cid, []),
                }
            )

    if not results:
        return json.dumps({"message": f"No customers found matching '{name}'.", "available_customers": [c["name"] for c in CUSTOMERS.values()]})

    return json.dumps({"results": results, "count": len(results)}, indent=2)
