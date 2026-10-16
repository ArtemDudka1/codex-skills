"""Independent checks pinned in run configuration, never supplied by competitors."""
import fnmatch
from pathlib import Path
from .process import execute
from .state import atomic_json, digest
from .git import git, snapshot

TEST_PATTERNS = ['tests/*','test/*','**/tests/*','**/test/*','test_*','**/test_*',
                 '*.test.*','*.spec.*','**/*.test.*','**/*.spec.*']
CONFIG_PATTERNS = ['*lock*','package.json','pyproject.toml','tsconfig*','eslint*',
                     '.github/*','**/.github/*','arena.toml','arena.json','AGENTS.md',
                     'conftest.py','**/conftest.py','pytest.ini','**/pytest.ini',
                     'setup.cfg','tox.ini','Makefile','vitest.config.*','vite.config.*',
                     'playwright.config.*','jest.config.*','scripts/*','**/scripts/*']
DEFAULT_PROTECTED = TEST_PATTERNS + CONFIG_PATTERNS


def eligible(results, changed_files, protected=None, added_files=()):
    required = [check for check in results.values() if check.get('required',True)]
    if not required or any(check['status'] != 'passed' for check in required):
        return False
    patterns = DEFAULT_PROTECTED if protected is None else protected
    for name in changed_files:
        matches = [p for p in patterns if fnmatch.fnmatch(name,p)]
        if matches and not (name in added_files and all(p in TEST_PATTERNS for p in matches)):
            return False
    return True


def run_checks(store, path, checks, label):
    path = Path(path)
    before = snapshot(path)
    cache_key = 'checks:'+digest({'snapshot':before,'checks':checks,'label':label})
    cached = store.get(cache_key)
    if cached:
        return cached
    results = {}
    directory = store.directory/'checks'/digest(cache_key)[:20]
    directory.mkdir(parents=True,exist_ok=True)
    for check in checks:
        name = check['name']
        record_path = directory/(name+'.json')
        stdout = directory/(name+'.stdout')
        stderr = directory/(name+'.stderr')
        cwd = (path/check.get('cwd','.')).resolve()
        if not cwd.is_relative_to(path.resolve()):
            raise RuntimeError('Check cwd escapes worktree')
        result = execute(check['argv'],cwd,timeout=check.get('timeout',300),stdout_path=stdout,stderr_path=stderr)
        record = {**result,'name':name,'required':check.get('required',True),
                  'status':'passed' if result['returncode'] in check.get('success_codes',[0]) and not result['timeout'] else 'failed',
                  'stdout_path':str(stdout), 'stderr_path':str(stderr),
                  'sha':git(path,'rev-parse','HEAD'), 'regression_detail':'exit-code only; no per-test identity parser'}
        atomic_json(record_path,record)
        results[name] = record
    # A check must not silently modify tracked files. Generated ignored outputs are allowed.
    if snapshot(path) != before:
        raise RuntimeError(f'Checks changed tracked/untracked sources in {path}; inspect before resuming')
    store.put(cache_key,results)
    return results
