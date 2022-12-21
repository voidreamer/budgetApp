import seaborn
from matplotlib import pyplot


def visualize_data(data):
    # Extract the category, expense, and actual spending data from the JSON data
    categories = [row['Category'] for row in data]
    expenses = [row['Expense'] for row in data]
    amounts = [int(row['Amount']) for row in data]
    actual = [int(row['Actual spending']) for row in data]

    # Create a Seaborn barplot to visualize the data
    seaborn.barplot(x=categories, y=actual, hue=expenses)
    pyplot.show()
