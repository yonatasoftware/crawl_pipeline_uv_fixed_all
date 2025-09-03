import json, sys, time
from typing import Any, Mapping

def log(event: str, **fields: Any) -> None:
    rec: dict[str, Any] = {"event": event, "ts": time.time()}
    rec.update(fields)
    sys.stdout.write(json.dumps(rec) + "\n")
    sys.stdout.flush()
