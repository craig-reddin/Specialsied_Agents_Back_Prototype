# filename: week6_abstract_classes.py

from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14 * self.radius * self.radius

# Create an instance of Circle
circle = Circle(5)
print(f"Area of the circle: {circle.area()}")