from dataclasses import dataclass
from functools import partial
from pprint import pprint

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
    """
    This class is for managing general aspects of the UI window of a
    budget app(not the tree widget and it's items)
    """
    budget_added = QtCore.Signal(dict)
    budget_removed = QtCore.Signal(dict)
    budget_updated = QtCore.Signal(dict)
    add_new_transaction_signal = QtCore.Signal(str, str, str, str)
    del_transaction_signal = QtCore.Signal(dict)
    del_row_signal = QtCore.Signal(str, str, str, str)

    def __init__(self, budget):
        super().__init__()

        # User settings.
        settings = QtCore.QSettings("EP", "BudgetApp")
        self.restoreGeometry(settings.value("windowGeometry"))
        self.restoreState(settings.value("windowState"))

        # Initialize UI.
        self.setWindowTitle('Budget Test')
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

        self.add_delete_button = QtWidgets.QPushButton('Delete')
        self.add_delete_button.clicked.connect(self.delete_row)

        self.figure_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.category_btn = QtWidgets.QPushButton('Add category')

        main_layout = QtWidgets.QHBoxLayout()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.dateEdit)
        layout.addWidget(self.tree)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.add_transaction_button)
        button_layout.addWidget(self.add_delete_button)
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

        self.add_new_transaction_signal.connect(self.tree_update_spending)
        '''
        self.budget_added.connect(self.budget.add_budget)
        self.budget_removed.connect(self.budget.remove_budget)
        self.budget_updated.connect(self.budget.update_budget)
        '''

    def get_data_for_date(self, input_year: str, input_month: str) -> None:
        ''' Populates the tree widget with data from the json file.

        :Example:

        data = {"2023": {
        ...         "January": {
        ...             "Category 1": {
        ...                 "Expense 1": {
        ...                     "Allotted": 100,
        ...                     "Spending": 50,
        ...                     "Comment": "This is a comment"
        ...                 }
        ...             }
        ...         }
        ...     }
        ...}
        '''

        self.tree.clear()

        if self.budget.data.get(input_year) is None:
            return None
        if self.budget.data.get(input_year).get(input_month) is None:
            return None

        for category, category_data in self.budget.data[input_year][input_month].items():
            category_item = BudgetCategoryItem(self.tree)
            category_item.setText(0, category)
            for expense, expenseData in category_data.items():
                BudgetItem(category_item,
                           expense,
                           round(float(expenseData["Allotted"]), 2),
                           round(float(expenseData["Spending"]), 2),
                           expenseData["Comment"],
                           )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        settings = QtCore.QSettings("EP", "BudgetApp")
        settings.setValue("windowGeometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def on_calendar_selection_changed(self):
        # Update the table data when the calendar selection changes
        print(f'month : {self.dateEdit.calendarWidget().selectedDate().toString("yyyy")}')
        print(f'month : {self.dateEdit.calendarWidget().selectedDate().toString("MMMM")}')
        self.get_data_for_date(self.dateEdit.calendarWidget().selectedDate().toString("yyyy"),
                               self.dateEdit.calendarWidget().selectedDate().toString("MMMM"))
        # self.set_table_data()

    def save_tree_data(self):
        # Get the selected month from the calendar widget
        selected_year = self.dateEdit.calendarWidget().selectedDate().toString("yyyy")
        selected_month = self.dateEdit.calendarWidget().selectedDate().toString("MMMM")

        # Iterate over the tree and save the data
        try:
            selected_month_data = self.budget.data[selected_year][selected_month]
        except KeyError as e:
            print("Nothing to save")
        # items = self.tree.findItems("", QtCore.Qt.MatchContains) if parent is None else parent.takeChildren()
        for i in range(self.tree.topLevelItemCount()):
            category_item = self.tree.topLevelItem(i)
            for j in range(category_item.childCount()):
                category_name = category_item.text(0)
                expense_item = category_item.child(j)
                expense = expense_item.text(1)
                allotted = expense_item.text(2)
                spending = expense_item.text(3)
                comment = expense_item.text(4)
                category_update = {
                    expense: {
                        "Allotted": allotted,
                        "Spending": spending,
                        "Comment": comment
                    }
                }
                if category_name in selected_month_data:
                    selected_month_data[category_name].update(category_update)
                else:
                    selected_month_data[category_name] = category_update

        self.budget.data[selected_year][selected_month] = selected_month_data
        self.budget.save()

    def show_add_transaction_popup(self):
        popup = AddTransactionPopup(self, self.budget, self.dateEdit.calendarWidget().selectedDate().toString("yyyy"),
                                    self.dateEdit.calendarWidget().selectedDate().toString("MMMM"))

    def visualize_data(self):
        # Get the selected month from the calendar widget
        selectedYear = self.dateEdit.calendarWidget().selectedDate().toString('yyyy')
        selectedMonth = self.dateEdit.calendarWidget().selectedDate().toString('MMMM')

        # Filter the data to only include the selected month
        data = self.budget.data.get(selectedYear).get(selectedMonth)
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

    def tree_update_spending(self, *args):
        self.tree.update_expense_spending(*args)

    def delete_row(self):
        selected_year = self.dateEdit.calendarWidget().selectedDate().toString("yyyy")
        selected_month = self.dateEdit.calendarWidget().selectedDate().toString("MMMM")
        self.tree.remove_currently_selected(selected_year, selected_month)


class AddTransactionPopup(QtWidgets.QDialog):
    category_popup_closed = QtCore.Signal(str, str)

    def __init__(self, parent, budget, year, month):
        super().__init__(parent)
        self.budget = budget
        self.year = year
        self.month = month
        self.setWindowTitle("Add transaction")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(200)

        try:
            self.year_data = self.budget.data[year]
        except KeyError:
            self.budget.data[year] = {}
            self.year_data = self.budget.data[year]

        try:
            self.month_data = self.budget.data[year][month]
        except KeyError:
            self.budget.data[year][month] = {}
            self.month_data = self.budget.data[year][month]

        self.combo_category = QtWidgets.QComboBox(self)
        self.combo_category.addItems(self.month_data)
        self.combo_category.addItem("Add/Edit...")
        self.combo_subcategory = QtWidgets.QComboBox(self)
        self.combo_subcategory.setObjectName('combo_expense')

        # activated signal triggers even when press the same item
        # this is needed when the only option is "Add/Edit..."
        self.combo_category.activated.connect(self.populate_subcategories)
        # self.combo_category.activated.connect(self.check_if_works)
        self.combo_subcategory.activated.connect(self.add_new_category)
        self.combo_category.setCurrentIndex(1)
        self.category_popup_closed.connect(self.select_new_categories)

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
        if text == "Add/Edit...":
            AddNewCategoryPopup(self)
            # TODO: after adding new category need to set the combobox

    def select_new_categories(self, *args):
        category = args[0]
        self.combo_category.addItem(category)
        expense = args[1]
        self.combo_subcategory.addItem(expense)
        index_cat = self.combo_category.findText(category, QtCore.Qt.MatchFlag.MatchExactly)
        index_exp = self.combo_subcategory.findText(expense, QtCore.Qt.MatchFlag.MatchExactly)
        self.combo_category.setCurrentIndex(index_cat)
        self.combo_subcategory.setCurrentIndex(index_exp)

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
        if self.sender().currentText() == "Add/Edit...":
            self.add_new_category(self.sender())
        subcategories = self.month_data.get(self.combo_category.currentText())
        if self.combo_subcategory and subcategories:
            self.combo_subcategory.clear()
            self.combo_subcategory.addItems(subcategories)

        index = self.combo_subcategory.findText("Add/Edit...")
        if index == -1:
            self.combo_subcategory.insertItem(0, "Add/Edit...")

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
            if row_data is None:
                # TODO put this on logic module instead.
                current_spending = float(self.month_data[category][expense]["Spending"])
                updated_spending = current_spending + float(amount)
                self.month_data[category][expense].update({"Spending": updated_spending})
                self.populate_rows()
                self.parent().add_new_transaction_signal.emit(category, expense, str(updated_spending), comment)


class AddNewCategoryPopup(QtWidgets.QDialog):
    def __init__(self, parent, category: str = None):
        super().__init__(parent)
        self.budget = parent.budget
        self.setWindowTitle("Add new category")
        self.setMinimumWidth(1000)

        self.category_name_line_edit = QtWidgets.QLineEdit(self)
        self.category_name_line_edit.setPlaceholderText("Enter category name...")
        self.category_name_line_edit.setText(category if category != 'Add new...' else None)

        self.expense_name_line_edit = QtWidgets.QLineEdit(self)
        self.expense_name_line_edit.setPlaceholderText("Enter expense name...")

        self.allotted_amount_line_edit = QtWidgets.QLineEdit(self)
        self.allotted_amount_line_edit.setPlaceholderText("Enter allotted amount...")

        self.timer = QtCore.QTimer(self)
        self.timer2 = QtCore.QTimer(self)

        self.comment_line_edit = QtWidgets.QLineEdit(self)
        self.comment_line_edit.setPlaceholderText("Enter comment...")

        add_button = QtWidgets.QPushButton("Add", self)
        add_button.clicked.connect(
            lambda: self.add_new_category(self.category_name_line_edit.text(),
                                          self.expense_name_line_edit.text(),
                                          self.allotted_amount_line_edit.text(),
                                          self.comment_line_edit.text()))

        main_layout = QtWidgets.QVBoxLayout()
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.category_name_line_edit)
        input_layout.addWidget(self.expense_name_line_edit)
        input_layout.addWidget(self.allotted_amount_line_edit)
        input_layout.addWidget(self.comment_line_edit)
        input_layout.addWidget(add_button)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)
        self.exec_()
        self.close()
        self.destroy()
        self.deleteLater()

    def add_new_category(self, category, expense, allotted, comment):
        # This block of code checks that we are not adding "empty"
        # expense/category/allotted amount
        style = self.category_name_line_edit.styleSheet()
        if not category:
            self.category_name_line_edit.setStyleSheet(StyleManager.red_frame_style)
            self.timer.singleShot(1000, lambda: self.back_to_style(self.category_name_line_edit,
                                                                   style, category))
            return
        if not expense:
            self.expense_name_line_edit.setStyleSheet(StyleManager.red_frame_style)
            self.timer.singleShot(1000, lambda: self.back_to_style(self.expense_name_line_edit,
                                                                   style, expense))
            return
        if not allotted:
            self.allotted_amount_line_edit.setStyleSheet(StyleManager.red_frame_style)
            self.timer.singleShot(1000, lambda: self.back_to_style(self.allotted_amount_line_edit,
                                                                   style, allotted))
            return
        try:
            float(allotted)
        except ValueError:
            self.allotted_amount_line_edit.setStyleSheet(StyleManager.red_frame_style)
            self.timer.singleShot(1000, lambda: self.back_to_style(self.allotted_amount_line_edit,
                                                                   style, allotted))
            return

        # This part of the code checks if we already have the category created
        # if we don't it will create a new
        tree: QtWidgets.QTreeWidget = self.parent().parent().tree

        category_item = tree.find_category_item(category)
        if category_item is None:
            category_item = BudgetCategoryItem(tree)
            category_item.setText(0, category)

        if comment is None:
            comment = ""

        # This part of the code checks if such expense item already exists
        # if it does not it creates the expense if it does it updates
        # allotted and comment
        expense_item = tree.find_expense_item(category, expense)
        if expense_item:
            original_text = self.expense_name_line_edit.text()
            style_expense = StyleManager.get_temp_text_style("Exists")
            self.expense_name_line_edit.setStyleSheet(style_expense)
            self.timer.singleShot(800, lambda: self.back_to_style(self.expense_name_line_edit,
                                                                  style, original_text))
            style_allotted = StyleManager.get_temp_text_style("Updated")
            self.allotted_amount_line_edit.setStyleSheet(style_allotted)
            self.timer.singleShot(800, lambda: self.back_to_style(self.allotted_amount_line_edit,
                                                                  style, allotted))
            self.comment_line_edit.setStyleSheet(style_allotted)
            expense_item.setText(2, allotted)
            self.timer.singleShot(800, lambda: self.back_to_style(self.comment_line_edit,
                                                                  style, comment))
            expense_item.setText(4, comment)
            return
        else:
            expense_item = BudgetItem(category_item, expense, float(allotted), 0.0, comment)
            self.budget.add_new_category(self.parent().year, self.parent().month,
                                         category, expense, float(allotted), comment)
            tree.expandItem(category_item)
            self.parent().category_popup_closed.emit(category, expense)
            self.close()

    @staticmethod
    def back_to_style(widget: QtWidgets.QLineEdit, style: str, text: str) -> None:
        widget.setStyleSheet(style)
        widget.setText(text)

    # def closeEvent(self, event: QtGui.QCloseEvent) -> None:
    #     print("close event")
    #     category = self.category_name_line_edit.text()
    #     expense = self.expense_name_line_edit.text()
    #     self.parent().category_popup_closed.emit(category, expense)


class BudgetCategoryItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent=None):
        super().__init__(parent)


class BudgetItem(QtWidgets.QTreeWidgetItem):
    """
    Class to the set QTreeWidgetItem object for the new expense added by user
    """

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
            print(spending + 1, allotted + 1)


class BudgetItemDelegate(QtWidgets.QStyledItemDelegate):
    """
    The class paint expense in red if the expense exceeds allotted
    """

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
    """
    Class manages QTreeWidget and it's items of the YU
    """

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

    def find_category_item(self, category: str) -> QtWidgets.QTreeWidgetItem:
        category_item = None
        for i in range(self.topLevelItemCount()):
            if self.topLevelItem(i).text(0) == category:
                category_item = self.topLevelItem(i)
                break
        return category_item

    def find_expense_item(self, category: str, expense: str) -> QtWidgets.QTreeWidgetItem:
        category_item = self.find_category_item(category)
        if not category_item:
            return None
        expense_item = None
        for i in range(0, category_item.childCount()):
            if category_item.child(i).text(1) == expense:
                expense_item = category_item.child(i)
        return expense_item

    def remove_currently_selected(self, year, month):
        """
        Removes currently selected
        """
        current_item = self.currentItem()
        if current_item:
            parent_item = current_item.parent()
            if parent_item:
                index = parent_item.indexOfChild(current_item)
                category = parent_item.text(0)
                removed_item = parent_item.takeChild(index)
                self.parent.del_row_signal.emit(year,
                                                month,
                                                category,
                                                removed_item.text(1))
                del removed_item
            else:
                # It's a top-level item
                index = self.indexOfTopLevelItem(current_item)
                removed_item = self.takeTopLevelItem(index)
                self.parent.del_row_signal.emit(year,
                                                month,
                                                removed_item.text(0),
                                                None)
                del removed_item

    def update_expense_spending(self, *args):
        """
        *args passed to this method(slot) by the add_new_transaction_signal
        Signal of the parent BudgetEditorWindow:
            category: str
            expense: str
            amount: float/str
            comment: str
        """
        item = self.find_expense_item(args[0], args[1])
        item.setText(3, args[2])


class StyleManager:
    default_style = ""
    red_frame_style = """
            QLineEdit {
                border: 2px solid red;
                border-radius: 4px;
                padding: 2px;
            }
        """

    @staticmethod
    def get_temp_text_style(message: str) -> str:
        temp_text_style = """
            QLineEdit {{
                color: red;
                qproperty-text: "{}"; 
                text-align: right; 
                }}
            """.format(message)
        return temp_text_style


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
