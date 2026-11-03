# Logging

Reference for the backend's centralized logging: where messages go, how files rotate, log levels, and configuration.

---

## 📋 Contents

- [📄 Overview](#-overview)
- [⚙️ How it works](#️-how-it-works)
- [🔧 Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [📚 References](#-references)

---

## 📄 Overview

The backend uses Python's standard `logging` module, configured in one place: [backend/utils/logging_config.py](../backend/utils/logging_config.py). FastAPI applies that configuration at startup, from the `lifespan` event in [backend/main.py](../backend/main.py).

What it does:

- Writes to the **console** and to a **file** at the same time.
- **Rotates** log files so they do not grow without a limit.
- **Does not duplicate handlers**: calling `setup_logging()` again does not add a second copy.
- Takes the log level from the `LOG_LEVEL` environment variable.

---

## ⚙️ How it works

When the backend starts, `setup_logging()` configures the root logger with two handlers:

1. **`StreamHandler`** — writes messages to the console (stdout).
2. **`RotatingFileHandler`** — writes messages to a file and rotates the file when it reaches the size limit.

### Log file

- **Path**: `backend/logs/backend.log`
- **Maximum size per file**: 5 MB
- **Backups kept**: 5 (rotated files are renamed `backend.log.1`, `backend.log.2`, and so on)

The [backend/logs/](../backend/logs/) folder is created automatically if it does not exist.

### Message format

```text
2026-04-17 10:23:45 | INFO     | module.name | Log message
```

The fields are: timestamp, level, logger name (usually the Python module), and message.

### Use in code

Each module gets its own logger with the usual `__name__`:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Operation completed")
logger.warning("Unexpected value")
logger.error("Processing failed")
```

Individual modules do not configure logging themselves. They inherit it from the root logger.

`utils.replay_guard` logs when the SSO single-use check cannot reach Redis (missing variables, timeout, or an invalid response). The message does not include the SSO token or the value of `KV_REST_API_TOKEN`. `api.auth` logs `SSO replay guard unavailable` and rejects the sign-in.

### Third-party libraries kept quiet

The low-level HTTP libraries used underneath (`httpx`, `httpcore`, `hpack`) print raw HTTP headers at `DEBUG`, including `Authorization` and `apikey`, which is the `SUPABASE_SERVICE_ROLE_KEY`. To keep those out of the log file, `setup_logging()` forces those three loggers to `WARNING` **regardless** of the `LOG_LEVEL` chosen for the rest of the app. You can set `LOG_LEVEL=DEBUG` to debug application logic without writing secrets to disk.

---

## 🔧 Configuration

The log level is the `LOG_LEVEL` environment variable in [backend/.env](../backend/.env) (see [backend/.env.example](../backend/.env.example) for the template).

Accepted values, from the most verbose to the least:

- `DEBUG` — every detail, useful while developing.
- `INFO` — meaningful events in the normal flow (the default).
- `WARNING` — suspicious situations that do not stop the process.
- `ERROR` — handled errors.
- `CRITICAL` — severe errors that can break the application.

Example in `.env`:

```env
LOG_LEVEL=DEBUG
```

For a temporary override (useful in tests), `setup_logging()` takes optional arguments:

```python
from pathlib import Path
from utils.logging_config import setup_logging

setup_logging(log_level="DEBUG", log_file=Path("/tmp/custom.log"))
```

---

## 🧪 Testing

Logging tests live in [backend/tests/utils/test_logging_config.py](../backend/tests/utils/test_logging_config.py). They check:

- that log files and handlers are created correctly
- that messages are actually written
- that setup is idempotent

From the `backend/` folder:

```bash
pytest tests/utils/test_logging_config.py -v
```

---

## 📚 References

- **Code**: [backend/utils/logging_config.py](../backend/utils/logging_config.py)
- **Tests**: [backend/tests/utils/test_logging_config.py](../backend/tests/utils/test_logging_config.py)
- **Related docs**: [Configuration](config.md), [Repository structure](repo_structure.md)
- **External**: [Python logging HOWTO](https://docs.python.org/3/howto/logging.html), [RotatingFileHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.RotatingFileHandler)
