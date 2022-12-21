from PySide2 import QtWidgets, QtGui, QtCore
import json
import sys

import dataVisualization


class BudgetEditorWindow(QtWidgets.QMainWindow):
    def __init__(self, data_path):
        super().__init__()
        self._data_path = data_path
        self._data = set_json_data(data_path)
        self.init_UI()

    def init_UI(self):
        # Set the window title and size
        self.setWindowTitle('Budget App')
        self.resize(600, 400)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ['Category', 'Expense', 'Amount', 'Actual spending'])
        self.set_table_data()

        self.table.itemChanged.connect(self.set_cell_style)

        # Create a button to save the table data to the loaded json file.
        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.clicked.connect(self.save_table_data)

        # Create a button to visualize the table data as a graph.
        self.visualize_button = QtWidgets.QPushButton('Visualize graph')
        self.visualize_button.clicked.connect(self.visualize_data)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.table)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.visualize_button)
        layout.addLayout(button_layout)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        set_dark_theme()

    @property
    def data(self):
        return self._data

    @property
    def data_path(self):
        return self._data_path

    def set_cell_style(self, item):
        # Set the cell style based on the values in the "Actual spending" and "Amount" columns
        if item.column() == 3:  # Check if the changed item is in the "Actual spending" column
            # Get the value in the "Amount" column for the same row
            amount = self.table.item(item.row(), 2)
            if amount:
                # If the value in the "Actual spending" column is greater than the value in the "Amount" column,
                # set the cell text color to white and the cell background color to red
                if int(item.text()) > int(amount.text()):
                    item.setForeground(QtGui.QColor('white'))
                    item.setBackground(QtGui.QColor('red'))
                # Otherwise, set the cell text color to black and the cell background color to white
                else:
                    item.setForeground(QtGui.QColor('black'))
                    item.setBackground(QtGui.QColor('white'))

    def save_table_data(self):
        # Write the table data to a JSON file
        data = []
        for i in range(self.table.rowCount()):
            row = {}
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item:
                    row[self.table.horizontalHeaderItem(j).text()] = item.text()
                else:
                    row[self.table.horizontalHeaderItem(j).text()] = ''
            data.append(row)
        with open(self.data_path, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)

    def set_table_data(self):
        row_count = len(self.data)
        self.table.setRowCount(row_count)
        for i, row in enumerate(self.data):
            for j, value in enumerate(row.values()):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

    def visualize_data(self):
        dataVisualization.visualize_data(self.data)


# Util functions.
def set_dark_theme():
    # Set the dark theme
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    QtWidgets.QApplication.setPalette(dark_palette)
    QtWidgets.QApplication.setStyle('Fusion')


def set_json_data(data_path):
    with open(data_path, 'r') as jsonfile:
        return json.load(jsonfile)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    tableEditor = BudgetEditorWindow(data_path='budget.json')
    tableEditor.show()
    sys.exit(app.exec_())
