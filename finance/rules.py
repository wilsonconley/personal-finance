import os
from pathlib import Path

import pandas as pd


class Rules:

    rule_columns: list[str] = ["search_str", "transaction_field", "categorize"]
    filename = Path(__file__).parent / ".rules.csv"
    rules: pd.DataFrame

    def __init__(self) -> None:
        if os.path.exists(self.filename):
            self.rules = pd.read_csv(self.filename)
        else:
            self.rules = pd.DataFrame({k: [] for k in self.rule_columns})
            self.save_rules()

    def save_rules(self) -> None:
        self.rules.to_csv(self.filename, index=False)

    def add_rule(
        self, search_str: str, transaction_field: str, categorize: str
    ) -> None:
        # Example:
        #   self.add_rule("'HOME TELE' in transaction['name']", "Utilities")
        if (
            (self.rules["search_str"] == search_str)
            & (self.rules["transaction_field"] == transaction_field)
            & (self.rules["categorize"] == categorize)
        ).any():
            # Rule already in ruleset
            return

        self.rules = pd.concat(
            [
                self.rules,
                pd.DataFrame(
                    {
                        "search_str": search_str,
                        "transaction_field": transaction_field,
                        "categorize": categorize,
                    },
                    index=[0],
                ),
            ],
            ignore_index=True,
        )
        self.save_rules()

    def remove_rule(self, index: int) -> None:
        self.rules.drop(index, inplace=True)
        self.rules.index = range(len(self.rules))
        self.save_rules()
