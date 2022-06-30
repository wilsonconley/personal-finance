import os
import typing as t
from datetime import date

import json
import smartsheet
import smartsheet.models

from plaid.model.location import Location
from plaid.model.payment_meta import PaymentMeta

try:
    from api_keys import get_smartsheet
except ModuleNotFoundError as exc:
    print(
        "\nERROR: rename sample_api_keys.py to api_keys.py and insert your API keys!!\n"
    )
    raise exc

os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_smartsheet()


class SmartsheetManager:
    client: smartsheet.Smartsheet
    sheets: list[smartsheet.models.sheet.Sheet] = []

    def __init__(self) -> None:
        self.client = smartsheet.Smartsheet()

    def get_sheets(self) -> list[smartsheet.models.sheet.Sheet]:
        response = self.client.Sheets.list_sheets(include_all=True)
        self.sheets = response.data
        return self.sheets

    def get_sheet_id(self, name: str) -> int:
        if not self.sheets:
            self.get_sheets()
        for sheet in self.sheets:
            if sheet.name.lower() == name.lower():
                return sheet.id

        sheet_spec = smartsheet.models.Sheet(
            {
                "name": name,
                "columns": [
                    {"title": "Primary Column", "primary": True, "type": "TEXT_NUMBER"}
                ],
            }
        )
        response = self.client.Home.create_sheet(sheet_spec)
        return response.result.id

    def get_col_id(self, sheet_id: int, name: str) -> t.Optional[int]:
        response = self.client.Sheets.get_columns(
            sheet_id,
            include_all=True,
        )
        columns = response.data
        for col in columns:
            if col.title.lower() == name.lower():
                return col.id

    def add_col(self, sheet_id: int, col_name: str) -> int:
        response = self.client.Sheets.get_columns(sheet_id, include_all=True)
        indexes = []
        for col in response.data:
            indexes.append(col.index)
        min_index = 0
        while min_index not in indexes:
            min_index += 1

        # Create the columns
        column = smartsheet.models.Column(
            {
                "title": col_name,
                "type": "TEXT_NUMBER",
                "index": min_index,
            }
        )

        # Add columns to the sheet
        response = self.client.Sheets.add_columns(
            sheet_id,
            [column],
        )
        return response.result[0].id

    def check_row(self, sheet_id: int, value: t.Any, col_id: int) -> t.Optional[int]:
        sheet = self.client.Sheets.get_sheet(sheet_id)
        for row in sheet.rows:
            for cell in row.cells:
                if cell.column_id == col_id:
                    if cell.value == value:
                        return row.id

    def add_rows(
        self, sheet_id: int, data: dict[str, list[t.Any]], check_col: str
    ) -> None:
        new_data = {}
        num_rows = 0
        for col in data:
            col_id = self.get_col_id(sheet_id, col)
            if not col_id:
                col_id = self.add_col(sheet_id, col)
            if col == check_col:
                check_id = col_id
            new_data[col_id] = data[col]
            if num_rows == 0:
                num_rows = len(data[col])
            elif num_rows != len(data[col]):
                raise ValueError("all cols must have same number of data points")

        row_add = []
        row_update = []
        for i in range(0, num_rows):
            row_id = self.check_row(sheet_id, data[check_col][i], check_id)
            row = smartsheet.models.Row()
            for col_id in new_data:
                value = new_data[col_id][i]
                if value is None:
                    value = ""
                elif not issubclass(type(value), (int, float, str)):
                    if issubclass(type(value), date):
                        value = value.strftime("%Y/%m/%d - %H:%M:%S")
                    elif issubclass(type(value), (Location, PaymentMeta)):
                        value = json.dumps(value.to_dict())
                    else:
                        value = json.dumps(value)
                row.cells.append({"column_id": col_id, "value": value})
            if row_id:
                row.id = row_id
                row_update.append(row)
            else:
                row.to_top = True
                row_add.append(row)

        # Add rows to sheet
        if row_add:
            self.client.Sheets.add_rows(sheet_id, row_add)
        if row_update:
            self.client.Sheets.update_rows(sheet_id, row_update)
