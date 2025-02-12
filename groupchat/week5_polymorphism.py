# filename: week5_polymorphism.py

class Bird:
    def fly(self):
        return "Flying"

class Sparrow(Bird):
    def fly(self):
        return "Sparrow flying"

class Penguin(Bird):
    def fly(self):
        return "Penguins can't fly"

# Demonstrate polymorphism
birds = [Sparrow(), Penguin()]
for bird in birds:
    print(bird.fly())