"""Bounded child processes; kill descendants on timeout or interruption."""
import os
from pathlib import Path
import signal
import subprocess
import time
import threading
from .state import atomic_json

CANCEL = threading.Event()


def process_birth(pid):
    result = subprocess.run(['ps','-p',str(pid),'-o','lstart='],capture_output=True,text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def still_running(record):
    return record.get('birth') is not None and process_birth(record['pid']) == record['birth']


def execute(argv, cwd, timeout=900, stdin=None, stdout_path=None, stderr_path=None, process_path=None, cancel_event=None):
    started = time.monotonic()
    out = open(stdout_path, 'w') if stdout_path else subprocess.PIPE
    err = open(stderr_path, 'w') if stderr_path else subprocess.PIPE
    child = None
    timed_out = False
    cancelled = False
    cancel = cancel_event or CANCEL
    try:
        child = subprocess.Popen(argv, cwd=Path(cwd), stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                 stdout=out, stderr=err, text=True, start_new_session=True,
                                 env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
        if process_path:
            atomic_json(process_path, {'pid':child.pid,'birth':process_birth(child.pid)})
        try:
            first = True
            while True:
                remaining=timeout-(time.monotonic()-started)
                if remaining<=0 or cancel.is_set():
                    timed_out=remaining<=0
                    cancelled=cancel.is_set()
                    os.killpg(child.pid, signal.SIGKILL)
                    stdout, stderr=child.communicate()
                    break
                try:
                    stdout, stderr=child.communicate(stdin if first else None, timeout=min(1,remaining))
                    break
                except subprocess.TimeoutExpired:
                    first=False
        except BaseException:
            os.killpg(child.pid, signal.SIGKILL)
            child.communicate()
            raise
        return {'returncode':child.returncode,'stdout':stdout or '', 'stderr':stderr or '',
                'timeout':timed_out, 'cancelled':cancelled, 'seconds':round(time.monotonic()-started,3)}
    finally:
        # Also stop any background server descendants after an otherwise successful command.
        if child is not None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if stdout_path:
            out.close()
        if stderr_path:
            err.close()
