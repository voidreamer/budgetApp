import uuid
from dataclasses import dataclass, field
from typing import List, Dict

from PySide2 import QtWidgets, QtGui, QtCore
import json
import pathlib
import sys
from matplotlib import pyplot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from functools import partial

# TODO separate logic from UI in two modules.


@dataclass
class Transaction:
    id: str
    categoryData: Dict[str, str]
    amount: float
    allotted: float
    comment: str


@dataclass
class Budget:
    transactions: List[Transaction] = field(default_factory=list)

    def add_new_transaction(self, categoryData: Dict[str, str], amount: float, allotted: float, comment: str) -> None:
        transaction_id = str(uuid.uuid4())
        transaction = Transaction(transaction_id, categoryData, amount, allotted, comment)
        self.transactions.append(transaction)


def set_json_data(data_path):
    with open(data_path, 'r') as jsonfile:
        return json.load(jsonfile)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    data_path_parent = pathlib.Path(__file__).parent
    tableEditor = BudgetEditorWindow(data_path=data_path_parent / 'refactored_data2.json')
    tableEditor.show()
    sys.exit(app.exec_())
