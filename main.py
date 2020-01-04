import numpy as np
import matplotlib.colors as colors
import matplotlib.pyplot as plot

from datetime import datetime
from datetime import date
import csv


### Read input


class Transaction:

    def __init__(self, dict):
        self.date = datetime.strptime(dict.get("Datum"), "%Y%m%d").date()
        self.description = dict.get("Naam / Omschrijving")
        self.accountNumber = dict.get("Rekening")
        self.otherAccountNumber = dict.get("Tegenrekening")
        self.mutationCode = dict.get("Code")
        self.mutationType = dict.get("MutatieSoort")
        self.type = dict.get("Af Bij")
        self.amount = float(dict.get("Bedrag (EUR)").replace(',', '.'))
        self.info = dict.get("Mededelingen")

        self.is_income = self.type == "Bij" 

        self.category = None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<{} - {} - {}>".format(self.date.strftime("%Y%m%d"), self.amount, self.description)


class Category:

    def __init__(self, name, color, rules, priority):
        self.name = name
        self.color = color
        self.rules = rules
        self.priority = priority
        self._transactions = []
  
    def __repr__(self):
        return self.name

    def is_income(self):
        if not self._transactions:
            raise Exception("Unable to determine if category '{}' is income or spending".format(self.name))
        return self._transactions[0].is_income
    
    def collect_transactions(self, transactions):
        for transaction in transactions:
            for rule in self.rules:
                if not rule.matches(transaction):
                    continue
                if transaction.category and transaction.category.priority >= self.priority:
                    raise Exception("Rule '{}' tried to claim transaction: '{}', but was already categorized as '{}'".format(self.name, transaction, transaction.category.name))
                self.add_transaction(transaction)

    def add_transaction(self, transaction):
        if not self._transactions or self.is_income() == transaction.is_income:
            self._transactions.append(transaction)
            transaction.category = self
        else:
            raise Exception("Transaction is_income mismatch! ")
    
    def get_total_for_month(self, month):
        total = 0
        for transaction in self._get_transactions_for_month(month):
            total += transaction.amount
        return total

    def _get_transactions_for_month(self, month):
        return [transaction for transaction in self._transactions if transaction.date.month == month]


class Rule:

    def __init__(self, matches):
        self.matches = matches


categories = [
    # Example
    Category("salary", "green", [
        Rule(lambda x: x.otherAccountNumber == "your employers account number")
    ], 1)

    # Example
    Category("rent", "red", [
        Rule(lambda x: x.otherAccountNumber == "your landlords account number")
    ], 1)
]

transactions = []

with open('transacties_2019.csv') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        transactions.append(Transaction(row))

transactions.reverse()

def get_months(transactions: list):
    result = set()
    for transaction in transactions:
        result.add(transaction.date.month)
    return result

months = get_months(transactions)


### Categorize records


for category in categories:
    category.collect_transactions(transactions)

def sanity_check(transactions):
    uncategorized_transactions = [transaction for transaction in transactions if not transaction.category]
    uncategorize_income = [transaction for transaction in uncategorized_transactions if transaction.is_income]
    uncategorize_spending = [transaction for transaction in uncategorized_transactions if not transaction.is_income]
    if uncategorize_income or uncategorize_spending:
        raise Exception("There are still uncategorized transactions! income: {} - spending {}".format(len(uncategorize_income), len(uncategorize_spending)))

sanity_check(transactions)


### Plot groups


width = 0.4
 
def plot_bar(index, income_totals, bottom, width, color):
    plot.bar(index, income_totals, bottom=bottom, width=width, color=colors.CSS4_COLORS[color])


income_categories = [category for category in categories if category.is_income()]
spending_categories = [category for category in categories if not category.is_income()]

for i, month in enumerate(months):
    bottom = 0
    for category in income_categories:
        index = i-0.2
        total = category.get_total_for_month(month)
        plot_bar(index, total, bottom, width, category.color)
        bottom += total

for i, month in enumerate(months):
    bottom = 0
    for category in spending_categories:
        index = i+0.2
        total = category.get_total_for_month(month)
        plot_bar(index, total, bottom, width, category.color)
        bottom += total

plot.ylabel('Amount')
plot.xlabel('Month')
plot.title('Income vs spending')
plot.xticks(np.arange(len(months)), months)

#TODO: legend

plot.yticks(np.arange(0, 10000, 1000))
for y in np.arange(0, 10000, 500):
    plot.axhline(y=y, color=colors.CSS4_COLORS['gray'], linestyle='dotted', linewidth=0.5)

plot.show()