#!/usr/bin/env python3
"""
Advanced class examples for the formatting system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum


# 1. Enum - rendered as a regular class
class Status(Enum):
    """Order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# 2. Abstract class with several abstract methods
class AbstractRepository(ABC):
    """Abstract repository for data access."""
    
    @abstractmethod
    def save(self, entity) -> None:
        """Store an entity."""
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: str):
        """Find an entity by ID."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity."""
        pass
    
    @abstractmethod
    def find_all(self) -> List:
        """Find all entities."""
        pass


# 3. Complex dataclass with default field values
@dataclass
class Order:
    """An order in the system."""
    order_id: str
    customer_name: str
    items: List[Dict[str, Union[str, int, float]]] = field(default_factory=list)
    status: Status = Status.PENDING
    total_amount: float = 0.0
    created_at: Optional[str] = None
    
    def add_item(self, name: str, quantity: int, price: float) -> None:
        """Add an item to the order."""
        item = {
            "name": name,
            "quantity": quantity,
            "price": price,
            "total": quantity * price
        }
        self.items.append(item)
        self.total_amount += item["total"]
    
    def get_item_count(self) -> int:
        """Return the number of items."""
        return len(self.items)
    
    def is_empty(self) -> bool:
        """Check whether the order is empty."""
        return len(self.items) == 0


# 4. Regular class with multiple inheritance
class BaseEntity:
    """Base class for all entities."""
    
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.created_at = None
        self.updated_at = None
    
    def get_id(self) -> str:
        """Return the entity ID."""
        return self.entity_id


class TimestampMixin:
    """Mixin that maintains timestamps."""
    
    def update_timestamp(self) -> None:
        """Update the timestamp."""
        from datetime import datetime
        self.updated_at = datetime.now()


class EntityWithTimestamps(BaseEntity, TimestampMixin):
    """Entity carrying timestamps."""
    
    def __init__(self, entity_id: str, name: str):
        super().__init__(entity_id)
        self.name = name
        self.update_timestamp()
    
    def get_name(self) -> str:
        """Return the entity name."""
        return self.name


# 5. Validation interface
class Validator:
    """Interface for data validation."""
    pass


# 6. Concrete implementation of an abstract repository
class InMemoryRepository(AbstractRepository):
    """In-memory repository implementation."""
    
    def __init__(self):
        self._storage: Dict[str, any] = {}
    
    def save(self, entity) -> None:
        """Store an entity in memory."""
        if hasattr(entity, 'entity_id'):
            self._storage[entity.entity_id] = entity
    
    def find_by_id(self, entity_id: str):
        """Find an entity by ID."""
        return self._storage.get(entity_id)
    
    def delete(self, entity_id: str) -> bool:
        """Delete an entity."""
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False
    
    def find_all(self) -> List:
        """Find all entities."""
        return list(self._storage.values())


# 7. Another dataclass with nested structures
@dataclass
class Address:
    """Postal address."""
    street: str
    city: str
    postal_code: str
    country: str = "Russia"


@dataclass
class Customer:
    """Customer with an address."""
    customer_id: str
    name: str
    email: str
    address: Address
    phone: Optional[str] = None
    is_vip: bool = False
    
    def get_full_address(self) -> str:
        """Return the full address."""
        return f"{self.address.street}, {self.address.city}, {self.address.postal_code}, {self.address.country}"
    
    def is_local(self) -> bool:
        """Check whether the customer is local."""
        return self.address.country == "Russia"


# 8. Abstract class with concrete methods
class AbstractPaymentProcessor(ABC):
    """Abstract payment processor."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.is_configured = bool(api_key)
    
    @abstractmethod
    def process_payment(self, amount: float, currency: str) -> bool:
        """Process a payment."""
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: str) -> bool:
        """Refund a payment."""
        pass
    
    def is_ready(self) -> bool:
        """Check whether the processor is ready."""
        return self.is_configured


# 9. Regular class with decorated methods
class Logger:
    """Application logger."""
    
    def __init__(self, name: str):
        self.name = name
        self.logs: List[str] = []
    
    def info(self, message: str) -> None:
        """Log an informational message."""
        log_entry = f"[INFO] {self.name}: {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def error(self, message: str) -> None:
        """Log an error."""
        log_entry = f"[ERROR] {self.name}: {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def get_logs(self) -> List[str]:
        """Return every log entry."""
        return self.logs.copy()
    
    def clear_logs(self) -> None:
        """Clear the logs."""
        self.logs.clear()


# 10. Configuration interface
class ConfigProvider:
    """Configuration provider."""
    pass
