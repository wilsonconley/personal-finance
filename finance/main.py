import json
import typing as t

import plaid
import uvicorn
from bokeh.embed import json_item
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from plaid.api import plaid_api
from plaid.exceptions import ApiException
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from pydantic import BaseModel

import finance.plotters as plotters
from finance.budget import Budget
from finance.plaid_manager import PlaidManager
from finance.smartsheet_manager import SmartsheetManager

APP = FastAPI()


plaid_app: PlaidManager
budget: Budget


@APP.on_event("startup")
def startup():
    APP.add_middleware(
        CORSMiddleware,
        allow_origins=json.dumps(["http://127.0.0.1:5173"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Available environments are
    # 'Production'
    # 'Development'
    # 'Sandbox'
    env = plaid.Environment.Sandbox

    # Get managers
    global plaid_app
    plaid_app = PlaidManager(env)
    # smart = SmartsheetManager()

    # Load budget
    global budget
    budget = Budget()

    # Get data
    try:
        refresh()
    except ApiException:
        pass


@APP.get("/refresh_data/")
def refresh():
    # Update balances and transactions
    plaid_app.get_balances()
    plaid_app.get_transactions()

    # # Create bokeh plots
    # plotters.pie_chart_balances(plaid_app.balances)
    # plotters.pie_chart_transactions(plaid_app.transactions, plaid_app.categories)
    return "success"


class BudgetParam(BaseModel):
    budget: dict[str, float]


@APP.get("/budget/")
def get_budget():
    return json.dumps(budget.budget)


@APP.post("/budget/")
def set_budget(param: BudgetParam):
    budget.budget = param.budget
    budget.save_budget()
    return "success"


@APP.get("/table_balances/")
def table_balances():
    p = plotters.table_balances(plaid_app.balances)
    return json.dumps(json_item(p))


@APP.get("/plot_balances/")
def plot_balances():
    p = plotters.pie_chart_balances(plaid_app.balances)
    return json.dumps(json_item(p))


@APP.get("/plot_budget/")
def plot_budget():
    p = plotters.bar_graph_budget(plaid_app.transactions, budget.budget)
    return json.dumps(json_item(p))


@APP.get("/plot_transactions_in/")
def plot_transactions_in():
    p = plotters.pie_chart_transactions_in(plaid_app.transactions, plaid_app.categories)
    return json.dumps(json_item(p))


@APP.get("/plot_transactions_out/")
def plot_transactions_out():
    p = plotters.pie_chart_transactions_out(
        plaid_app.transactions, plaid_app.categories
    )
    return json.dumps(json_item(p))


@APP.get("/balances/")
def get_balances():
    return plaid_app.balances.to_json(orient="records")


@APP.get("/net_worth/")
def get_net_worth():
    return plaid_app.net_worth


class TransactionsParam(BaseModel):
    month: str
    year: str


@APP.post("/transactions/")
def get_transactions(param: TransactionsParam):
    plaid_app.filter_transactions_by_month(param.month, param.year)
    return plaid_app.transactions.to_json(orient="records")


@APP.post("/yearly_transactions/")
def yearly_transactions(param: TransactionsParam):
    plaid_app.filter_transactions_by_year(param.year)
    return plaid_app.yearly_transactions.to_json(orient="records")


@APP.get("/check_existing_tokens/")
def check_existing_tokens():
    return json.dumps(plaid_app.check_existing_tokens())


class Item(BaseModel):
    token: str


@APP.post("/create_link_token/")
def create_link_token(item: t.Optional[Item] = None):
    # Create a link_token for the given user
    if item is not None:
        request = plaid_api.LinkTokenCreateRequest(
            client_name="Personal Finance App",
            country_codes=[CountryCode("US")],
            # redirect_uri="https://domainname.com/oauth-page.html",
            language="en",
            # webhook="https://webhook.example.com",
            user=LinkTokenCreateRequestUser(client_user_id="wilsonconley"),
            access_token=item.token,
        )
    else:
        request = plaid_api.LinkTokenCreateRequest(
            products=[Products("auth")],
            client_name="Personal Finance App",
            country_codes=[CountryCode("US")],
            # redirect_uri="https://domainname.com/oauth-page.html",
            language="en",
            # webhook="https://webhook.example.com",
            user=LinkTokenCreateRequestUser(client_user_id="wilsonconley"),
        )
    response = plaid_app.client.link_token_create(request)
    response_ = response.to_dict()
    return json.dumps(response_["link_token"])


@APP.post("/exchange_public_token/")
def exchange_public_token(item: Item):
    request = plaid_api.ItemPublicTokenExchangeRequest(public_token=item.token)
    response = plaid_app.client.item_public_token_exchange(request)
    access_token = response["access_token"]
    print("retrieved access token: " + access_token)
    plaid_app.add_token(access_token)
    return json.dumps(response.to_dict())


if __name__ == "__main__":
    uvicorn.run(
        "main:APP",
        reload=True,
    )
