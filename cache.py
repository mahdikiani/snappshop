import asyncio
import datetime
import json
import os
from pathlib import Path
from typing import Callable

try:
    base_dir = Path(os.path.dirname(__file__))
except NameError:
    base_dir = Path(".")


def file_cache(
    cache_file_name: Path = base_dir / "db" / "cache.json", ttl=60 * 60 * 24
):
    cached_data = {}

    def decorator(func: Callable):
        def get_cache():
            nonlocal cached_data
            if cached_data:
                return cached_data

            if not cache_file_name.exists():
                cache_file_name.parent.mkdir(parents=True, exist_ok=True)
                cached_data = (
                    {}
                )  # Ensure cached_data is initialized as an empty dictionary
                return cached_data
            with open(cache_file_name, "r") as f:
                cached_data = json.load(f)
            return cached_data

        def check_cache(*args, **kwargs):
            cache = get_cache()

            if func.__name__ not in cache:
                return None

            key = f"{args}:{kwargs}"
            if key not in cache[func.__name__]:
                return None

            cached = cache[func.__name__].get(key)
            timestamp = cached.get("timestamp")
            if datetime.datetime.now().timestamp() - timestamp > ttl:
                return None
            return cached.get("result")

        def update_cache(result, *args, **kwargs):
            cache = get_cache()

            cached = cache.get(func.__name__, {})
            key = f"{args}:{kwargs}"
            cached[key] = {
                "result": result,
                "timestamp": datetime.datetime.now().timestamp(),
            }
            cache[func.__name__] = cached
            with open(cache_file_name, "w") as f:
                json.dump(cache, f, ensure_ascii=False, indent=4)
            return result

        async def async_wrapper(*args, **kwargs):
            result = check_cache(*args, **kwargs)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            return update_cache(result, *args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            result = check_cache(*args, **kwargs)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            return update_cache(result, *args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


if __name__ == "__main__":
    # Example usage
    @file_cache(cache_file_name=Path("custom_cache.json"))
    def example_function(x):
        import time

        time.sleep(2)
        return x * x

    @file_cache(cache_file_name=Path("custom_async_cache.json"))
    async def example_async_function(x):
        await asyncio.sleep(2)
        return x * x

    # For async function
    async def test_async():
        print(await example_async_function(3))  # Should compute and cache the result
        print(await example_async_function(3))  # Should retrieve the result from cache

    # Usage
    print(example_function(3))  # Should compute and cache the result
    print(example_function(3))  # Should retrieve the result from cache

    asyncio.run(test_async())
