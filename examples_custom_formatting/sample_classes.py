#!/usr/bin/env python3
"""
Sample classes of every kind, used to demonstrate the formatting system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


# 1. Regular class - rendered as "class" with the default colour
class RegularClass:
    """Regular class without special decorators."""
    
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value
    
    def get_name(self) -> str:
        """Return the name."""
        return self.name
    
    def get_value(self) -> int:
        """Return the value."""
        return self.value
    
    def set_value(self, new_value: int) -> None:
        """Set a new value."""
        self.value = new_value


# 2. Abstract class - rendered as "abstract" with a white background
class AbstractShape(ABC):
    """Abstract base class for geometric shapes."""
    
    def __init__(self, color: str):
        self.color = color
    
    @abstractmethod
    def area(self) -> float:
        """Compute the area of the shape."""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """Compute the perimeter of the shape."""
        pass
    
    def get_color(self) -> str:
        """Return the colour of the shape."""
        return self.color


# 3. Dataclass - rendered as "class" with a green background
@dataclass
class User:
    """System user - a dataclass."""
    name: str
    email: str
    age: int
    is_active: bool = True
    
    def get_display_name(self) -> str:
        """Return the display name."""
        return f"{self.name} ({self.email})"
    
    def is_adult(self) -> bool:
        """Check whether the user is an adult."""
        return self.age >= 18


# 4. Another dataclass with extra parameters
@dataclass(frozen=True)
class Point:
    """Immutable point in 2D space."""
    x: float
    y: float
    
    def distance_to_origin(self) -> float:
        """Compute the distance to the origin."""
        return (self.x ** 2 + self.y ** 2) ** 0.5


# 5. Interface (a class without methods) - rendered as "interface" with a white background
class DatabaseConnection:
    """Interface for database connections."""
    pass


# 6. Concrete implementation of an abstract class
class Circle(AbstractShape):
    """Circle - an AbstractShape implementation."""
    
    def __init__(self, color: str, radius: float):
        super().__init__(color)
        self.radius = radius
    
    def area(self) -> float:
        """Compute the area of the circle."""
        return 3.14159 * self.radius ** 2
    
    def perimeter(self) -> float:
        """Compute the perimeter of the circle."""
        return 2 * 3.14159 * self.radius


# 7. Another regular class
class Calculator:
    """Simple calculator."""
    
    def __init__(self):
        self.history: List[str] = []
    
    def add(self, a: float, b: float) -> float:
        """Addition."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiplication."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self) -> List[str]:
        """Return the operation history."""
        return self.history.copy()


# 8. Class with multiple inheritance
class Square(AbstractShape):
    """Square - another AbstractShape implementation."""
    
    def __init__(self, color: str, side: float):
        super().__init__(color)
        self.side = side
    
    def area(self) -> float:
        """Compute the area of the square."""
        return self.side ** 2
    
    def perimeter(self) -> float:
        """Compute the perimeter of the square."""
        return 4 * self.side


# 9. Another dataclass with methods
@dataclass
class Product:
    """Product in the shop."""
    name: str
    price: float
    category: str
    in_stock: bool = True
    
    def get_formatted_price(self) -> str:
        """Return the formatted price."""
        return f"${self.price:.2f}"
    
    def is_expensive(self, threshold: float = 100.0) -> bool:
        """Check whether the product is expensive."""
        return self.price > threshold


# 10. Service interface
class NotificationService:
    """Interface for a notification service."""
    pass
