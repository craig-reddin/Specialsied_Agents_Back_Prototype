# filename: week4_encapsulation.py

class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.__balance = balance

    def deposit(self, amount):
        self.__balance += amount
        return self.__balance

    def withdraw(self, amount):
        if amount > self.__balance:
            return "Insufficient funds"
        else:
            self.__balance -= amount
            return self.__balance

# Create an instance of BankAccount
account = BankAccount("Alice", 100)
print(account.deposit(50))
print(account.withdraw(30))