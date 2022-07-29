# Copyright 2022, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
from dataclasses import dataclass, field
import threading
from time import time
from collections import OrderedDict
from typing import Optional, Generic, TypeVar, Hashable
from sys import version_info

if version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol  # type: ignore

# generic type definitions for LRUCache parameters
K = TypeVar('K', bound=Hashable, contravariant=True)
V = TypeVar('V')


class LRUCache(Generic[K, V]):
    """Least Recently Used cache that invalidates entries older than the timeout."""

    def __init__(self, capacity: int, timeout_in_secs: int):
        self.lock = threading.Lock()
        self.map: OrderedDict[K, CacheElement[V]] = OrderedDict()
        self.capacity = capacity
        self.timeout = timeout_in_secs

    def lookup(self, key: K) -> Optional[V]:
        """Return the non-stale value associated with the provided key and move the
        element to the end of the cache. If the selected value is stale, remove it from
        the cache and clear the entire cache if stale.
        """
        if self.capacity <= 0:
            return None

        with self.lock:
            if key not in self.map:
                return None

            self.map.move_to_end(key)
            element = self.map[key]

            if element._is_stale(self.timeout):
                del self.map[key]
                return None

        return element.value

    def save(self, key: K, value: V) -> None:
        """Insert and/or move the provided key/value pair to the most recent end of the cache.
        If the cache grows beyond the cache capacity, the least recently used element will be
        removed.
        """
        if self.capacity <= 0:
            return

        with self.lock:
            if key in self.map:
                self.map.move_to_end(key)

            self.map[key] = CacheElement(value)

            if len(self.map) > self.capacity:
                self.map.popitem(last=False)

    def reset(self) -> None:
        """ Clear the cache."""
        if self.capacity <= 0:
            return
        with self.lock:
            self.map.clear()

    def peek(self, key: K) -> Optional[V]:
        """Returns the value associated with the provided key without updating the cache."""
        if self.capacity <= 0:
            return None
        with self.lock:
            element = self.map.get(key)
        return element.value if element is not None else None


@dataclass
class CacheElement(Generic[V]):
    """Individual element for the LRUCache."""
    value: V
    timestamp: float = field(default_factory=time)

    def _is_stale(self, timeout: float) -> bool:
        """Returns True if the provided timeout has passed since the element's timestamp."""
        if timeout <= 0:
            return False
        return time() - self.timestamp >= timeout


class OptimizelySegmentsCache(Protocol):
    """Protocol for implementing custom cache."""
    def reset(self) -> None:
        """ Clear the cache."""
        ...

    def lookup(self, key: str) -> Optional[list[str]]:
        """Return the value associated with the provided key."""
        ...

    def save(self, key: str, value: list[str]) -> None:
        """Save the key/value pair in the cache."""
        ...
