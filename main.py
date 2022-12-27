from PySide2 import QtWidgets, QtGui, QtCore
import json
import pathlib
import sys
from matplotlib import pyplot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg



class BudgetEditorWindow(QtWidgets.QMainWindow):
    def __init__(self, data_path):
        super().__init__()
        self._data_path = data_path
        self._data = set_json_data(data_path)
        self.init_UI()

    def init_UI(self):        
        self.setMinimumSize(1024, 720)
        # Create a calendar widget
        self.calendar = QtWidgets.QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self.on_calendar_selection_changed)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ['Category', 'Expense', 'Allotted', 'Spending'])
        self.set_table_data()

        self.table.itemChanged.connect(self.set_cell_style)
        self.figure, self.axes = pyplot.subplots()

        # Create a FigureCanvasQTAgg object to display the figure
        self.figure_canvas = FigureCanvasQTAgg(self.figure)

        # Create a button to save the table data to the loaded json file.
        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.clicked.connect(self.save_table_data)

        # Create a button to visualize the table data as a graph.
        self.visualize_button = QtWidgets.QPushButton('Visualize graph')
        self.visualize_button.clicked.connect(self.visualize_data)

        self.table.setMinimumSize(450, 200)
        self.calendar.setMinimumSize(450, 200)
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.calendar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.figure_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        mainLayout = QtWidgets.QHBoxLayout() 
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.calendar)
        layout.addWidget(self.table)        
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.visualize_button)
        layout.addLayout(button_layout)

        mainLayout.addLayout(layout)
        mainLayout.addWidget(self.figure_canvas)

        widget = QtWidgets.QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)
        
        # Visualize current month as soon as the app loads.
        self.visualize_button.click()
        set_dark_theme()

    def on_calendar_selection_changed(self):
        # Update the table data when the calendar selection changes
        print(f'month : {self.calendar.selectedDate().toString("MMMM")}')
        self._data = self.get_data_for_month(self.calendar.selectedDate().toString("MMMM"))
        self.set_table_data()

    def get_data_for_month(self, month):
        # Return the data for the specified month from the JSON file
        with open(self._data_path, 'r') as jsonfile:
            data = json.load(jsonfile)
        return [row for row in data if row['Month'] == month]

    def set_cell_style(self, item):
        # Set the cell style based on the values in the "Spending" and "Allotted" columns
        if item.column() == 3:  # Check if the changed item is in the "Spending" column
            # Get the value in the "Allotted" column for the same row
            amount = self.table.item(item.row(), 2)
            if amount:
                # If the value in the "Spending" column is greater than the value in the "Allotted" column,
                # set the cell text color to white and the cell background color to red
                if int(item.text()) > int(amount.text()):
                    item.setForeground(QtGui.QColor('white'))
                    item.setBackground(QtGui.QColor('red'))
                # Otherwise, set the cell text color to black and the cell background color to white
                else:
                    item.setForeground(QtGui.QColor('black'))
                    item.setBackground(QtGui.QColor('white'))

    def save_table_data(self):
        # Read the JSON file and store the data in a list
        with open(self._data_path, 'r') as jsonfile:
            data = json.load(jsonfile)

        # Get the selected month from the calendar widget
        selected_month = self.calendar.selectedDate().toString("MMMM")

        # Remove the existing data for the selected month from the data list
        data = [row for row in data if row['Month'] != selected_month]

        # Add the new data for the selected month to the data list
        for i in range(self.table.rowCount()):
            row = {}
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item:
                    row[self.table.horizontalHeaderItem(j).text()] = item.text()
                else:
                    row[self.table.horizontalHeaderItem(j).text()] = ''
            # Add the selected month to the row data
            row['Month'] = selected_month
            data.append(row)

        # Write the data to the JSON file
        with open(self._data_path, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)

    def set_table_data(self):
        # Get the selected month from the calendar widget
        selected_month = self.calendar.selectedDate().toString('MMMM')

        # Filter the data to only include the selected month
        data = [row for row in self._data if row['Month'] == selected_month]

        row_count = len(data)
        self.table.setRowCount(row_count)
        for i, row in enumerate(data):
            for j, value in enumerate(row.values()):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

    def visualize_data(self):
        # Get the selected month from the calendar widget
        selected_month = self.calendar.selectedDate().toString('MMMM')

        # Filter the data to only include the selected month
        data = [row for row in self._data if row['Month'] == selected_month]

        # Extract the category, expense, and spending data from the JSON data
        categories = [row['Category'] for row in data]
        expenses = [row['Expense'] for row in data]
        amounts = [int(row['Allotted']) for row in data]
        spending = [int(row['Spending']) for row in data]

        # Create a bar chart with the data
        self.axes.clear()
        self.axes.barh(expenses, amounts, color='blue')
        self.axes.barh(expenses, spending, color='red', alpha=0.9)
        self.axes.set_title(f'{selected_month} Budget')
        self.axes.set_xlabel('Allotted')
        self.axes.set_ylabel('Expense')
        self.axes.set_yticks(expenses)
        self.axes.set_yticklabels(expenses)

        # Add labels with the amount value to the middle of each bar
        for x, y in enumerate(amounts):
            self.axes.text(y + 5, x - 0.4, str(y), color='black', fontweight='bold')

        # Add a label in the middle of each bar with the amount value
        for i, bar in enumerate(self.axes.containers[0]):
            height = bar.get_height()
            self.axes.text(bar.get_x() + bar.get_width() / 2, height / 2, str(height), ha='center', va='bottom')

        self.axes.legend()
        
        # Update the graph on the FigureCanvasQTAgg object
        self.figure_canvas.draw()

def set_json_data(data_path):
    with open(data_path, 'r') as jsonfile:
        return json.load(jsonfile)


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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    data_path_parent = pathlib.Path(__file__).parent
    tableEditor = BudgetEditorWindow(data_path=data_path_parent / 'budget.json')
    tableEditor.show()
    sys.exit(app.exec_())
