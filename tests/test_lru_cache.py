# Copyright 2022, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
import time
from unittest import TestCase
from optimizely.odp.lru_cache import LRUCache, CacheProtocol
from typing import Optional


class LRUCacheTest(TestCase):
    def test_min_config(self):
        cache = LRUCache(1000, 2000)
        self.assertEqual(1000, cache.capacity)
        self.assertEqual(2000, cache.timeout)

        cache = LRUCache(0, 0)
        self.assertEqual(0, cache.capacity)
        self.assertEqual(0, cache.timeout)

    def test_save_and_lookup(self):
        max_size = 2
        cache = LRUCache(max_size, 1000)

        self.assertIsNone(cache.peek(1))
        cache.save(1, 100)                       # [1]
        cache.save(2, 200)                       # [1, 2]
        cache.save(3, 300)                       # [2, 3]
        self.assertIsNone(cache.peek(1))
        self.assertEqual(200, cache.peek(2))
        self.assertEqual(300, cache.peek(3))

        cache.save(2, 201)                       # [3, 2]
        cache.save(1, 101)                       # [2, 1]
        self.assertEqual(101, cache.peek(1))
        self.assertEqual(201, cache.peek(2))
        self.assertIsNone(cache.peek(3))

        self.assertIsNone(cache.lookup(3))       # [2, 1]
        self.assertEqual(201, cache.lookup(2))   # [1, 2]
        cache.save(3, 302)                       # [2, 3]
        self.assertIsNone(cache.peek(1))
        self.assertEqual(201, cache.peek(2))
        self.assertEqual(302, cache.peek(3))

        self.assertEqual(302, cache.lookup(3))   # [2, 3]
        cache.save(1, 103)                       # [3, 1]
        self.assertEqual(103, cache.peek(1))
        self.assertIsNone(cache.peek(2))
        self.assertEqual(302, cache.peek(3))

        self.assertEqual(len(cache.map), max_size)
        self.assertEqual(len(cache.map), cache.capacity)

    def test_size_zero(self):
        cache = LRUCache(0, 1000)

        self.assertIsNone(cache.lookup(1))
        cache.save(1, 100)                       # [1]
        self.assertIsNone(cache.lookup(1))

    def test_size_less_than_zero(self):
        cache = LRUCache(-2, 1000)

        self.assertIsNone(cache.lookup(1))
        cache.save(1, 100)                       # [1]
        self.assertIsNone(cache.lookup(1))

    def test_timeout(self):
        max_timeout = .5

        cache = LRUCache(1000, max_timeout)

        cache.save(1, 100)                       # [1]
        cache.save(2, 200)                       # [1, 2]
        cache.save(3, 300)                       # [1, 2, 3]
        time.sleep(1.1)  # wait to expire
        cache.save(4, 400)                       # [1, 2, 3, 4]
        cache.save(1, 101)                       # [2, 3, 4, 1]

        self.assertEqual(101, cache.lookup(1))   # [4, 1]
        self.assertIsNone(cache.lookup(2))
        self.assertIsNone(cache.lookup(3))
        self.assertEqual(400, cache.lookup(4))

    def test_timeout_zero(self):
        max_timeout = 0
        cache = LRUCache(1000, max_timeout)

        cache.save(1, 100)                       # [1]
        cache.save(2, 200)                       # [1, 2]
        time.sleep(1)  # wait to expire

        self.assertEqual(100, cache.lookup(1), "should not expire when timeout is 0")
        self.assertEqual(200, cache.lookup(2))

    def test_timeout_less_than_zero(self):
        max_timeout = -2
        cache = LRUCache(1000, max_timeout)

        cache.save(1, 100)                       # [1]
        cache.save(2, 200)                       # [1, 2]
        time.sleep(1)  # wait to expire

        self.assertEqual(100, cache.lookup(1), "should not expire when timeout is less than 0")
        self.assertEqual(200, cache.lookup(2))

    def test_all_stale(self):
        max_timeout = 1
        cache = LRUCache(1000, max_timeout)

        cache.save(1, 100)                       # [1]
        cache.save(2, 200)                       # [1, 2]
        cache.save(3, 300)                       # [1, 2, 3]
        time.sleep(1.1)  # wait to expire
        self.assertEqual(len(cache.map), 3)

        self.assertIsNone(cache.lookup(1))       # []
        self.assertEqual(len(cache.map), 0, "cache should be reset when detected that all items are stale")

    def test_reset(self):
        cache = LRUCache(1000, 600)
        cache.save('wow', 'great')
        cache.save('tow', 'freight')

        self.assertEqual(cache.lookup('wow'), 'great')
        self.assertEqual(len(cache.map), 2)

        cache.reset()

        self.assertEqual(cache.lookup('wow'), None)
        self.assertEqual(len(cache.map), 0)

        cache.save('cow', 'crate')
        self.assertEqual(cache.lookup('cow'), 'crate')

    # type checker tests
    # confirm that a custom cache and the LRUCache align with CacheProtocol
    class CustomCache:
        """Custom cache implementation for type checker"""
        def reset(self) -> None:
            ...

        def lookup(self, key: str) -> Optional[list[str]]:
            ...

        def save(self, key: str, value: list[str]) -> None:
            ...

        def peek(self, key: str) -> Optional[list[str]]:
            ...

        def extra(self) -> None:
            ...

    class TestCacheManager:
        """Test cache manager for type checker"""
        def __init__(self, cache: CacheProtocol[str, list[str]]) -> None:
            self.cache = cache

        def process(self) -> Optional[list[str]]:
            self.cache.reset()
            self.cache.save('key', ['value'])
            self.cache.peek('key')
            return self.cache.lookup('key')

    # confirm that LRUCache matches CacheProtocol
    TestCacheManager(LRUCache(0, 0))
    # confirm that custom cache implementation matches CacheProtocol
    TestCacheManager(CustomCache())
