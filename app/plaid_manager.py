import typing as t
from datetime import datetime

import pandas as pd
import plaid
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import (
    TransactionsGetRequestOptions,
)

from app.api_keys import get_plaid

class PlaidManager:
    client_id: str
    secret: str
    access_token: list[str]
    api_client: plaid.ApiClient
    client: plaid_api.PlaidApi

    balances: pd.DataFrame
    transactions: pd.DataFrame

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
    ) -> pd.DataFrame:
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

        # Parse data into DataFrame
        data = {
            key: [i[key] for i in transactions] for key in transactions[0].to_dict()
        }
        self.transactions = pd.DataFrame(data)
        return self.transactions

    def get_balances(self, access_token: t.Optional[list[str]] = None) -> pd.DataFrame:
        if not access_token:
            access_token = self.access_token

        accounts = []
        for token in access_token:
            # Pull real-time balance information for each account associated with the Item
            request = AccountsBalanceGetRequest(access_token=token)
            response = self.client.accounts_balance_get(request)
            accounts.extend(response["accounts"])

        # Parse data into DataFrame
        accounts_ = [account.to_dict() for account in accounts]
        for account in accounts_:
            account["balances"] = account["balances"]["available"]
        data = {key: [i[key] for i in accounts_] for key in accounts_[0]}
        self.balances = pd.DataFrame(data)
        return self.balances
