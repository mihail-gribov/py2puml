#!/usr/bin/env python3
"""
Примеры различных типов классов для демонстрации новой системы форматирования.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


# 1. Обычный класс - будет отображаться как "class" со стандартным цветом
class RegularClass:
    """Обычный класс без специальных декораторов."""
    
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value
    
    def get_name(self) -> str:
        """Получить имя."""
        return self.name
    
    def get_value(self) -> int:
        """Получить значение."""
        return self.value
    
    def set_value(self, new_value: int) -> None:
        """Установить новое значение."""
        self.value = new_value


# 2. Абстрактный класс - будет отображаться как "abstract" с белым цветом
class AbstractShape(ABC):
    """Абстрактный базовый класс для геометрических фигур."""
    
    def __init__(self, color: str):
        self.color = color
    
    @abstractmethod
    def area(self) -> float:
        """Вычислить площадь фигуры."""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """Вычислить периметр фигуры."""
        pass
    
    def get_color(self) -> str:
        """Получить цвет фигуры."""
        return self.color


# 3. Датакласс - будет отображаться как "class" с зеленым цветом
@dataclass
class User:
    """Пользователь системы - датакласс."""
    name: str
    email: str
    age: int
    is_active: bool = True
    
    def get_display_name(self) -> str:
        """Получить отображаемое имя."""
        return f"{self.name} ({self.email})"
    
    def is_adult(self) -> bool:
        """Проверить, является ли пользователь совершеннолетним."""
        return self.age >= 18


# 4. Еще один датакласс с дополнительными параметрами
@dataclass(frozen=True)
class Point:
    """Неизменяемая точка в 2D пространстве."""
    x: float
    y: float
    
    def distance_to_origin(self) -> float:
        """Вычислить расстояние до начала координат."""
        return (self.x ** 2 + self.y ** 2) ** 0.5


# 5. Интерфейс (класс без методов) - будет отображаться как "interface" с белым цветом
class DatabaseConnection:
    """Интерфейс для подключения к базе данных."""
    pass


# 6. Конкретная реализация абстрактного класса
class Circle(AbstractShape):
    """Круг - реализация абстрактного класса AbstractShape."""
    
    def __init__(self, color: str, radius: float):
        super().__init__(color)
        self.radius = radius
    
    def area(self) -> float:
        """Вычислить площадь круга."""
        return 3.14159 * self.radius ** 2
    
    def perimeter(self) -> float:
        """Вычислить периметр круга."""
        return 2 * 3.14159 * self.radius


# 7. Еще один обычный класс
class Calculator:
    """Простой калькулятор."""
    
    def __init__(self):
        self.history: List[str] = []
    
    def add(self, a: float, b: float) -> float:
        """Сложение."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Умножение."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self) -> List[str]:
        """Получить историю операций."""
        return self.history.copy()


# 8. Класс с множественным наследованием
class Square(AbstractShape):
    """Квадрат - еще одна реализация AbstractShape."""
    
    def __init__(self, color: str, side: float):
        super().__init__(color)
        self.side = side
    
    def area(self) -> float:
        """Вычислить площадь квадрата."""
        return self.side ** 2
    
    def perimeter(self) -> float:
        """Вычислить периметр квадрата."""
        return 4 * self.side


# 9. Еще один датакласс с методами
@dataclass
class Product:
    """Товар в магазине."""
    name: str
    price: float
    category: str
    in_stock: bool = True
    
    def get_formatted_price(self) -> str:
        """Получить отформатированную цену."""
        return f"${self.price:.2f}"
    
    def is_expensive(self, threshold: float = 100.0) -> bool:
        """Проверить, является ли товар дорогим."""
        return self.price > threshold


# 10. Интерфейс для сервисов
class NotificationService:
    """Интерфейс для сервиса уведомлений."""
    pass
