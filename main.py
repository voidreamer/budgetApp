from PySide2 import QtWidgets, QtGui, QtCore
import json
import sys

import seaborn as sns
import matplotlib.pyplot as plt


class TableEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create a table widget and set its columns and data
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)  # Set the number of columns to 4
        self.table.setHorizontalHeaderLabels(
            ['Category', 'Expense', 'Amount', 'Actual spending'])  # Set the column labels
        self.setTableData()

        # Connect the itemChanged signal to the setCellStyle method
        self.table.itemChanged.connect(self.setCellStyle)

        # Create a button to save the table data
        self.saveButton = QtWidgets.QPushButton('Save')
        self.saveButton.clicked.connect(self.saveTableData)

        # Create a button to visualize the table data as a graph
        self.visualizeButton = QtWidgets.QPushButton('Visualize graph')
        self.visualizeButton.clicked.connect(self.visualizeData)

        # Create a layout to hold the table, save button, and visualize button
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.table)
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.saveButton)
        buttonLayout.addWidget(self.visualizeButton)
        layout.addLayout(buttonLayout)

        # Create a widget to hold the layout and set it as the central widget
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def setTableData(self):
        # Read the JSON file and set the table data
        with open('Budget2.json', 'r') as jsonfile:
            data = json.load(jsonfile)
            rowCount = len(data)
            self.table.setRowCount(rowCount)
            for i, row in enumerate(data):
                for j, value in enumerate(row.values()):
                    self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

    def setCellStyle(self, item):
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

    def saveTableData(self):
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
        with open('Budget2.json', 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)

    def visualizeData(self):
        # Read the JSON data from the file
        with open('Budget2.json', 'r') as jsonfile:
            data = json.load(jsonfile)

        # Extract the category, expense, and actual spending data from the JSON data
        categories = [row['Category'] for row in data]
        expenses = [row['Expense'] for row in data]
        amounts = [int(row['Amount']) for row in data]
        actual = [int(row['Actual spending']) for row in data]

        # Create a Seaborn barplot to visualize the data
        sns.barplot(x=categories, y=actual, hue=expenses)
        plt.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    tableEditor = TableEditor()
    tableEditor.show()
    sys.exit(app.exec_())
