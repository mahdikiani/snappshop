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
    def decorator(func: Callable):
        def check_cache(*args, **kwargs):
            if not cache_file_name.exists():
                return
            with open(cache_file_name, "r") as f:
                cache = json.load(f)

            if func.__name__ not in cache:
                return

            key = f"{args}:{kwargs}"
            if key not in cache:
                return None

            cached = cache[func.__name__].get(key)
            timestamp = cached.get("timestamp")
            if datetime.datetime.now().timestamp() - timestamp > ttl:
                return None
            return cached.get("value")

        def update_cache(result, *args, **kwargs):
            if cache_file_name.exists():
                with open(cache_file_name, "r") as f:
                    cache = json.load(f)
            else:
                cache_file_name.parent.mkdir(parents=True, exist_ok=True)
                cache = {}

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
