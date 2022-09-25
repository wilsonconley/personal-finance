import typing as t
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bokeh.io import export_svg
from bokeh.models import ColumnDataSource, DataTable, LabelSet, TableColumn
from bokeh.palettes import Category20c
from bokeh.plotting import figure, output_file, save, show, Figure
from bokeh.transform import cumsum


def pie_chart_balances(balances_df: pd.DataFrame) -> Figure:
    balances_df["legend"] = [
        f"{name} ({id[0:4]})"
        for id, name in zip(balances_df["account_id"], balances_df["name"])
    ]
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


def pie_chart_transactions_out(
    transaction_df: pd.DataFrame, categories: list[str]
) -> Figure:
    # Transactions Out
    transaction_dict = {"category": [], "total": []}
    for category in categories:
        selector = [
            x["primary"] == category
            for x in transaction_df["personal_finance_category"]
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
            x["primary"] == category
            for x in transaction_df["personal_finance_category"]
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
