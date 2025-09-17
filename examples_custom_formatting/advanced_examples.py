#!/usr/bin/env python3
"""
Продвинутые примеры классов для демонстрации системы форматирования.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum


# 1. Перечисление (enum) - будет отображаться как обычный класс
class Status(Enum):
    """Статусы заказа."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# 2. Абстрактный класс с множественными абстрактными методами
class AbstractRepository(ABC):
    """Абстрактный репозиторий для работы с данными."""
    
    @abstractmethod
    def save(self, entity) -> None:
        """Сохранить сущность."""
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: str):
        """Найти сущность по ID."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Удалить сущность."""
        pass
    
    @abstractmethod
    def find_all(self) -> List:
        """Найти все сущности."""
        pass


# 3. Сложный датакласс с полями по умолчанию
@dataclass
class Order:
    """Заказ в системе."""
    order_id: str
    customer_name: str
    items: List[Dict[str, Union[str, int, float]]] = field(default_factory=list)
    status: Status = Status.PENDING
    total_amount: float = 0.0
    created_at: Optional[str] = None
    
    def add_item(self, name: str, quantity: int, price: float) -> None:
        """Добавить товар в заказ."""
        item = {
            "name": name,
            "quantity": quantity,
            "price": price,
            "total": quantity * price
        }
        self.items.append(item)
        self.total_amount += item["total"]
    
    def get_item_count(self) -> int:
        """Получить количество товаров."""
        return len(self.items)
    
    def is_empty(self) -> bool:
        """Проверить, пустой ли заказ."""
        return len(self.items) == 0


# 4. Обычный класс с множественным наследованием
class BaseEntity:
    """Базовый класс для всех сущностей."""
    
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.created_at = None
        self.updated_at = None
    
    def get_id(self) -> str:
        """Получить ID сущности."""
        return self.entity_id


class TimestampMixin:
    """Миксин для работы с временными метками."""
    
    def update_timestamp(self) -> None:
        """Обновить временную метку."""
        from datetime import datetime
        self.updated_at = datetime.now()


class EntityWithTimestamps(BaseEntity, TimestampMixin):
    """Сущность с временными метками."""
    
    def __init__(self, entity_id: str, name: str):
        super().__init__(entity_id)
        self.name = name
        self.update_timestamp()
    
    def get_name(self) -> str:
        """Получить имя сущности."""
        return self.name


# 5. Интерфейс для валидации
class Validator:
    """Интерфейс для валидации данных."""
    pass


# 6. Конкретная реализация абстрактного репозитория
class InMemoryRepository(AbstractRepository):
    """Реализация репозитория в памяти."""
    
    def __init__(self):
        self._storage: Dict[str, any] = {}
    
    def save(self, entity) -> None:
        """Сохранить сущность в памяти."""
        if hasattr(entity, 'entity_id'):
            self._storage[entity.entity_id] = entity
    
    def find_by_id(self, entity_id: str):
        """Найти сущность по ID."""
        return self._storage.get(entity_id)
    
    def delete(self, entity_id: str) -> bool:
        """Удалить сущность."""
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False
    
    def find_all(self) -> List:
        """Найти все сущности."""
        return list(self._storage.values())


# 7. Еще один датакласс с вложенными структурами
@dataclass
class Address:
    """Адрес."""
    street: str
    city: str
    postal_code: str
    country: str = "Russia"


@dataclass
class Customer:
    """Клиент с адресом."""
    customer_id: str
    name: str
    email: str
    address: Address
    phone: Optional[str] = None
    is_vip: bool = False
    
    def get_full_address(self) -> str:
        """Получить полный адрес."""
        return f"{self.address.street}, {self.address.city}, {self.address.postal_code}, {self.address.country}"
    
    def is_local(self) -> bool:
        """Проверить, является ли клиент местным."""
        return self.address.country == "Russia"


# 8. Абстрактный класс с конкретными методами
class AbstractPaymentProcessor(ABC):
    """Абстрактный процессор платежей."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.is_configured = bool(api_key)
    
    @abstractmethod
    def process_payment(self, amount: float, currency: str) -> bool:
        """Обработать платеж."""
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: str) -> bool:
        """Вернуть платеж."""
        pass
    
    def is_ready(self) -> bool:
        """Проверить готовность процессора."""
        return self.is_configured


# 9. Обычный класс с декораторами методов
class Logger:
    """Логгер для приложения."""
    
    def __init__(self, name: str):
        self.name = name
        self.logs: List[str] = []
    
    def info(self, message: str) -> None:
        """Логировать информационное сообщение."""
        log_entry = f"[INFO] {self.name}: {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def error(self, message: str) -> None:
        """Логировать ошибку."""
        log_entry = f"[ERROR] {self.name}: {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def get_logs(self) -> List[str]:
        """Получить все логи."""
        return self.logs.copy()
    
    def clear_logs(self) -> None:
        """Очистить логи."""
        self.logs.clear()


# 10. Интерфейс для конфигурации
class ConfigProvider:
    """Провайдер конфигурации."""
    pass
