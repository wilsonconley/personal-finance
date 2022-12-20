import os
from pathlib import Path

import pandas
import plaid

client_id = {
    plaid.Environment.Sandbox: "XXXXXXXXXXXX",
    plaid.Environment.Development: "",
}
secret = {
    plaid.Environment.Sandbox: "XXXXXXXXXXXX",
    plaid.Environment.Development: "",
}
if os.path.exists(Path(__file__).parent / ".access_tokens.csv"):
    stored_tokens = pandas.read_csv(Path(__file__).parent / ".access_tokens.csv")
    access_token = {
        plaid.Environment.Sandbox: list(
            stored_tokens[stored_tokens["env"] == "sandbox"]["token"]
        ),
        plaid.Environment.Development: list(
            stored_tokens[stored_tokens["env"] == "development"]["token"]
        ),
    }
else:
    access_token = {
        plaid.Environment.Sandbox: ["XXXXXXXXXXXX"],
        plaid.Environment.Development: [""],
    }
smartsheet_token = "XXXXXXXXXXXX"


def get_plaid(env: str):
    return client_id[env], secret[env], access_token[env]


def get_smartsheet():
    return smartsheet_token
