import json
import sys
import tkinter
from functools import partial
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PySide2 import QtWidgets, QtGui, QtCore
from matplotlib import pyplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

import budget


class BudgetTree(QtWidgets.QTreeWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("""
            QTreeWidget{
                border: 0;
                background-color: #222222;
            }
            QTreeWidget::item{
                border: 0;
                background-color: #222222;
                padding: 10px;
                border-radius: 10px;
            }
            QTreeWidget::item:checked{
                border: 2px solid;
                border-color: #C29202;
                background-color: #C29202;
            }
            QTreeWidget::item:selected{
                background-color: #0492C2;
            }
        """)


class BudgetEditorWindow(QtWidgets.QMainWindow):
    budget_added = QtCore.Signal(dict)
    budget_removed = QtCore.Signal(dict)
    budget_updated = QtCore.Signal(dict)

    def __init__(self, data_path):
        super().__init__()
        settings = QtCore.QSettings("EP", "BudgetApp")
        self.restoreGeometry(settings.value("windowGeometry"))
        self.restoreState(settings.value("windowState"))

        self._data_path = data_path
        self._data = set_json_data(data_path)
        self.init_UI()
        self.setStyleSheet("""
            QPushButton{
                border: 0;
                background-color: #222222;
                padding: 15px;
                border-radius: 15px;
            }
            QPushButton::hover{
                border: 2px solid;
                border-color: #0492C2;
            }
            QPushButton::pressed{
                background-color: #0492C2;
            }

        """)

        # Signals for budget logic.
        self.budget = budget.Budget()
        '''
        self.budget_added.connect(self.budget.add_budget)
        self.budget_removed.connect(self.budget.remove_budget)
        self.budget_updated.connect(self.budget.update_budget)
        '''

    def init_UI(self):
        self.setMinimumSize(1280, 720)
        # Create a calendar widget
        self.dateEdit = QtWidgets.QDateEdit(self)
        self.dateEdit.setDisplayFormat('MMMM yyyy')
        self.dateEdit.setDate(QtCore.QDate.currentDate())
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.calendarWidget().selectionChanged.connect(self.on_calendar_selection_changed)

        # Create a QTreeWidget
        self.tree = BudgetTree(self)
        self.tree.setColumnCount(6)
        self.tree.header().setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.tree.setHeaderLabels(
            ['Category', 'Expense', 'Allotted', 'Spending', 'Comment', 'Btn'])

        # Connect the itemChanged signal to a slot
        # self.tree.itemChanged.connect(self.set_cell_style)
        self.figure, self.axes = pyplot.subplots()

        # Create a FigureCanvasQTAgg object to display the figure
        self.figure_canvas = FigureCanvasQTAgg(self.figure)
        self.figure.set_facecolor("#222222")

        # Create a button to save the table data to the loaded json file.
        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.clicked.connect(self.save_table_data)

        # Create a button to visualize the table data as a graph.
        self.visualize_button = QtWidgets.QPushButton('Visualize graph')
        self.visualize_button.clicked.connect(self.visualize_data)

        self.add_transaction_button = QtWidgets.QPushButton('Add transaction')
        self.add_transaction_button.clicked.connect(self.show_add_transaction_popup)

        self.figure_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.category_btn = QtWidgets.QPushButton('Add category')

        mainLayout = QtWidgets.QHBoxLayout()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.dateEdit)
        layout.addWidget(self.tree)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.add_transaction_button)
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

    def get_data_for_month(self, inputMonth: str) -> None:
        ''' Populates the tree widget with data from the json file.

        :Example:

        data = {
        ...     "January": {
        ...         "Category 1": {
        ...             "Expense 1": {
        ...                 "Allotted": 100,
        ...                 "Spending": 50,
        ...                 "Comment": "This is a comment"
        ...             }
        ...         }
        ...     }
        ... }
        '''

        self.tree.clear()

        if self._data.get(inputMonth) is None:
            return None

        for category, category_data in self._data[inputMonth].items():
            category_item = BudgetItem(self.tree)
            category_item.setText(0, category)

            for expense, expenseData in category_data.items():
                expense_item = BudgetItem(category_item)
                expense_item.setText(1, expense)
                expense_item.setText(2, expenseData["Allotted"])
                expense_item.setText(3, f'{float(expenseData["Spending"]):.2f}')
                expense_item.setText(4, expenseData["Comment"])
                if float(expenseData["Spending"]) > float(expenseData["Allotted"]):
                    expense_item.setCheckState(0, QtCore.Qt.Checked)

    def add_row_button_clicked(self):
        # column_count = self.table.columnCount()
        row_count = self.table.rowCount()
        self.table.insertRow(row_count - 1)
        del_row_btn = self.create_delete_row_btn()
        for i in range(0, 5):
            self.table.setItem(row_count - 1, i, QtWidgets.QTableWidgetItem(str("0")))
        self.table.setCellWidget(row_count - 1, 5, del_row_btn)
        del_row_btn.clicked.connect(partial(self.del_row_button_clicked, del_row_btn))

    def add_row_button(self):
        pixmap = QtGui.QPixmap(32, 32)

        # Fill the pixmap with a transparent color
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))

        # Create a QPainter object to draw on the pixmap
        painter = QtGui.QPainter(pixmap)

        # Set the pen and brush to red
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 225, 0)))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 225, 0)))

        # Draw a circle on the pixmap
        painter.drawEllipse(4, 4, 24, 24)

        painter.setPen(QtGui.QPen(QtGui.QColor(225, 225, 225)))
        painter.drawLine(8, 16, 24, 16)
        painter.drawLine(16, 8, 16, 24)
        painter.end()

        # Save the pixmap to an image file
        pixmap.save("icon_green_circle.png")

        row_btn = QtWidgets.QPushButton()

        # Set the icon for the delete button
        row_btn.setIcon(QtGui.QIcon(pixmap))
        row_btn.setIconSize(pixmap.size())
        row_btn.setFixedSize(pixmap.size())

        return row_btn

    def add_transaction(self, transaction_value: str, transaction_comment: str, popup_instance: QtCore.QObject) -> None:
        selected_row = self.table.currentRow()
        try:
            current_value = float(self.table.item(selected_row, 3).text())
        except AttributeError as e:
            popup_instance.accept()
            dialog = QtWidgets.QDialog(self)
            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(QtWidgets.QLabel("Incorrect selection, select a row from the table"))
            dialog.setLayout(layout)
            dialog.exec_()

            return

        category = self.table.item(selected_row, 0).text()
        expense = self.table.item(selected_row, 1).text()
        alloted = self.table.item(selected_row, 2).text()
        spending = self.table.item(selected_row, 3).text()
        comment = self.table.item(selected_row, 4).text()

        new_value = current_value + float(transaction_value)
        self.table.item(selected_row, 3).setText(str(new_value))

        categoryData[category].append(expense)
        self.budget.add_new_transaction(categoryData, float(transaction_value), alloted, transaction_comment)

        # popup_instance.accept()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        settings = QtCore.QSettings("EP", "BudgetApp")
        settings.setValue("windowGeometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def _clear_table_data(self):
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def create_delete_row_btn(self):
        # Create a QPixmap with a size of 32x32 pixels
        pixmap = QtGui.QPixmap(32, 32)

        # Fill the pixmap with a transparent color
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))

        # Create a QPainter object to draw on the pixmap
        painter = QtGui.QPainter(pixmap)

        # Set the pen and brush to red
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0)))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0)))

        # Draw a circle on the pixmap
        painter.drawEllipse(4, 4, 24, 24)

        painter.setPen(QtGui.QPen(QtGui.QColor(225, 225, 225)))
        painter.drawLine(8, 16, 24, 16)

        painter.end()

        # Save the pixmap to an image file
        pixmap.save("icon_red_circle.png")

        # Create a delete button
        delete_button = QtWidgets.QPushButton()

        # Set the icon for the delete button
        delete_button.setIcon(QtGui.QIcon(pixmap))

        # Set the icon size for the delete button
        delete_button.setIconSize(pixmap.size())

        # Set the icon for the button using the style sheet
        # delete_button.setStyleSheet("background-image: url(icon.png)")

        # Set the size of the button to match the size of the icon
        delete_button.setFixedSize(pixmap.size())

        return delete_button

    def delete_add_row_btn(self):
        # Find the widget in the table widget
        found = False
        for row in range(self.table.rowCount()):
            # for col in range(self.table.columnCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QtWidgets.QPushButton):
                # print(f'Widget found at cell ({row}, {col})')
                self.table.removeCellWidget(row, 0)
                found = True
                break
            if found:
                break
        if not found:
            print('Widget not found in the table widget')

    def del_row_button_clicked(self, btn):

        pos = btn.pos()
        index = self.table.indexAt(pos)
        if index.isValid():
            # Get the row and column of the cell
            row = index.row()
            self.table.removeRow(row)
        self.table.clearSelection()

    def on_calendar_selection_changed(self):
        # Update the table data when the calendar selection changes
        print(f'month : {self.dateEdit.calendarWidget().selectedDate().toString("MMMM")}')
        self.get_data_for_month(self.dateEdit.calendarWidget().selectedDate().toString("MMMM"))
        # self.set_table_data()

    def save_table_data(self):
        # Read the JSON file and store the data in a list
        with open(self._data_path, 'r') as jsonfile:
            data = json.load(jsonfile)

        # Get the selected month from the calendar widget
        selected_month = self.dateEdit.calendarWidget().selectedDate().toString("MMMM")

        # Remove the existing data for the selected month from the data list
        data = [row for row in data if row['Month'] != selected_month]

        # Add the new data for the selected month to the data list
        for i in range(self.table.rowCount() - 1):
            row = {}
            for j in range(self.table.columnCount()):
                if self.table.horizontalHeaderItem(j).text() == 'Btn':
                    continue
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

    '''
    def set_cell_style(self, item):
        # Set the cell style based on the values in the "Spending" and "Allotted" columns
        if item.column() == 3:  # Check if the changed item is in the "Spending" column
            # Get the value in the "Allotted" column for the same row
            amount = self.table.item(item.row(), 2)
            if not amount:
                return
            # If the value in the "Spending" column is greater than the value in the "Allotted" column,
            # set the cell text color to white and the cell background color to red
            if float(item.text()) > float(amount.text()):
                item.setForeground(QtGui.QColor('#333333'))
                item.setBackground(QtGui.QColor('red'))
            # Otherwise, set the cell text color to black and the cell background color to white
            else:
                item.setForeground(QtGui.QColor('black'))
                item.setBackground(QtGui.QColor('white'))
    
    def set_table_data(self):
        # elf.delete_add_row_btn()

        # Get the selected month from the calendar widget
        selected_month = self.dateEdit.calendarWidget().selectedDate().toString('MMMM')

        # Filter the data to only include the selected month
        data = [row for row in self._data if row['Month'] == selected_month]

        row_count = len(data)
        self.table.setRowCount(row_count)
        for i, row in enumerate(data):
            for j, value in enumerate(row.values()):
                if value == selected_month:
                    del_row_btn = self.create_delete_row_btn()
                    self.table.setCellWidget(i, j, del_row_btn)
                    del_row_btn.clicked.connect(partial(self.del_row_button_clicked, del_row_btn))
                else:
                    self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

        # here we need to delete all the buttons  dd row buttons
        self.delete_add_row_btn()
        row_count = self.table.rowCount()
        self.table.setRowCount(row_count + 1)
        row_btn = self.add_row_button()
        self.table.setCellWidget(self.table.rowCount() - 1, 0, row_btn)
        row_btn.clicked.connect(self.add_row_button_clicked)
    '''

    def show_add_transaction_popup(self):
        def populateSubcategories(categoryIndex: int):
            subcategories = monthData[combo_category.currentText()]
            combo_subcategory.clear()
            combo_subcategory.addItems(subcategories)

        popup = QtWidgets.QDialog(self)
        popup.setWindowTitle("Add transaction")
        popup.setMinimumWidth(1000)

        combo_category = QtWidgets.QComboBox(popup)
        combo_category.currentIndexChanged.connect(populateSubcategories)
        monthData = self._data.get(self.dateEdit.calendarWidget().selectedDate().toString("MMMM"))
        if monthData is None:
            return
        combo_category.addItems(monthData)
        combo_subcategory = QtWidgets.QComboBox(popup)
        combo_subcategory.addItems(monthData[combo_category.currentText()])

        input_text = QtWidgets.QLineEdit(popup)
        input_text.setPlaceholderText("Enter amount")

        transaction_comment = QtWidgets.QLineEdit(popup)
        transaction_comment.setPlaceholderText("Description...")

        tableLayout = QtWidgets.QVBoxLayout()
        historyTable = QtWidgets.QTableWidget()
        historyTable.setColumnCount(5)
        historyTable.setRowCount(len(self.budget.transactions))
        historyTable.setHorizontalHeaderLabels(["category", "Expense", "Spending", "Alloted", "Comment"])
        tableLayout.addWidget(historyTable)

        add_button = QtWidgets.QPushButton("Add transaction", popup)
        add_button.clicked.connect(lambda: self.add_transaction(input_text.text(), transaction_comment.text(), popup))

        # Add data to the table .
        for row, transaction in enumerate(self.budget.transactions):
            historyTable.setItem(row, 0, QtWidgets.QTableWidgetItem(transaction.category))
            historyTable.setItem(row, 1, QtWidgets.QTableWidgetItem(transaction.expense))
            historyTable.setItem(row, 2, QtWidgets.QTableWidgetItem(str(transaction.amount)))
            historyTable.setItem(row, 3, QtWidgets.QTableWidgetItem(str(transaction.allotted)))
            historyTable.setItem(row, 4, QtWidgets.QTableWidgetItem(transaction.comment))

        main_layout = QtWidgets.QVBoxLayout()
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(combo_category)
        input_layout.addWidget(combo_subcategory)
        input_layout.addWidget(input_text)
        input_layout.addWidget(transaction_comment)
        input_layout.addWidget(add_button)
        main_layout.addLayout(input_layout)
        main_layout.addLayout(tableLayout)

        popup.setLayout(main_layout)
        popup.exec_()

    def visualize_data(self):
        # Get the selected month from the calendar widget
        selectedMonth = self.dateEdit.calendarWidget().selectedDate().toString('MMMM')

        # Filter the data to only include the selected month
        data = self._data.get(selectedMonth)
        if data is None:
            return

        # Extract the category, expense, and spending data from the JSON data
        categories = []
        expenses = []
        amounts = []
        spending = []

        for category, subdict in data.items():
            categories.append(category)
            for subcategory, values in subdict.items():
                expenses.append(subcategory)
                amounts.append(float(values['Allotted']))
                spending.append(float(values['Spending']))
        # Create a bar chart with the data
        self.axes.clear()
        self.axes.set_facecolor('#222222')
        self.axes.barh(expenses, amounts, color='#444444')
        self.axes.barh(expenses, spending, color='#FF3333', alpha=0.9)
        self.axes.set_title(f'{selectedMonth} Budget')
        self.axes.set_xlabel('Allotted')
        self.axes.set_ylabel('Expense')
        self.axes.set_yticks(expenses)
        self.axes.set_yticklabels(expenses)
        self.axes.xaxis.label.set_color('white')
        self.axes.yaxis.label.set_color('white')
        self.axes.title.set_color('white')
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        self.axes.spines['top'].set_color('white')
        self.axes.spines['bottom'].set_color('white')
        self.axes.spines['left'].set_color('white')
        self.axes.spines['right'].set_color('white')

        # Add labels with the amount value to the middle of each bar
        for x, y in enumerate(amounts):
            self.axes.text(y + 5, x - 0.4, str(y), color='#CCCCCC', fontweight='bold')

        plt.legend(['Allotted', 'Spending'])
        plt.tight_layout()

        self.axes.legend()

        # Update the graph on the FigureCanvasQTAgg object
        self.figure_canvas.draw()

    def stacked_bar_chart(self, categories, subcategories, values, width=0.8):
        # Get the number of main categories and subcategories
        n_categories = len(categories)
        n_subcategories = len(subcategories[0])

        # Create an array of positions for the main categories
        category_pos = np.arange(n_categories)

        # Loop over the categories and plot the bars with an offset
        for i in range(n_categories):
            # Get the values for the current category
            category_values = values[i]

            # Calculate the offset and the bar width
            offset = width / 2 - (i + 0.5) * width / n_categories
            bar_width = width / n_categories

            # Initialize an array of bottom positions for each segment
            bottoms = np.zeros(n_subcategories)

            # Loop over the subcategories and plot the segments with different colors
            colors = plt.cm.tab20(np.linspace(0, 1, n_subcategories))
            for j in range(n_subcategories):
                # Get the value for the current segment
                try:
                    segment_value = category_values[j]
                except IndexError:
                    # Do something when the index is out of range
                    segment_value = [0, 0]  # Use a default value

                # Plot the segment with a color and a bottom position
                plt.bar(category_pos[i] + offset, segment_value[0], bar_width / 2,
                        align='center', color=colors[j], bottom=bottoms[j])
                plt.bar(category_pos[i] + offset + bar_width / 2, segment_value[1], bar_width / 2,
                        align='center', color=colors[j], bottom=bottoms[j], alpha=0.9)

                # Update the bottom position for the next segment
                bottoms[j] += segment_value[0]

        # Set the xticks and labels
        plt.xticks(category_pos + width / 4, categories)


class BudgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent=None):
        super().__init__(parent)


class TableWidget(QtWidgets.QTableWidget):
    def __init__(self, *args, **kwargs):
        super(TableWidget, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.drag_start_row = None
        self.setStyleSheet("""
            QTableWidget{
                background-color: #222222;
                padding: 10px;
                font-size: 14px;
                font-family: "Source Sans Pro"
            }
        """)

    # def mouseMoveEvent(self, event):
    #     if event.buttons() == QtCore.Qt.MidButton:
    #         index = self.indexAt(event.pos())
    #         if index.isValid():
    #             self.drag_start_row = index.row()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            if self.indexAt(event.pos()):
                self.drag_start_row = index.row()
                self.selectRow(self.drag_start_row)
        elif event.button() == QtCore.Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item:
                self.editItem(item)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                end_row = index.row()
                self.moveRow(self.drag_start_row, end_row)

    def moveRow(self, start_row, end_row):
        if start_row > end_row:
            start_row = start_row + 1
        else:
            end_row = end_row + 1
        # Insert the row at the new position and place empty treewidgetitems there
        self.insertRow(end_row)
        num_columns = self.columnCount()
        for col in range(num_columns - 1):
            self.setItem(end_row, col, QtWidgets.QTableWidgetItem(str("0")))

        for col in range(num_columns - 1):
            # just swap data to the newly inserted row and
            cur_item = self.takeItem(start_row, col)
            self.setItem(end_row, col, cur_item)

        cellWidget = self.cellWidget(start_row, num_columns - 1)
        if cellWidget:
            cellWidget.setParent(None)
            self.setCellWidget(end_row, num_columns - 1, cellWidget)

        self.removeRow(start_row)


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
    root = tkinter.Tk()
    root.withdraw()
    filePath = filedialog.askopenfilename(parent=root, title='Select a JSON file', filetypes=[('JSON', '*.json')])
    app = QtWidgets.QApplication(sys.argv)
    tableEditor = BudgetEditorWindow(data_path=filePath)
    tableEditor.show()
    sys.exit(app.exec_())
