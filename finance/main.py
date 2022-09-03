import json

import plaid
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import finance.plotters as plotters
from finance.plaid_manager import PlaidManager
from finance.smartsheet_manager import SmartsheetManager

APP = FastAPI()


plaid_app: PlaidManager


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

    # Create bokeh plots
    plotters.pie_chart_bokeh(plaid_app.balances)

    # # Create matplotlib plots
    # plotters.pie_chart_matplotlib(plaid_app.balances)

    # # Create balances table
    # plotters.table_bokeh(plaid_app.balances)


@APP.get("/refresh/")
def refresh():
    plaid_app.get_balances()
    plaid_app.get_transactions()
    return "success"


@APP.get("/balances/")
def get_balances():
    return plaid_app.balances.to_json(orient="records")


@APP.get("/transactions/")
def get_transactions():
    return plaid_app.transactions.to_json(orient="records")


if __name__ == "__main__":
    # startup()
    uvicorn.run(
        "main:APP",
        reload=True,
    )
