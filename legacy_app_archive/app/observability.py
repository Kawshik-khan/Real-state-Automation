from collections import Counter
from threading import Lock
from time import perf_counter


class Metrics:
    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()
        self._latencies: dict[str, list[float]] = {}
        self._lock = Lock()

    def observe(self, name: str, elapsed: float) -> None:
        with self._lock:
            self._counts[name] += 1
            self._latencies.setdefault(name, []).append(elapsed)

    def prometheus(self) -> str:
        with self._lock:
            lines = []
            for name, count in self._counts.items():
                metric = name.replace("-", "_")
                lines.append(f"{metric}_total {count}")
                values = self._latencies.get(name, [])
                if values:
                    lines.append(f"{metric}_last_seconds {values[-1]:.6f}")
            return "\n".join(lines) + ("\n" if lines else "")


def redact_pii(value: str) -> str:
    import re

    value = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", value)
    return re.sub(r"\b\d{8,}\b", "[number]", value)


def timed(metrics: Metrics, name: str):
    def decorator(function):
        def wrapped(*args, **kwargs):
            started = perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                metrics.observe(name, perf_counter() - started)

        return wrapped

    return decorator