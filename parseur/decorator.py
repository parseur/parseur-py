import functools
import logging
import time
from typing import Any, Callable, Iterable


def rate_limited_batch(batch_size: int = 5, max_per_second: int = 5):
    """
    Decorator for a batch-processing function that takes a list of items and yields results.
    Applies rate limiting: max N calls per second, B items per batch.
    """
    assert batch_size > 0 and max_per_second > 0

    def decorator(func: Callable[..., Iterable[Any]]):
        @functools.wraps(func)
        def wrapper(cls, items: Iterable[Any], *args, **kwargs) -> Iterable[Any]:
            batch = []
            start_time = None

            for item in items:
                logging.info(f"Processing item: {item}")
                batch.append(item)

                if len(batch) >= batch_size:
                    if start_time:
                        elapsed = time.time() - start_time
                        sleep_time = max(0, 1.0 - elapsed)
                        if sleep_time > 0:
                            time.sleep(sleep_time)

                    start_time = time.time()
                    for result in func(cls, batch, *args, **kwargs):
                        yield result
                    batch = []

            # Remaining items
            if batch:
                if start_time:
                    elapsed = time.time() - start_time
                    sleep_time = max(0, 1.0 - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                for result in func(cls, batch, *args, **kwargs):
                    yield result

        return wrapper

    return decorator
