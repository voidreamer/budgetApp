import json
import sys
import tkinter
import uuid
from dataclasses import dataclass, field
from tkinter import filedialog
from typing import Dict, List

from PySide2 import QtWidgets

from BudgetUI import BudgetEditorWindow


@dataclass
class Transaction:
    allotted: float
    amount: float
    category_data: Dict[str, str]
    comment: str
    id: str


@dataclass
class BudgetTransactions:
    transactions: List[Transaction] = field(default_factory=list)

    def add_new_transaction(self, category_data: Dict[str, str], amount: float, allotted: float, comment: str) -> None:
        transaction_id = str(uuid.uuid4())
        transaction = Transaction(allotted, amount, category_data, comment, transaction_id)
        self.transactions.append(transaction)


class Budget:
    def __init__(self, file_path: str):
        self._data = set_json_data(file_path)
        self.budget_transactions = BudgetTransactions()

        budget_editor = BudgetEditorWindow(self)
        budget_editor.show()
        budget_editor.add_new_transaction_signal.connect(self.add_new_transaction)

    @property
    def data(self):
        return self._data

    @property
    def transactions(self):
        return self.budget_transactions.transactions

    def add_new_transaction(self):
        self.budget_transactions.add_new_transaction()


def set_json_data(data_path):
    with open(data_path, 'r') as jsonfile:
        return json.load(jsonfile)


if __name__ == '__main__':
    root = tkinter.Tk()
    root.withdraw()
    app = QtWidgets.QApplication(sys.argv)
    bud = Budget(filedialog.askopenfilename(parent=root, title='Select a JSON file', filetypes=[('JSON', '*.json')]))
    sys.exit(app.exec_())
