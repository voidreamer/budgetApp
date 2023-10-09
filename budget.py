import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Transaction:
    id: str
    categoryData: Dict[str, str]
    amount: float
    allotted: float
    comment: str


@dataclass
class Budget:
    transactions: List[Transaction] = field(default_factory=list)

    def add_new_transaction(self, categoryData: Dict[str, str], amount: float, allotted: float, comment: str) -> None:
        transaction_id = str(uuid.uuid4())
        transaction = Transaction(transaction_id, categoryData, amount, allotted, comment)
        self.transactions.append(transaction)
