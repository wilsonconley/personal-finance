import typing as t
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bokeh.io import export_svg
from bokeh.models import ColumnDataSource, DataTable, LabelSet, TableColumn
from bokeh.palettes import Category20c
from bokeh.plotting import figure, output_file, save, show
from bokeh.transform import cumsum


def pie_chart_bokeh(data):
    p_data = pd.DataFrame(data)
    p_data["angle"] = p_data["balances"] / p_data["balances"].sum() * 2 * np.pi
    num_account = len(p_data["balances"])
    if num_account < min(Category20c.keys()):
        p_data["color"] = Category20c[min(Category20c.keys())][0:num_account]
    elif num_account > max(Category20c.keys()):
        p_data["color"] = (
            Category20c[max(Category20c.keys())]
            * int(np.ceil(num_account / max(Category20c.keys())))
        )[0:num_account]
    else:
        p_data["color"] = Category20c[num_account]
    p_data["labels"] = [f"${x:.2f}" for x in p_data["balances"]]
    p_data["legend"] = [
        f"{name} ({id[0:4]})" for id, name in zip(p_data["account_id"], p_data["name"])
    ]

    p = figure(
        height=350,
        # title="Account Balances Overview",
        toolbar_location=None,
        tools="hover",
        tooltips="@name: @labels",
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
        legend_field="legend",
        source=p_data,
    )

    value = p_data["balances"].values
    p_data["cum_angle"] = [
        (sum(value[0 : i + 1]) - (item / 2)) / sum(value) * 2.0 * np.pi
        for i, item in enumerate(value)
    ]
    p_data["cos"] = np.cos(p_data["cum_angle"]) * 0.25
    p_data["sin"] = np.sin(p_data["cum_angle"]) * 0.5
    source = ColumnDataSource(p_data)
    labels = LabelSet(
        x="cos",
        y="sin",
        text="labels",
        source=source,
        text_font_size="10pt",
        text_color="black",
        text_align="center",
    )
    p.add_layout(labels)

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    p.output_backend = "svg"
    p.background_fill_color = None
    p.border_fill_color = None

    # show(p)
    output_file(Path(__file__).parent / "../frontend/src/assets/balances.html")
    # save(p, title="Balances Overview")
    export_svg(
        p, filename=Path(__file__).parent / "../frontend/src/assets/balances.svg"
    )


def pie_chart_matplotlib(data):
    # Get plot data
    p_data = pd.DataFrame(data)
    balances = p_data["balances"]
    names = p_data["name"]
    num_account = len(balances)
    if num_account < min(Category20c.keys()):
        colors = Category20c[min(Category20c.keys())][0:num_account]
    elif num_account > max(Category20c.keys()):
        colors = (
            Category20c[max(Category20c.keys())]
            * int(np.ceil(num_account / max(Category20c.keys())))
        )[0:num_account]
    else:
        colors = Category20c[num_account]

    # Wedge properties
    # wp = {"linewidth": 1, "edgecolor": "black"}

    # Creating autocpt arguments
    def format_autopct(pct, allvalues):
        absolute = int(pct / 100.0 * np.sum(allvalues))
        return "${:.2f}".format(absolute)

    # Creating plot
    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(
        balances,
        autopct=lambda pct: format_autopct(pct, balances),
        labels=names,
        # shadow=True,
        colors=colors,
        startangle=90,
    )

    # Adding legend
    ax.legend(
        wedges,
        names,
        title="Accounts",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
    )

    plt.setp(autotexts, size=8, weight="bold")
    ax.set_title("Account Balances Overview")

    # show plot
    # plt.show()
    plt.savefig(
        (Path(__file__).parent / "../frontend/src/assets/balances.svg").resolve()
    )


def table_bokeh(data):
    df = pd.DataFrame(data)
    source = ColumnDataSource(df)

    columns = [
        TableColumn(field="name", title="Name"),
        TableColumn(field="balances", title="Balance"),
    ]

    myTable = DataTable(source=source, columns=columns)
    output_file(Path(__file__).parent / "../frontend/src/assets/balances_table.html")
    # save(myTable, title="Balances Table Overview")
    export_svg(
        myTable,
        filename=Path(__file__).parent / "../frontend/src/assets/balances_table.svg",
    )
