import json

'''
# Load the existing data
with open('budget.json', 'r') as f:
    existing_data = json.load(f)

# Initialize an empty dictionary to hold the refactored data
refactored_data = {}

# Iterate over the existing data
for item in existing_data:
    category = item['Category']
    expense = item['Expense']

    # If the category is not in the refactored data, add it
    if category not in refactored_data:
        refactored_data[category] = []

    # Remove the 'Category' field from the item
    del item['Category']

    # Add the item to the category's list of expenses
    refactored_data[category].append(item)

# Convert the refactored data to a list of dictionaries
refactored_data = [{'Category': k, 'Expenses': v} for k, v in refactored_data.items()]

# Save the refactored data
with open('refactored_data.json', 'w') as f:
    json.dump(refactored_data, f, indent=4)
'''

'''
# Assuming the original json data is stored in a variable called data
import json

# Create a new dictionary to store the refactored data
new_data = {}

# Load the existing data
with open('refactored_data.json', 'r') as f:
    data = json.load(f)

data = data[0]

# Copy the category name from the original data
new_data["Category"] = data["Category"]

# Create a nested dictionary to store the months and expenses
new_data["Months"] = {}

# Loop through the expenses in the original data
for expense in data["Expenses"]:
    # Get the month name from the expense
    month = expense["Month"]

    # Check if the month is already in the new data
    if month not in new_data["Months"]:
        # If not, create a new dictionary for the month
        new_data["Months"][month] = {}
        # Create an empty list to store the expenses for the month
        new_data["Months"][month]["Expenses"] = []

    # Remove the month key from the expense
    expense.pop("Month")

    # Append the expense to the list of expenses for the month
    new_data["Months"][month]["Expenses"].append(expense)

# Save the refactored data
with open('refactored_data2.json', 'w') as f:
    json.dump(new_data, f, indent=4)


# Convert the new data to a json string
new_json = json.dumps(new_data, indent=4)

# Print the new json string
print(new_json)
'''
'''
outputObj = {}

# Load the existing data
with open('refactored_data.json', 'r') as f:
    inputObj = json.load(f)

for category in inputObj:
    for expense in category['Expenses']:
        month = expense['Month']
        if month not in outputObj:
            outputObj[month] = []
        expenseCopy = expense.copy()
        expenseCopy["Category"] = category["Category"]
        expenseCopy.pop("Month")
        outputObj[month].append(expenseCopy)

# Save the refactored data
with open('refactored_data3.json', 'w') as f:
    json.dump(outputObj, f, indent=4)
    
'''

'''
# Load the existing data
with open('budget.json', 'r') as f:
    inputObj = json.load(f)

outputObj = {}

for month, expenses in inputObj.items():
    if month not in outputObj:
        outputObj[month] = {}

    for expense in expenses:
        category = expense['Category']
        expenseName = expense['Expense']
        if category not in outputObj[month]:
            outputObj[month][category] = {}
        expenseCopy = expense.copy()
        expenseCopy.pop("Category")
        expenseCopy.pop("Expense")
        outputObj[month][category][expenseName] = expenseCopy

# Save the refactored data
with open('refactored_data3.json', 'w') as f:
    json.dump(outputObj, f, indent=4)
'''
# Load the existing data
with open('budget.json', 'r') as f:
    inputObj = json.load(f)

outputObj = {}

for expense in inputObj:
    month = expense['Month']
    category = expense['Category']
    expenseName = expense['Expense']
    if month not in outputObj:
        outputObj[month] = {}
    if category not in outputObj[month]:
        outputObj[month][category] = {}

    expenseCopy = expense.copy()
    expenseCopy.pop("Month")
    expenseCopy.pop("Category")
    expenseCopy.pop("Expense")

    outputObj[month][category][expenseName] = expenseCopy

# Save the refactored data
with open('refactored_data3.json', 'w') as f:
    json.dump(outputObj, f, indent=4)
