import json
import sys
import tkinter
import uuid
from dataclasses import dataclass, field
from tkinter import filedialog
from typing import Dict, List, Set

from PySide2 import QtWidgets


@dataclass(frozen=True)
class Transaction:
    amount: float
    category: str
    expense: str
    comment: str
    id: str


class Budget:
    def __init__(self, file_path: str):
        self._data = set_json_data(file_path)
        self.budget_transactions = BudgetTransactions()

        from BudgetUI import BudgetEditorWindow

        budget_editor = BudgetEditorWindow(self)
        budget_editor.show()
        budget_editor.add_new_transaction_signal.connect(self.add_new_transaction)
        budget_editor.del_transaction_signal.connect(self.del_transaction)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def transactions(self):
        return self.budget_transactions.transactions

    def add_new_category(self, month: str, category: str, expense: str, allotted: str, comment: str) -> None:
        month_data = self.data[month]
        expense_data = {expense: {"Allotted": allotted,
                                  "Spending": 0,
                                  "Comment": comment}}
        if category in month_data:
            month_data[category].update(expense_data)
        else:
            month_data[category] = expense_data
        self.data[month] = month_data

    def add_new_transaction(self, *args, **kwargs) -> None:
        self.budget_transactions.add_new_transaction(*args)

    def del_transaction(self, transaction: Dict[str, str]) -> None:
        if transaction is None:
            return
        self.budget_transactions.del_transaction(Transaction(**transaction))


@dataclass
class BudgetTransactions:
    transactions: Set[Transaction] = field(default_factory=set)

    def add_new_transaction(self, category: str, expense: str, amount: float, comment: str) -> None:
        transaction_id = str(uuid.uuid4())
        self.transactions.add(Transaction(amount, category, expense, comment, transaction_id))

    def del_transaction(self, transaction: Transaction) -> None:
        print(f'deleting transaction {transaction}')
        self.transactions.discard(transaction)


def set_json_data(data_path):
    with open(data_path, 'r') as jsonfile:
        return json.load(jsonfile)


if __name__ == '__main__':
    root = tkinter.Tk()
    root.withdraw()
    app = QtWidgets.QApplication(sys.argv)
    bud = Budget(filedialog.askopenfilename(parent=root, title='Select data JSON file', filetypes=[('JSON', '*.json')]))
    sys.exit(app.exec_())
