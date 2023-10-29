from dataclasses import dataclass
from functools import partial

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from PySide2 import QtWidgets, QtGui, QtCore
from matplotlib import pyplot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg


@dataclass
class BudgetData:
    expense: str
    allotted: float
    spending: float
    comment: str


class BudgetEditorWindow(QtWidgets.QMainWindow):
    budget_added = QtCore.Signal(dict)
    budget_removed = QtCore.Signal(dict)
    budget_updated = QtCore.Signal(dict)
    add_new_transaction_signal = QtCore.Signal(str, str, str, str)
    del_transaction_signal = QtCore.Signal(dict)

    def __init__(self, budget):
        super().__init__()

        # User settings.
        settings = QtCore.QSettings("EP", "BudgetApp")
        self.restoreGeometry(settings.value("windowGeometry"))
        self.restoreState(settings.value("windowState"))

        # Initialize UI.
        self.setWindowTitle('No Bullshit Budget')
        self.setMinimumSize(1280, 720)
        # Create a calendar widget
        self.dateEdit = QtWidgets.QDateEdit(self)
        self.dateEdit.setDisplayFormat('MMMM yyyy')
        self.dateEdit.setDate(QtCore.QDate.currentDate())
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.calendarWidget().selectionChanged.connect(self.on_calendar_selection_changed)

        # Create a QTreeWidget
        self.tree = BudgetTreeWidget(self)
        self.tree.setItemDelegate(BudgetItemDelegate(self.tree))
        self.tree.setColumnCount(5)
        self.tree.header().setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.tree.setHeaderLabels(
            ['Category', 'Expense', 'Allotted', 'Spending', 'Comment'])

        # Connect the itemChanged signal to a slot
        # self.tree.itemChanged.connect(self.set_cell_style)
        self.figure, self.axes = pyplot.subplots()

        # Create a FigureCanvasQTAgg object to display the figure
        self.figure_canvas = FigureCanvasQTAgg(self.figure)
        self.figure.set_facecolor("#AAAAAA")

        # Create a button to save the table data to the loaded json file.
        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.clicked.connect(self.save_tree_data)

        # Create a button to visualize the table data as a graph.
        self.visualize_button = QtWidgets.QPushButton('Visualize graph')
        self.visualize_button.clicked.connect(self.visualize_data)

        self.add_transaction_button = QtWidgets.QPushButton('Add transaction')
        self.add_transaction_button.clicked.connect(self.show_add_transaction_popup)

        self.figure_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.category_btn = QtWidgets.QPushButton('Add category')

        main_layout = QtWidgets.QHBoxLayout()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.dateEdit)
        layout.addWidget(self.tree)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.add_transaction_button)
        button_layout.addWidget(self.visualize_button)
        layout.addLayout(button_layout)

        main_layout.addLayout(layout)
        main_layout.addWidget(self.figure_canvas)

        widget = QtWidgets.QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # Visualize current month as soon as the app loads.
        # self.visualize_button.click()
        set_dark_theme()

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

        self.budget = budget

        # Signals for budget logic.
        self.combo_category = None
        self.combo_subcategory = None

        '''
        self.budget_added.connect(self.budget.add_budget)
        self.budget_removed.connect(self.budget.remove_budget)
        self.budget_updated.connect(self.budget.update_budget)
        '''

    def get_data_for_month(self, input_month: str) -> None:
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

        if self.budget.data.get(input_month) is None:
            return None

        for category, category_data in self.budget.data[input_month].items():
            category_item = BudgetCategoryItem(self.tree)

            category_item.setText(0, category)

            for expense, expenseData in category_data.items():
                BudgetItem(category_item,
                           expense,
                           round(float(expenseData["Allotted"]), 2),
                           round(float(expenseData["Spending"]), 2),
                           expenseData["Comment"],
                           )

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

    def save_tree_data(self):
        # Get the selected month from the calendar widget
        selected_month = self.dateEdit.calendarWidget().selectedDate().toString("MMMM")

        '''
        # Iterate over self.tree and add the data to self.budget.data
        for category, subcategories in self.tree.items():
            self.budget.data[selected_month][category] = subcategories
            for subcategory, expenses in subcategories.items():
                self.budget.data[selected_month][category][subcategory] = expenses
                for expense, amount in expenses.items():
                    self.budget.data[selected_month][category][subcategory][expense] = amount
                    self.budget.data[selected_month][category][subcategory][expense]["comment"] = ""
                    self.budget.data[selected_month][category][subcategory][expense]["allotted"] = 0
                    self.budget.data[selected_month][category][subcategory][expense]["spending"] = 0
                    self.budget.data[selected_month][category][subcategory][expense]["expense"] = expense
                    self.budget.data[selected_month][category][subcategory][expense]["category"] = category
                    self.budget.data[selected_month][category][subcategory][expense]["subcategory"] = subcategory
                    self.budget.data[selected_month][category][subcategory][expense]["amount"] = amount
        '''
        result = {}
        # items = self.tree.findItems("", QtCore.Qt.MatchContains) if parent is None else parent.takeChildren()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            for j in range(item.childCount()):
                child = item.child(j)
                for k in range(child.childCount()):
                    grandchild = child.child(k)
                    for l in range(grandchild.childCount()):
                        result[grandchild.text(0)] = {
                            "Allotted": grandchild.text(2),
                            "Spending": grandchild.text(3),
                            "Comment": grandchild.text(4)
                        }

        for item in result:
            text = item.text(0)
            if item.childCount() > 0:
                # result[text] = self.save_tree_data(item)
                pass
            else:
                result[text] = {
                    "Allotted": item.text(2),
                    "Spending": item.text(3),
                    "Comment": item.text(4)
                }
        print(result)
        return result

        '''
        # Write the data to the JSON file
        with open(self._data_path, 'w') as jsonfile:
            json.dump(result, jsonfile, indent=2)
        '''

    def show_add_transaction_popup(self):
        popup = AddTransactionPopup(self, self.budget, self.dateEdit.calendarWidget().selectedDate().toString("MMMM"))

    def visualize_data(self):
        # Get the selected month from the calendar widget
        selectedMonth = self.dateEdit.calendarWidget().selectedDate().toString('MMMM')

        # Filter the data to only include the selected month
        data = self.budget.data.get(selectedMonth)
        if data is None:
            return

        # Extract the category, expense, and spending data from the JSON data
        expenses = []
        amounts = []
        types = []

        for category, subdict in data.items():
            for subcategory, values in subdict.items():
                expenses.append(subcategory)
                amounts.append(float(values['Allotted']))
                types.append('Allotted')
                expenses.append(subcategory)
                amounts.append(float(values['Spending']))
                types.append('Spending')

        # Create a dataframe with the data
        data = pd.DataFrame({'expenses': expenses, 'amounts': amounts, 'types': types})

        # Set the theme of the plot
        sns.set_theme(style="whitegrid", palette="pastel", font_scale=1.2, color_codes=True)

        # Create a bar chart with seaborn
        self.axes.clear()
        ax = sns.barplot(x="amounts", y="expenses", hue="types", data=data, ax=self.axes)
        self.axes.set_title(f'{selectedMonth} Budget')
        self.axes.set_xlabel('Amount')
        self.axes.set_ylabel('Expense')

        # Remove the top and right spines
        sns.despine(offset=10)

        # Adjust the spacing and padding
        plt.tight_layout(pad=1)

        # Add labels and numbers to the barplot
        for container in ax.containers:
            ax.bar_label(container, fmt='%.2f')

        # Update the graph on the FigureCanvasQTAgg object
        self.figure_canvas.draw()


