#!/usr/bin/env python3
"""
Edge cases for the formatting system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


# 1. Class decorated with @dataclass but carrying methods - still a dataclass
@dataclass
class DataClassWithMethods:
    """Dataclass with extra methods."""
    name: str
    value: int
    
    def get_display_name(self) -> str:
        """Return the display name."""
        return f"DataClass: {self.name}"
    
    def calculate(self, multiplier: int) -> int:
        """Compute the value with a multiplier."""
        return self.value * multiplier


# 2. Class without methods but with fields - should be a dataclass
class ImplicitDataClass:
    """Class that behaves like a dataclass."""
    
    def __init__(self, field1: str, field2: int):
        self.field1 = field1
        self.field2 = field2


# 3. Class without methods and without fields - should be an interface
class EmptyInterface:
    """Empty interface."""
    pass


# 4. Abstract class without concrete methods
class PureAbstractClass(ABC):
    """Purely abstract class."""
    
    @abstractmethod
    def method1(self):
        pass
    
    @abstractmethod
    def method2(self):
        pass


# 5. Class with several decorators
@dataclass
class ComplexDataClass:
    """Complex dataclass."""
    id: int
    name: str
    description: str = ""
    
    def __post_init__(self):
        """Post-initialisation hook."""
        if not self.description:
            self.description = f"Description for {self.name}"
    
    def get_info(self) -> str:
        """Return the details."""
        return f"ID: {self.id}, Name: {self.name}, Description: {self.description}"


# 6. Regular class with several methods
class ComplexClass:
    """Complex regular class."""
    
    def __init__(self, name: str):
        self.name = name
        self._private_field = "private"
        self.__very_private = "very private"
    
    def public_method(self) -> str:
        """Public method."""
        return f"Public method of {self.name}"
    
    def _protected_method(self) -> str:
        """Protected method."""
        return f"Protected method of {self.name}"
    
    def __private_method(self) -> str:
        """Private method."""
        return f"Private method of {self.name}"
    
    @property
    def name_property(self) -> str:
        """Name property."""
        return self.name
    
    @name_property.setter
    def name_property(self, value: str) -> None:
        """Name setter."""
        self.name = value
    
    @staticmethod
    def static_method() -> str:
        """Static method."""
        return "Static method"
    
    @classmethod
    def class_method(cls) -> str:
        """Class method."""
        return f"Class method of {cls.__name__}"


# 7. Abstract class with concrete methods
class AbstractWithConcrete(ABC):
    """Abstract class with concrete methods."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def abstract_method(self):
        """Abstract method."""
        pass
    
    def concrete_method(self) -> str:
        """Concrete method."""
        return f"Concrete method of {self.name}"
    
    def another_concrete_method(self) -> str:
        """Another concrete method."""
        return f"Another concrete method of {self.name}"


# 8. Class inheriting from an abstract one
class ConcreteImplementation(AbstractWithConcrete):
    """Concrete implementation of an abstract class."""
    
    def __init__(self, name: str, value: int):
        super().__init__(name)
        self.value = value
    
    def abstract_method(self):
        """Implementation of an abstract method."""
        return f"Implementation of abstract method: {self.name} = {self.value}"


# 9. Dataclass with inheritance
@dataclass
class BaseDataClass:
    """Base dataclass."""
    id: int
    name: str


@dataclass
class DerivedDataClass(BaseDataClass):
    """Subclass of a dataclass."""
    description: str
    is_active: bool = True
    
    def get_full_info(self) -> str:
        """Return the full details."""
        status = "active" if self.is_active else "inactive"
        return f"{self.name} (ID: {self.id}): {self.description} - {status}"


# 10. Class with multiple inheritance
class Mixin1:
    """First mixin."""
    
    def method1(self) -> str:
        return "Mixin1 method"


class Mixin2:
    """Second mixin."""
    
    def method2(self) -> str:
        return "Mixin2 method"


class MultipleInheritanceClass(Mixin1, Mixin2):
    """Class with multiple inheritance."""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_name(self) -> str:
        return self.name
    
    def all_methods(self) -> str:
        return f"{self.get_name()}: {self.method1()}, {self.method2()}"
