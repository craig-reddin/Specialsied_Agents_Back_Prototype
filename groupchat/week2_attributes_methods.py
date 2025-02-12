# filename: week2_attributes_methods.py

class Car:
    def __init__(self, make, model, year):
        self.make = make
        self.model = model
        self.year = year

    def description(self):
        return f"{self.year} {self.make} {self.model}"

# Create an instance of Car
my_car = Car("Toyota", "Corolla", 2020)
print(my_car.description())