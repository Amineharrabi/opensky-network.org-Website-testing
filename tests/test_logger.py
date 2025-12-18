import logging
import time as time_module


def get_logger(name: str) -> logging.Logger:
    """Return a console logger with consistent formatting.

    Uses plain ASCII prefixes to avoid Windows console encoding issues.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_test_start(logger: logging.Logger, test_name: str) -> None:
    logger.info(f"[START] {test_name}")


def log_test_end(
    logger: logging.Logger, test_name: str, duration: float, status: str = "PASSED"
) -> None:
    if status == "PASSED":
        logger.info(f"[PASS]  {test_name} ({duration:.2f}s)")
    elif status == "FAILED":
        logger.error(f"[FAIL]  {test_name} ({duration:.2f}s)")
    elif status == "SKIPPED":
        logger.warning(f"[SKIP]  {test_name}")
    else:
        logger.info(f"[DONE]  {test_name} ({duration:.2f}s)")


def log_step(logger: logging.Logger, step_num: int, description: str) -> None:
    logger.info(f"  [STEP {step_num}] {description}")


def log_check(logger: logging.Logger, message: str, passed: bool = True) -> None:
    prefix = "[OK]" if passed else "[WARN]"
    logger.info(f"  {prefix} {message}")


def slow_down(seconds: float = 1.0) -> None:
    time_module.sleep(seconds)
