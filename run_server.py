import os
import sys
import traceback
import uvicorn

if __name__ == "__main__":
    try:
        sys.stdin = open(os.devnull, "r")
    except Exception:
        pass

    try:
        uvicorn.run(
            "backend.main:app",
            host="127.0.0.1",
            port=8000,
            log_level="info",
            access_log=True
        )
    except Exception as exc:
        with open("server_exit.log", "w", encoding="utf-8") as f:
            f.write(f"Exception: {exc}\n")
            traceback.print_exc(file=f)
    except BaseException as be:
        with open("server_exit.log", "w", encoding="utf-8") as f:
            f.write(f"BaseException: {type(be).__name__}: {be}\n")
            traceback.print_exc(file=f)
