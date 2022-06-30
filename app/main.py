import typing as t
from datetime import datetime

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

from smartsheet_manager import SmartsheetManager

try:
    from api_keys import get_plaid
except ModuleNotFoundError as exc:
    print(
        "\nERROR: rename sample_api_keys.py to api_keys.py and insert your API keys!!\n"
    )
    raise exc


class PlaidManager:
    client_id: str
    secret: str
    access_token: list[str]
    api_client: plaid.ApiClient
    client: plaid_api.PlaidApi

    def __init__(self, env: str) -> None:
        client_id, secret, access_token = get_plaid(env)
        configuration = plaid.Configuration(
            host=env,
            api_key={
                "clientId": client_id,
                "secret": secret,
            },
        )
        api_client = plaid.ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)

        self.client_id = client_id
        self.secret = secret
        self.access_token = access_token
        self.api_client = api_client
        self.client = client

    def get_transactions(
        self, access_token: t.Optional[list[str]] = None
    ) -> list[dict[str, t.Any]]:
        if not access_token:
            access_token = self.access_token

        transactions = []
        for token in access_token:
            request = TransactionsGetRequest(
                access_token=token,
                start_date=datetime.strptime("2020-01-01", "%Y-%m-%d").date(),
                end_date=datetime.strptime("2021-01-01", "%Y-%m-%d").date(),
            )
            response = self.client.transactions_get(request)
            transactions.extend(response["transactions"])

            # the transactions in the response are paginated, so make multiple calls while increasing the offset to
            # retrieve all transactions
            while len(transactions) < response["total_transactions"]:
                options = TransactionsGetRequestOptions()
                options.offset = len(transactions)

                request = TransactionsGetRequest(
                    access_token=token,
                    start_date=datetime.strptime("2020-01-01", "%Y-%m-%d").date(),
                    end_date=datetime.strptime("2021-01-01", "%Y-%m-%d").date(),
                    options=options,
                )
                response = self.client.transactions_get(request)
                transactions.extend(response["transactions"])

        return transactions

    def get_balances(
        self, access_token: t.Optional[list[str]] = None
    ) -> list[dict[str, t.Any]]:
        if not access_token:
            access_token = self.access_token

        accounts = []
        for token in access_token:
            # Pull real-time balance information for each account associated with the Item
            request = AccountsBalanceGetRequest(access_token=token)
            response = self.client.accounts_balance_get(request)
            accounts.extend(response["accounts"])
        return accounts


if __name__ == "__main__":
    # Available environments are
    # 'Production'
    # 'Development'
    # 'Sandbox'
    env = plaid.Environment.Sandbox
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
