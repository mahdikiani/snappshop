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


def file_cache(cache_file_name: Path = base_dir / "db" / "cache.json"):
    def decorator(func: Callable):
        def check_cache(*args, **kwargs):
            if cache_file_name.exists():
                key = f"{func.__name__}:{args}:{kwargs}"
                with open(cache_file_name, "r") as f:
                    cache = json.load(f)
                if key in cache:
                    cached = cache[key]
                    timestamp = cached.get("timestamp")
                    if datetime.datetime.now().timestamp() - timestamp < 60 * 60 * 24:
                        return cached.get("result")
            return None

        def update_cache(result, *args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            if cache_file_name.exists():
                with open(cache_file_name, "r") as f:
                    cache = json.load(f)
            else:
                cache = {}
            cache[key] = {
                "result": result,
                "timestamp": datetime.datetime.now().timestamp(),
            }
            with open(cache_file_name, "w") as f:
                json.dump(cache, f)
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