class AddTransactionPopup(QtWidgets.QDialog):
    def __init__(self, parent, budget, month):
        super().__init__(parent)
        self.budget = budget
        self.setWindowTitle("Add transaction")
        self.setMinimumWidth(1000)

        self.month_data = self.budget.data.get(month)
        if self.month_data is None:
            return

        self.combo_category = QtWidgets.QComboBox(self)
        self.combo_category.addItems(self.month_data)
        self.combo_category.addItem("Add new...")
        self.combo_subcategory = QtWidgets.QComboBox(self)

        self.combo_category.currentIndexChanged.connect(self.populate_subcategories)
        self.combo_subcategory.currentIndexChanged.connect(self.add_new_category)
        self.combo_category.setCurrentIndex(1)

        transaction_amount = QtWidgets.QLineEdit(self)
        transaction_amount.setPlaceholderText("Enter amount")

        transaction_comment = QtWidgets.QLineEdit(self)
        transaction_comment.setPlaceholderText("Description...")

        tree_layout = QtWidgets.QVBoxLayout()
        self.transactions_tree = QtWidgets.QTreeWidget()
        self.transactions_tree.setColumnCount(4)
        self.transactions_tree.setHeaderLabels(["category", "Expense", "Spending", "Comment"])
        tree_layout.addWidget(self.transactions_tree)

        add_button = QtWidgets.QPushButton("Add", self)
        add_button.clicked.connect(lambda: self.add_transaction(self.combo_category.currentText(),
                                                                self.combo_subcategory.currentText(),
                                                                transaction_amount.text(),
                                                                transaction_comment.text()))

        delete_button = QtWidgets.QPushButton("Delete selected", self)
        delete_button.clicked.connect(self.delete_transaction)

        main_layout = QtWidgets.QVBoxLayout()
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.combo_category)
        input_layout.addWidget(self.combo_subcategory)
        input_layout.addWidget(transaction_amount)
        input_layout.addWidget(transaction_comment)
        input_layout.addWidget(add_button)
        input_layout.addWidget(delete_button)
        main_layout.addLayout(input_layout)
        main_layout.addLayout(tree_layout)

        self.setLayout(main_layout)
        self.populate_rows()
        self.exec_()

    def add_new_category(self, sender=None):
        sender = self.sender() or sender
        text = sender.currentText()
        if text == "Add new...":
            print(f'add new for {sender}')

    def add_transaction(self, category, expense, amount, comment):
        # Create a new QTreeWidgetItem with the data values
        item = QtWidgets.QTreeWidgetItem([category, expense, str(amount), comment])
        # Add the item to the tree widget
        self.transactions_tree.addTopLevelItem(item)

    def delete_transaction(self):
        transaction_item = self.transactions_tree.currentItem()
        transaction_index = self.transactions_tree.indexOfTopLevelItem(transaction_item)
        data = transaction_item.data(0, QtCore.Qt.UserRole)
        self.transactions_tree.takeTopLevelItem(transaction_index)
        self.parent().del_transaction_signal.emit(data)

    def populate_subcategories(self):
        if self.sender().currentText() == "Add new...":
            self.add_new_category(self.sender())
            return
        subcategories = self.month_data[self.combo_category.currentText()]
        if self.combo_subcategory is not None:
            self.combo_subcategory.clear()
            self.combo_subcategory.addItems(subcategories)
            self.combo_subcategory.addItem("Add new...")

    def populate_rows(self):
        for row, transaction in enumerate(self.budget.transactions):
            item = QtWidgets.QTreeWidgetItem(
                [transaction.category, transaction.expense, str(transaction.amount), transaction.comment])
            data = {"id": transaction.id,
                    "category": transaction.category,
                    "expense": transaction.expense,
                    "amount": transaction.amount,
                    "comment": transaction.comment}
            self.transactions_tree.addTopLevelItem(item)

            item.setData(0, QtCore.Qt.UserRole, data)
            item.setText(0, item.text(0))
            item.setText(1, item.text(1))
            item.setText(2, item.text(2))
            item.setText(3, item.text(3))
            item.setText(3, item.text(4))

    def closeEvent(self, arg__1: QtGui.QCloseEvent) -> None:
        for row in range(self.transactions_tree.topLevelItemCount()):
            category = self.transactions_tree.topLevelItem(row).text(0)
            expense = self.transactions_tree.topLevelItem(row).text(1)
            amount = self.transactions_tree.topLevelItem(row).text(2)
            comment = self.transactions_tree.topLevelItem(row).text(3)
            row_data = self.transactions_tree.topLevelItem(row).data(0, QtCore.Qt.UserRole)
            print(f'rowdata {row_data} - {category} - {expense} - {amount} - {comment}')
            if row_data is None:
                self.parent().add_new_transaction_signal.emit(category, expense, amount, comment)


class BudgetCategoryItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent=None):
        super().__init__(parent)


class BudgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, expense: str, allotted: float, spending: float, comment: str):
        super().__init__(parent)

        self.setData(0, QtCore.Qt.UserRole, BudgetData(expense, allotted, spending, comment))
        self.setText(1, expense)
        self.setText(2, str(allotted))
        self.setText(3, str(spending))
        self.setText(4, comment)

        if spending > allotted:
            # print(f'spending {spending} > allotted {allotted}')
            pass
        else:
            print(f'spending {spending} <= allotted {allotted}')
            print(spending + 1,  allotted + 1)


class BudgetItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent=parent)
        
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        option.backgroundBrush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        option.font.setBold(True)
        option.rect.adjust(2.2, 2.2, -2.2, -2.2)
        item = self.parent().itemFromIndex(index)
        data = item.data(0, QtCore.Qt.UserRole)
        if data is not None:
            if data.spending > data.allotted:
                painter.setPen(QtGui.QPen("red"))
                painter.drawRect(option.rect)
            else:
                painter.setPen(QtGui.QPen("green"))
                painter.drawRect(option.rect)

        super().paint(painter, option, index)


class BudgetTreeWidget(QtWidgets.QTreeWidget):
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
