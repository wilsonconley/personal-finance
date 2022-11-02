import os
from pathlib import Path

import pandas as pd

from finance.plaid_manager import PlaidManager


class Budget:

    categories: list[str] = PlaidManager.categories
    budget: dict[str, float]
    filename = Path(__file__).parent / ".budget.csv"

    def __init__(self) -> None:
        if os.path.exists(self.filename):
            self.budget = pd.read_csv(self.filename).to_dict(orient="records")[0]
        else:
            self.budget = {}
            for x in self.categories:
                self.budget[x] = 0
            self.save_budget()

    def save_budget(self) -> None:
        pd.DataFrame(self.budget, index=[0]).to_csv(self.filename, index=False)

    def set_category(self, category: str, value: float) -> None:
        self.budget[category] = value

    def get_category(self, category: str) -> float:
        return self.budget[category]
