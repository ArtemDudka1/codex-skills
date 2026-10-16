"""Single-writer ledger and durable, hashed response envelopes."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    with open(temporary, 'w') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)

    def __enter__(self):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = open(self.directory/'lock', 'a+')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise RuntimeError('Another Arena process holds this run lock') from None
        self.db = sqlite3.connect(self.directory/'state.sqlite')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, status TEXT NOT NULL,
              attempt INTEGER NOT NULL, fingerprint TEXT NOT NULL, result TEXT, error TEXT,
              updated REAL NOT NULL);
        ''')
        return self

    def __exit__(self, *args):
        self.db.close()
        self.lock.close()

    def get(self, key, default=None):
        row = self.db.execute('SELECT value FROM metadata WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, key, value):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',(key,json.dumps(value)))

    def job(self, job_id):
        self.db.row_factory = sqlite3.Row
        row = self.db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        return dict(row) if row else None

    def start(self, job_id, fingerprint):
        old = self.job(job_id)
        attempt = old['attempt']+1 if old else 1
        directory=self.directory/'jobs'/job_id
        directory.mkdir(parents=True,exist_ok=True)
        atomic_json(directory/f'{attempt:04d}.envelope.json',{
            'fingerprint':fingerprint,'usage':None,'valid':False,'result':None,
            'result_hash':digest(None),'returncode':None,'pending':True})
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?)',
                            (job_id,'running',attempt,fingerprint,None,None,time.time()))
        return attempt

    def finish(self, job_id, result):
        with self.db:
            self.db.execute("UPDATE jobs SET status='succeeded', result=?, error=NULL, updated=? WHERE id=?",
                            (json.dumps(result), time.time(), job_id))

    def fail(self, job_id, error):
        with self.db:
            self.db.execute("UPDATE jobs SET status='interrupted', error=?, updated=? WHERE id=?",
                            (str(error),time.time(),job_id))

    def jobs(self):
        self.db.row_factory = sqlite3.Row
        return [dict(row) for row in self.db.execute('SELECT * FROM jobs ORDER BY id')]

    def usage(self):
        # Envelopes include failed attempts too: their tokens were still consumed.
        raw = cached = 0
        unknown = []
        for envelope in (self.directory/'jobs').glob('*/*.envelope.json') if (self.directory/'jobs').exists() else []:
            data = json.loads(envelope.read_text())
            usage = data.get('usage')
            if usage is None:
                unknown.append(str(envelope))
            else:
                raw += usage['input_tokens'] + usage['output_tokens']
                cached += usage.get('cached_input_tokens',0)
        return {'raw_tokens':raw, 'cached_input_tokens':cached, 'unknown_attempts':unknown}
