import time
import random
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")

class RateLimitCounter:
    def __init__(self, iterable: Iterable[T], limit: int = 5, wait_time: int = 3, jitter: bool = True):
        self.iterable = iterable
        self.limit = limit
        self.wait_time = wait_time
        self.jitter = jitter

    def __iter__(self) -> Iterator[T]:
        count = 0
        for item in self.iterable:
            yield item
            count += 1
            if count >= self.limit:
                self._wait()
                count = 0

    def _wait(self):
        wait_time = self.wait_time + random.uniform(0, 1) if self.jitter else self.wait_time
        time.sleep(wait_time)
