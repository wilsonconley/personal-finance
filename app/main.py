import plaid

from plaid_manager import PlaidManager
from smartsheet_manager import SmartsheetManager

if __name__ == "__main__":
    # Available environments are
    # 'Production'
    # 'Development'
    # 'Sandbox'
    env = plaid.Environment.Sandbox

    # Get managers
    app = PlaidManager(env)
    smart = SmartsheetManager()

    # Transactions
    transactions = app.get_transactions()
    data = {key: [i[key] for i in transactions] for key in transactions[0].to_dict()}

    sheet_id = smart.get_sheet_id("Transactions")
    smart.add_rows(sheet_id, data, "transaction_id")

    # Balances
    accounts = app.get_balances()
    new_accounts = [account.to_dict() for account in accounts]
    for account in new_accounts:
        account["balances"] = account["balances"]["available"]
    data = {key: [i[key] for i in new_accounts] for key in new_accounts[0]}

    sheet_id = smart.get_sheet_id("Balances")
    smart.add_rows(sheet_id, data, "account_id")
