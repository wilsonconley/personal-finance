import plaid

client_id = {
    plaid.Environment.Sandbox: "XXXXXXXXXXXX",
    plaid.Environment.Development: "",
}
secret = {
    plaid.Environment.Sandbox: "XXXXXXXXXXXX",
    plaid.Environment.Development: "",
}
access_token = {
    plaid.Environment.Sandbox: ["XXXXXXXXXXXX"],
    plaid.Environment.Development: [""],
}


def get_keys(env: str):
    return client_id[env], secret[env], access_token[env]
