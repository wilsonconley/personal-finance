import typing as t
from datetime import datetime

import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.transactions_get_request import TransactionsGetRequest

try:
    from plaid_keys import get_keys
except ModuleNotFoundError:
    print("rename sample_plaid_keys.py to plaid_keys.py and insert your API keys")


class PlaidManager:
    client_id: str
    secret: str
    access_token: list[str]
    api_client: plaid.ApiClient
    client: plaid_api.PlaidApi

    def __init__(self, env: str) -> None:
        client_id, secret, access_token = get_keys(env)
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


if __name__ == "__main__":
    # Available environments are
    # 'Production'
    # 'Development'
    # 'Sandbox'
    env = plaid.Environment.Sandbox
    app = PlaidManager(env)
    transactions = app.get_transactions()
    print(transactions)
