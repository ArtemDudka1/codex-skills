"""Git operations only in dedicated worktrees; pin source and detect drift."""
from pathlib import Path
import subprocess
from .state import digest


def git(path, *args, raw=False):
    result = subprocess.run(['git','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false',
                             '-C',str(path),*args],text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError(f'Git {args[0]}: {result.stderr.strip()}')
    return result.stdout if raw else result.stdout.strip()


def identity(path):
    root = Path(git(path,'rev-parse','--show-toplevel')).resolve()
    common = Path(git(root,'rev-parse','--path-format=absolute','--git-common-dir')).resolve()
    return root, common


def clean(path):
    if git(path,'status','--porcelain'):
        raise RuntimeError('Target checkout has uncommitted/untracked changes; commit or move them first')


def snapshot(path):
    # Covers staged, unstaged and nonignored untracked file contents without changing the index.
    names = git(path,'ls-files','--cached','--others','--exclude-standard','-z').split('\0')
    rows = []
    for name in sorted(set(names)):
        if not name:
            continue
        item = Path(path)/name
        if item.is_symlink():
            rows.append((name,'symlink',str(item.readlink())))
        elif item.is_file():
            import hashlib
            rows.append((name,item.stat().st_mode & 0o777,hashlib.sha256(item.read_bytes()).hexdigest()))
        else:
            rows.append((name,'missing',None))
    return digest({'head':git(path,'rev-parse','HEAD'),'files':rows,
                   'status':git(path,'status','--porcelain')})


def worktree(repo, path, base, branch=None):
    path = Path(path)
    if path.exists():
        root = Path(git(path,'rev-parse','--show-toplevel')).resolve()
        if root != path.resolve():
            raise RuntimeError(f'Existing path is not a worktree: {path}')
        return path
    path.parent.mkdir(parents=True,exist_ok=True)
    if branch:
        refs = git(repo,'for-each-ref','--format=%(refname:short)',f'refs/heads/{branch}')
        if refs:
            git(repo,'worktree','add',str(path),branch)
        else:
            git(repo,'worktree','add','-b',branch,str(path),base)
    else:
        git(repo,'worktree','add','--detach',str(path),base)
    return path


def commit(path, message):
    git(path,'add','--all')
    if git(path,'diff','--cached','--name-only'):
        git(path,'-c','user.name=Codex Arena','-c','user.email=arena@localhost',
            'commit','-m',message)
    return git(path,'rev-parse','HEAD')


def changed(path, base):
    return git(path,'diff','--name-only',base,'HEAD').splitlines()
