import logging
import time as time_module


def get_logger(name):
    """Get a logger that prints immediately to console"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(message)s', 
                                     datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_test_start(logger, test_name):
    """Log test start with clear formatting"""
    logger.info(f"▶️  {test_name}")


def log_test_end(logger, test_name, duration, status="PASSED"):
    """Log test end with duration and status"""
    if status == "PASSED":
        logger.info(f"✅ {test_name} passed in {duration:.2f}s")
    elif status == "FAILED":
        logger.error(f"❌ {test_name} FAILED in {duration:.2f}s")
    elif status == "SKIPPED":
        logger.warning(f"⊘ {test_name} skipped")
    else:
        logger.info(f"⏹️  {test_name} completed in {duration:.2f}s")


def log_step(logger, step_num, description):
    """Log a test step with consistent formatting"""
    logger.info(f"    ├─ Step {step_num}: {description}")


def log_check(logger, message, passed=True):
    """Log an assertion or check result"""
    symbol = "✅" if passed else "⚠️ "
    logger.info(f"    │  {symbol} {message}")


def slow_down(seconds=1.0):
    """Add a visible pause to the test execution"""
    time_module.sleep(seconds)
