import logging
import time as time_module


def get_logger(name):
    """Get a logger that prints immediately to console"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', 
                                     datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_step(logger, step_num, description):
    """Log a test step with consistent formatting"""
    logger.info(f"  ├─ Step {step_num}: {description}")


def log_assert(logger, condition, message):
    """Log an assertion result"""
    if condition:
        logger.info(f"  ├─ ✅ {message}")
    else:
        logger.warning(f"  ├─ ❌ {message}")
    return condition


def slow_down(seconds=1.0):
    """Add a visible pause to the test execution"""
    time_module.sleep(seconds)
