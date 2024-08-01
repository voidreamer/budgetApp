import configparser
import json
import logging
import sys
import tkinter
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog
from typing import Dict, List, Set

from PySide2 import QtWidgets

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass(frozen=True)
class Transaction:
    amount: float
    category: str
    expense: str
    comment: str
    id: str


class Budget:
    """
    The class is managing the database:
    adding the data if the new expense/category added to the UI
    saves the update to the database
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._data = set_json_data(file_path)
        self.budget_transactions = BudgetTransactions()

        from budgetUI import BudgetEditorWindow

        self.budget_editor = BudgetEditorWindow(self)
        self.budget_editor.show()
        self.budget_editor.add_new_transaction_signal.connect(self.add_new_transaction)
        self.budget_editor.del_transaction_signal.connect(self.del_transaction)
        self.budget_editor.del_row_signal.connect(self.delete_category)

    def add_new_transaction(self, category: str, expense: str, amount: float, comment: str) -> None:
        self.budget_transactions.add_new_transaction(category, expense, amount, comment)
        self.update_spending(category, expense, amount)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def transactions(self):
        return self.budget_transactions.transactions

    def add_new_category(self, year: str, month: str, category: str, expense: str, allotted: str, comment: str) -> None:
        """
        Updates the database when the new expense is added to the UI
        """
        month_data = self.data[year][month]
        expense_data = {expense: {"Allotted": allotted,
                                  "Spending": 0,
                                  "Comment": comment}}
        if category in month_data:
            month_data[category].update(expense_data)
        else:

            month_data[category] = expense_data
        self.data[year][month] = month_data

    def delete_category(self, *args):
        year = args[0]
        month = args[1]
        category = args[2]
        expense = args[3]
        data_expense = self.data.get(year).get(month).get(category).get(expense)
        if data_expense:
            del self.data[year][month][category][expense]
        else:
            del self.data[year][month][category]

    def del_transaction(self, transaction_id: str) -> None:
        transaction = next((t for t in self.transactions if t.id == transaction_id), None)
        if transaction:
            self.budget_transactions.del_transaction(transaction)
            self.update_spending(transaction.category, transaction.expense, -transaction.amount)

    def save(self):
        with open(self.file_path, 'w') as jsonfile:
            json.dump(self._data, jsonfile, indent=4)

    def update_spending(self, category: str, expense: str, amount: float) -> None:
        year = self.budget_editor.dateEdit.date().toString("yyyy")
        month = self.budget_editor.dateEdit.date().toString("MMMM")

        if year not in self._data:
            self._data[year] = {}
        if month not in self._data[year]:
            self._data[year][month] = {}
        if category not in self._data[year][month]:
            self._data[year][month][category] = {}
        if expense not in self._data[year][month][category]:
            self._data[year][month][category][expense] = {"Spending": 0, "Allotted": 0}

        self._data[year][month][category][expense]["Spending"] += amount


@dataclass
class BudgetTransactions:
    transactions: Set[Transaction] = field(default_factory=set)

    def add_new_transaction(self, category: str, expense: str, amount: float, comment: str) -> None:
        transaction_id = str(uuid.uuid4())
        self.transactions.add(Transaction(amount, category, expense, comment, transaction_id))
        logger.info(f'transaction {transaction_id} added')

    def del_transaction(self, transaction: Transaction) -> None:
        logger.info(f'deleting transaction {transaction}')
        self.transactions.discard(transaction)


def set_json_data(data_path):
    with open(data_path, 'r') as jsonfile:
        return json.load(jsonfile)


if __name__ == '__main__':
    config_file = Path(__file__).parent / r"config.ini"
    config = configparser.ConfigParser()
    if not config_file.exists():
        config.add_section('settings')

        config.set('settings', 'last_file', '.')
        with open(config_file, 'w') as configfile:
            config.write(configfile)

    config.read(config_file)
    last_file = Path(config['settings']['last_file'])

    root = tkinter.Tk()
    root.withdraw()
    app = QtWidgets.QApplication(sys.argv)
    file_path = filedialog.askopenfilename(
        parent=root, title='Select data JSON file', initialfile=last_file,
        initialdir=last_file.parent, filetypes=[('JSON', '*.json')])
    last_file = Path(file_path)
    config.set('settings', 'last_file', last_file.as_posix())
    with open(config_file, 'w') as configfile:
        config.write(configfile)

    bud = Budget(file_path)
    sys.exit(app.exec_())
