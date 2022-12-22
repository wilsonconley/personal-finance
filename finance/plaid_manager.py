import json
import os
import typing as t
from datetime import datetime
from pathlib import Path
from time import sleep

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
from finance.rules import Rules


class PlaidManager:
    # API
    client_id: str
    secret: str
    access_tokens: list[str]
    api_client: plaid.ApiClient
    client: plaid_api.PlaidApi
    env: str

    # Data
    balances: pd.DataFrame = pd.DataFrame({})
    net_worth: float
    transactions: pd.DataFrame
    transactions_all: pd.DataFrame
    yearly_transactions: pd.DataFrame

    # Helpers
    base_categories: list[str] = [
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
    categories: list[str]

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

        self.categories = self.base_categories

        self.transactions = pd.DataFrame()

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
                start_date=datetime.strptime("2015-01-01", "%Y-%m-%d").date(),
                end_date=datetime.now().date(),
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
                options = TransactionsGetRequestOptions(
                    include_personal_finance_category=True
                )
                options.offset = len(transactions)

                request = TransactionsGetRequest(
                    access_token=token,
                    start_date=datetime.strptime("2015-01-01", "%Y-%m-%d").date(),
                    end_date=datetime.now().date(),
                    options=options,
                )
                response = self.client.transactions_get(request)
                transactions.extend(response["transactions"])

        # Parse data into DataFrame
        data = (
            {key: [i[key] for i in transactions] for key in transactions[0].to_dict()}
            if transactions
            else {"date": [], "personal_finance_category": []}
        )
        self.transactions_all = pd.DataFrame(data)

        # Additional formatting
        self.transactions_all["datestr"] = [
            x.strftime("%Y-%m-%d") for x in self.transactions_all["date"]
        ]
        self.transactions_all["personal_finance_category_primary"] = [
            _get_primary_category(x)
            for x in self.transactions_all["personal_finance_category"]
        ]

        self.apply_user_categories()

        return self.transactions_all

    def apply_user_categories(self) -> None:
        for df in (self.transactions, self.transactions_all):
            if len(df) == 0:
                continue

            # Apply custom rulesets for categorizing
            user_categories = ["" for _ in range(0, len(df))]
            for index, transaction in df.iterrows():
                for _, rule in Rules().rules.iterrows():
                    if eval(rule["condition"]):
                        user_categories[index] = rule["categorize"]
            if "user_category" in df.columns:
                df.loc[
                    [True for _ in range(len(df))], "user_category"
                ] = user_categories
            else:
                df.insert(len(df.columns), "user_category", user_categories)

            # Choose category for plotting
            plot_categories = []
            for _, transaction in df.iterrows():
                to_append = (
                    transaction["user_category"]
                    if transaction["user_category"]
                    else transaction["personal_finance_category_primary"]
                )
                plot_categories.append(to_append)
            if "plot_category" in df.columns:
                df.loc[
                    [True for _ in range(len(df))], "plot_category"
                ] = plot_categories
            else:
                df.insert(len(df.columns), "plot_category", plot_categories)

            self.categories = self.base_categories + list(
                set([x for x in plot_categories if x not in self.base_categories])
            )

    def filter_transactions_by_month(self, month: str, year: str) -> None:
        selector = [
            str(x)[0:4] == year and int(str(x)[5:7]) == int(month)
            for x in self.transactions_all["date"]
        ]
        self.transactions = self.transactions_all[selector]
        self.transactions.index = range(len(self.transactions))

    def filter_transactions_by_year(self, year: str) -> None:
        selector = [str(x)[0:4] == year for x in self.transactions_all["date"]]
        self.yearly_transactions = self.transactions_all[selector]
        self.yearly_transactions.index = range(len(self.yearly_transactions))

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
        data = (
            {key: [i[key] for i in accounts_] for key in accounts_[0]}
            if accounts_
            else {"account_id": [], "balances": [], "name": []}
        )
        self.balances = pd.DataFrame(data)

        # Additional formatting
        self.balances["balances_str"] = [f"${x:.2f}" for x in self.balances["balances"]]
        # self.balances["legend"] = [
        #     f"{name} ({id[0:4]})"
        #     for id, name in zip(self.balances["account_id"], self.balances["name"])
        # ]
        self.balances["legend"] = [
            f"{name} - {official_name}"
            for official_name, name in zip(
                self.balances["official_name"], self.balances["name"]
            )
        ]

        # Calculate net worth
        self.net_worth = sum(self.balances["balances"])

        return self.balances


def _get_primary_category(category: dict[str, str]) -> str:
    if category is not None and "primary" in category:
        return category["primary"]
    else:
        return "N/A"
