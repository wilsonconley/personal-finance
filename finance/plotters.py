import copy
import typing as t
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bokeh.io import export_svg
from bokeh.models import ColumnDataSource, DataTable, LabelSet, TableColumn, FactorRange
from bokeh.palettes import Category20c
from bokeh.plotting import figure, output_file, save, show, Figure
from bokeh.transform import cumsum, factor_cmap, dodge


def table_balances(balances_df: pd.DataFrame) -> Figure:
    columns = [
        TableColumn(field="legend", title="Name"),
        TableColumn(field="balances", title="Balance"),
    ]
    p = bokeh_data_table(
        balances_df,
        columns,
        height=280,
        width=400,
    )
    return p


def bokeh_data_table(
    df: pd.DataFrame,
    columns: list[TableColumn],
    height: int,
    width: int,
) -> Figure:
    source = ColumnDataSource(df)
    p = DataTable(source=source, columns=columns, width=width, height=height)
    return p


def pie_chart_balances(balances_df: pd.DataFrame) -> Figure:
    p = bokeh_pie_chart(
        balances_df,
        "balances",
        "legend",
        "balances_str",
        "balances",
        height=400,
        width=700,
    )
    return p


def bar_graph_budget(transaction_df: pd.DataFrame, budget: dict[str, float]) -> Figure:
    # Set params
    height = 400
    width = 700

    # Exclude irrelevant fields from chart
    budget = copy.deepcopy(budget)
    exclude = ["TRANSFER_IN", "INCOME"]
    for x in exclude:
        budget.pop(x)

    # Get Transactions
    categories = budget.keys()
    transaction_dict = {"category": [], "total": []}
    for category in categories:
        selector = [
            x == category for x in transaction_df["personal_finance_category_primary"]
        ]
        total = abs(sum(transaction_df["amount"][selector]))
        # if total > 0:
        #     # Only include non-zero and non-negative transactions
        #     transaction_dict["category"].append(category)
        #     transaction_dict["total"].append(total)
        transaction_dict["category"].append(category)
        transaction_dict["total"].append(total)
    df = pd.DataFrame(transaction_dict)
    df["labels"] = [f"${x:.2f}" for x in df["total"]]

    # Format data
    data = {"categories": [], "budget": [], "transactions": []}
    for x in categories:
        b = budget[x]
        idx = transaction_dict["category"].index(x)
        t = transaction_dict["total"][idx]
        if b != 0.0 or t != 0.0:
            data["categories"].append(x)
            data["budget"].append(b)
            data["transactions"].append(t)

    source = ColumnDataSource(data=data)
    p = figure(
        x_range=data["categories"],
        height=height,
        width=width,
        title="Budget Transactions",
        toolbar_location=None,
        tools="hover",
        tooltips=[("Budget", "$@budget"), ("Transactions", "$@transactions")],
    )
    p.vbar(
        x=dodge("categories", -0.125, range=p.x_range),
        top="budget",
        width=0.2,
        source=source,
        color="#2171b5",
        legend_label="Budget",
    )
    p.vbar(
        x=dodge("categories", 0.125, range=p.x_range),
        top="transactions",
        width=0.2,
        source=source,
        color="#FFDA00",
        legend_label="Transactions",
    )
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.legend.orientation = "vertical"
    p.xaxis.major_label_orientation = np.pi / 4
    p.y_range.start = 0
    p.add_layout(p.legend[0], "right")

    return p


def pie_chart_transactions_out(
    transaction_df: pd.DataFrame, categories: list[str]
) -> Figure:
    # Transactions Out
    transaction_dict = {"category": [], "total": []}
    for category in categories:
        selector = [
            x == category for x in transaction_df["personal_finance_category_primary"]
        ]
        total = sum(transaction_df["amount"][selector])
        if total > 0:
            # Only include non-zero and non-negative transactions
            transaction_dict["category"].append(category)
            transaction_dict["total"].append(total)
    df = pd.DataFrame(transaction_dict)
    df["labels"] = [f"${x:.2f}" for x in df["total"]]
    p = bokeh_pie_chart(
        df, "total", "category", "labels", "transactions_out", height=250, width=350
    )
    return p


def pie_chart_transactions_in(
    transaction_df: pd.DataFrame, categories: list[str]
) -> Figure:
    # Transactions In
    transaction_dict = {"category": [], "total": []}
    for category in categories:
        selector = [
            x == category for x in transaction_df["personal_finance_category_primary"]
        ]
        total = sum(transaction_df["amount"][selector])
        if total < 0:
            # Only include negative transactions
            transaction_dict["category"].append(category)
            transaction_dict["total"].append(total * -1)
    df = pd.DataFrame(transaction_dict)
    df["labels"] = [f"${x:.2f}" for x in df["total"]]
    p = bokeh_pie_chart(
        df, "total", "category", "labels", "transactions_in", height=250, width=350
    )
    return p


def bokeh_pie_chart(
    df: pd.DataFrame,
    angle_col: str,
    legend_col: str,
    label_col: str,
    filename: str,
    height: int,
    width: int,
) -> Figure:
    # Calculate angles of each data set
    df["angle"] = df[angle_col] / df[angle_col].sum() * 2 * np.pi
    count = len(df[angle_col])
    if count < min(Category20c.keys()):
        df["color"] = Category20c[min(Category20c.keys())][0:count]
    elif count > max(Category20c.keys()):
        df["color"] = (
            Category20c[max(Category20c.keys())]
            * int(np.ceil(count / max(Category20c.keys())))
        )[0:count]
    else:
        df["color"] = Category20c[count]

    # Create plot
    p = figure(
        height=height,
        width=width,
        # title="Account Balances Overview",
        toolbar_location=None,
        tools="hover",
        tooltips=f"@{legend_col}: @{label_col}",
        x_range=(-0.5, 1.0),
    )
    p.wedge(
        x=0,
        y=0,
        radius=0.4,
        start_angle=cumsum("angle", include_zero=True),
        end_angle=cumsum("angle"),
        line_color="white",
        fill_color="color",
        legend_field=legend_col,
        source=df,
    )

    # Add labels to each wedge
    value = df[angle_col].values
    df["cum_angle"] = [
        (sum(value[0 : i + 1]) - (item / 2)) / sum(value) * 2.0 * np.pi
        for i, item in enumerate(value)
    ]
    df["cos"] = np.cos(df["cum_angle"]) * 0.25
    df["sin"] = np.sin(df["cum_angle"]) * 0.5
    source = ColumnDataSource(df)
    labels = LabelSet(
        x="cos",
        y="sin",
        text=label_col,
        source=source,
        text_font_size="10pt",
        text_color="black",
        text_align="center",
    )
    p.add_layout(labels)
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    # Set background
    p.background_fill_color = None
    p.border_fill_color = None

    # # Save svg
    # p.output_backend = "svg"
    # output_file(Path(__file__).parent / f"../frontend/src/assets/{filename}.html")
    # export_svg(
    #     p, filename=Path(__file__).parent / f"../frontend/src/assets/{filename}.svg"
    # )
    return p
