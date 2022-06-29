import os
import typing as t

import smartsheet
import smartsheet.models

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
            if sheet.name == name:
                return sheet.id
        raise ValueError(f"sheet {name} not found")

    def get_col_id(self, sheet_id: int, name: str) -> int:
        response = self.client.Sheets.get_columns(
            sheet_id,
            include_all=True,
        )
        columns = response.data
        for col in columns:
            if col.title == name:
                return col.id

    def add_rows(self, sheet_id: int, data: dict[str, list[t.Any]]) -> None:
        new_data = {}
        num_rows = 0
        for col in data:
            new_data[self.get_col_id(sheet_id, col)] = data[col]
            if num_rows == 0:
                num_rows = len(data[col])
            elif num_rows != len(data[col]):
                raise ValueError("all cols must have same number of data points")

        row_list = []
        for i in range(0, num_rows):
            row = smartsheet.models.Row()
            row.to_top = True
            for col_id in new_data:
                row.cells.append({"column_id": col_id, "value": new_data[col_id][i]})
            row_list.append(row)

        # Add rows to sheet
        response = self.client.Sheets.add_rows(sheet_id, row_list)
