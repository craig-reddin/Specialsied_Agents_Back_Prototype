# filename: week3_inheritance.py

class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "Some sound"

class Cat(Animal):
    def speak(self):
        return "Meow"

# Create instances of Animal and Cat
generic_animal = Animal("Generic")
my_cat = Cat("Whiskers")
print(generic_animal.speak())
print(my_cat.speak())