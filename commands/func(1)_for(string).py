import asyncio
import time
import random
from abc import ABC, abstractmethod
from functools import lru_cache, wraps
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict

def timed(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper

def retry(times: int = 3):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == times - 1:
                        raise e
        return wrapper
    return decorator

class Task(ABC):
    @abstractmethod
    async def run(self) -> Any:
        pass

class IOTask(Task):
    @timed
    @retry(3)
    async def run(self) -> str:
        await asyncio.sleep(random.uniform(0.5, 2))
        if random.random() < 0.3:
            raise RuntimeError("IO failure")
        return "IO done"

class CPUTask(Task):
    def heavy(self, n: int) -> int:
        s = 0
        for i in range(n):
            s += i * i
        return s

    async def run(self) -> int:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.heavy, 2_000_000)

@lru_cache(maxsize=32)
def cached(x: int) -> int:
    time.sleep(1)
    return x * x

class TaskScheduler:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    def register(self, name: str, task: Task):
        self.tasks[name] = task

    async def execute(self):
        results = {}
        for name, task in self.tasks.items():
            try:
                results[name] = await task.run()
            except Exception as e:
                results[name] = str(e)
        return results

async def main():
    scheduler = TaskScheduler()

    scheduler.register("io1", IOTask())
    scheduler.register("io2", IOTask())
    scheduler.register("cpu", CPUTask())

    print(cached(10))
    print(cached(10))

    results = await scheduler.execute()
    for k, v in results.items():
        print(k, v)

if __name__ == "__main__":
    asyncio.run(main())
