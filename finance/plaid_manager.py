import json
import os
from time import sleep
import typing as t
from datetime import datetime
from pathlib import Path

import pandas as pd
import plaid
from plaid.api import plaid_api
from plaid.exceptions import ApiException
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import (
    TransactionsGetRequestOptions,
)

from finance.api_keys import get_plaid


class PlaidManager:
    # API
    client_id: str
    secret: str
    access_tokens: list[str]
    api_client: plaid.ApiClient
    client: plaid_api.PlaidApi
    env: str

    # Data
    balances: pd.DataFrame
    transactions: pd.DataFrame

    # Helpers
    categories: list[str] = [
        "INCOME",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "LOAN_PAYMENTS",
        "BANK_FEES",
        "ENTERTAINMENT",
        "FOOD_AND_DRINK",
        "GENERAL_MERCHANDISE",
        "HOME_IMPROVEMENT",
        "MEDICAL",
        "PERSONAL_CARE",
        "GENERAL_SERVICES",
        "GOVERNMENT_AND_NON_PROFIT",
        "TRANSPORTATION",
        "TRAVEL",
        "RENT_AND_UTILITIES",
    ]

    def __init__(self, env: str) -> None:
        client_id, secret, access_tokens = get_plaid(env)
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
        self.access_tokens = access_tokens
        self.api_client = api_client
        self.client = client
        self.env = env

    def check_existing_tokens(self) -> list[str]:
        bad_tokens = []
        for token in self.access_tokens:
            request = AccountsBalanceGetRequest(access_token=token)
            try:
                self.client.accounts_balance_get(request)
            except ApiException:
                bad_tokens.append(token)
        return bad_tokens

    def add_token(self, access_token: str) -> None:
        self.access_tokens.append(access_token)
        token_df = pd.DataFrame({"token": self.access_tokens, "env": self.env})
        if os.path.exists(Path(__file__).parent / "api_keys/.access_tokens.csv"):
            existing_df = pd.read_csv(
                Path(__file__).parent / "api_keys/.access_tokens.csv"
            )
            token_df.merge(existing_df)
            token_df = pd.concat(
                [token_df, existing_df], ignore_index=True
            ).drop_duplicates()
        token_df.to_csv(
            Path(__file__).parent / "api_keys/.access_tokens.csv", index=False
        )

    def get_transactions(
        self, access_tokens: t.Optional[list[str]] = None
    ) -> pd.DataFrame:
        if not access_tokens:
            access_tokens = self.access_tokens

        transactions = []
        for token in access_tokens:
            request = TransactionsGetRequest(
                access_token=token,
                start_date=datetime.strptime("2020-01-01", "%Y-%m-%d").date(),
                end_date=datetime.strptime("2021-01-01", "%Y-%m-%d").date(),
                options=TransactionsGetRequestOptions(
                    include_personal_finance_category=True
                ),
            )
            retries = 3
            response = None
            for _ in range(0, retries):
                try:
                    response = self.client.transactions_get(request)
                except ApiException as exc:
                    print(f"ERROR LOADING TRANSACTIONS FOR {token}")
                    http_response = json.loads(exc.body)
                    if http_response["error_code"] == "PRODUCT_NOT_READY":
                        print("retrying...")
                        sleep(5)
            if response is None:
                print(f"failed to load transasctions for {token}")
                continue

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

        # Additional formatting
        self.transactions["datestr"] = [
            x.strftime("%Y-%m-%d") for x in self.transactions["date"]
        ]
        self.transactions["personal_finance_category_primary"] = [
            x["primary"] for x in self.transactions["personal_finance_category"]
        ]

        return self.transactions

    def get_balances(self, access_tokens: t.Optional[list[str]] = None) -> pd.DataFrame:
        if not access_tokens:
            access_tokens = self.access_tokens

        accounts = []
        for token in access_tokens:
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

        # Additional formatting
        self.balances["balances_str"] = [f"${x:.2f}" for x in self.balances["balances"]]
        self.balances["legend"] = [
            f"{name} ({id[0:4]})"
            for id, name in zip(self.balances["account_id"], self.balances["name"])
        ]

        return self.balances
