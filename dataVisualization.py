from matplotlib import pyplot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class VisualizeData:
    def __init__(self, input_data, month_name):
        self._data = input_data
        self._month_name = month_name

        # Create a FigureCanvasQTAgg object to display the figure
        self._figure, self._axes = pyplot.subplots()
        self._figure_canvas = FigureCanvasQTAgg(self._figure)

    @property
    def data(self):
        return self._data

    @property
    def month_name(self):
        return self._month_name

    @property
    def figure(self):
        return self._figure

    @property
    def axes(self):
        return self._axes

    @property
    def figure_canvas(self):
        return self._figure_canvas

    def visualize_data(self):
        # Filter the data to only include the selected month
        data = [row for row in self._data if row['Month'] == self.month_name]

        # Extract the category, expense, and spending data from the JSON data
        categories = [row['Category'] for row in data]
        expenses = [row['Expense'] for row in data]
        amounts = [int(row['Allotted']) for row in data]
        spending = [int(row['Spending']) for row in data]

        # Create a bar chart with the data
        self.axes.clear()
        self.axes.barh(expenses, amounts, color='blue')
        self.axes.barh(expenses, spending, color='red', alpha=0.9)
        self.axes.set_title(f'{self.month_name} Budget')
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

        # Update the graph on the FigureCanvasQTAgg object
        self.figure_canvas.draw()

'''
    # Using seaborn
    def visualize_data(self):
        # Get the selected month from the calendar widget
        selected_month = self.calendar.selectedDate().toString("MMMM")

        # Get the data for the selected month
        data = self.get_data_for_month(selected_month)

        # Create a dictionary to store the total spending for each category
        category_totals = {}

        # Loop through the data and add the spending for each category to the dictionary
        for row in data:
            category = row['Category']
            spending = int(row['Spending'])
            if category in category_totals:
                category_totals[category] += spending
            else:
                category_totals[category] = spending

        # Calculate the total spending for all categories
        total_spending = sum(category_totals.values())

        # Calculate the remaining income (total income - total spending)
        income = 11180
        remaining_income = income - total_spending

        # Add the remaining income to the dictionary
        category_totals['Income'] = remaining_income

        # Create a bar plot using the seaborn library
        seaborn.barplot(x=list(category_totals.keys()), y=list(category_totals.values()))

        # Set the y-axis label
        self.axes.set_ylabel('Amount')

        self.axes.set_title(f'{selected_month} Budget')

        # Set the y-axis limit to be at least 0
        self.axes.set_ylim(bottom=0)

        # Set the graph background color to dark
        self.figure.set_facecolor('#CCCCCC')

        # Redraw the graph
        self.figure_canvas.draw()
    '''