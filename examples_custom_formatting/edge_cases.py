#!/usr/bin/env python3
"""
Граничные случаи для демонстрации системы форматирования.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


# 1. Класс с декоратором @dataclass, но с методами - должен быть dataclass
@dataclass
class DataClassWithMethods:
    """Датакласс с дополнительными методами."""
    name: str
    value: int
    
    def get_display_name(self) -> str:
        """Получить отображаемое имя."""
        return f"DataClass: {self.name}"
    
    def calculate(self, multiplier: int) -> int:
        """Вычислить значение с множителем."""
        return self.value * multiplier


# 2. Класс без методов, но с полями - должен быть dataclass
class ImplicitDataClass:
    """Класс, который ведет себя как датакласс."""
    
    def __init__(self, field1: str, field2: int):
        self.field1 = field1
        self.field2 = field2


# 3. Класс без методов и без полей - должен быть interface
class EmptyInterface:
    """Пустой интерфейс."""
    pass


# 4. Абстрактный класс без конкретных методов
class PureAbstractClass(ABC):
    """Чисто абстрактный класс."""
    
    @abstractmethod
    def method1(self):
        pass
    
    @abstractmethod
    def method2(self):
        pass


# 5. Класс с множественными декораторами
@dataclass
class ComplexDataClass:
    """Сложный датакласс."""
    id: int
    name: str
    description: str = ""
    
    def __post_init__(self):
        """Пост-инициализация."""
        if not self.description:
            self.description = f"Description for {self.name}"
    
    def get_info(self) -> str:
        """Получить информацию."""
        return f"ID: {self.id}, Name: {self.name}, Description: {self.description}"


# 6. Обычный класс с множественными методами
class ComplexClass:
    """Сложный обычный класс."""
    
    def __init__(self, name: str):
        self.name = name
        self._private_field = "private"
        self.__very_private = "very private"
    
    def public_method(self) -> str:
        """Публичный метод."""
        return f"Public method of {self.name}"
    
    def _protected_method(self) -> str:
        """Защищенный метод."""
        return f"Protected method of {self.name}"
    
    def __private_method(self) -> str:
        """Приватный метод."""
        return f"Private method of {self.name}"
    
    @property
    def name_property(self) -> str:
        """Свойство для имени."""
        return self.name
    
    @name_property.setter
    def name_property(self, value: str) -> None:
        """Сеттер для имени."""
        self.name = value
    
    @staticmethod
    def static_method() -> str:
        """Статический метод."""
        return "Static method"
    
    @classmethod
    def class_method(cls) -> str:
        """Метод класса."""
        return f"Class method of {cls.__name__}"


# 7. Абстрактный класс с конкретными методами
class AbstractWithConcrete(ABC):
    """Абстрактный класс с конкретными методами."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def abstract_method(self):
        """Абстрактный метод."""
        pass
    
    def concrete_method(self) -> str:
        """Конкретный метод."""
        return f"Concrete method of {self.name}"
    
    def another_concrete_method(self) -> str:
        """Еще один конкретный метод."""
        return f"Another concrete method of {self.name}"


# 8. Класс с наследованием от абстрактного
class ConcreteImplementation(AbstractWithConcrete):
    """Конкретная реализация абстрактного класса."""
    
    def __init__(self, name: str, value: int):
        super().__init__(name)
        self.value = value
    
    def abstract_method(self):
        """Реализация абстрактного метода."""
        return f"Implementation of abstract method: {self.name} = {self.value}"


# 9. Датакласс с наследованием
@dataclass
class BaseDataClass:
    """Базовый датакласс."""
    id: int
    name: str


@dataclass
class DerivedDataClass(BaseDataClass):
    """Наследник датакласса."""
    description: str
    is_active: bool = True
    
    def get_full_info(self) -> str:
        """Получить полную информацию."""
        status = "active" if self.is_active else "inactive"
        return f"{self.name} (ID: {self.id}): {self.description} - {status}"


# 10. Класс с множественным наследованием
class Mixin1:
    """Первый миксин."""
    
    def method1(self) -> str:
        return "Mixin1 method"


class Mixin2:
    """Второй миксин."""
    
    def method2(self) -> str:
        return "Mixin2 method"


class MultipleInheritanceClass(Mixin1, Mixin2):
    """Класс с множественным наследованием."""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_name(self) -> str:
        return self.name
    
    def all_methods(self) -> str:
        return f"{self.get_name()}: {self.method1()}, {self.method2()}"
