"""Command-line entry point; expensive actions are always explicit commands."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import uuid
from datetime import datetime, timezone
from . import __version__
from .adapter import NeedsReview, Paused
from .config import load
from .engine import Engine, call_count
from .git import clean, git, identity
from .process import execute, CANCEL
from .state import Store, atomic_json


def parser():
    p=argparse.ArgumentParser(prog='codex-arena',description='Resumable local audit and improvement tournaments. No automatic merge or push.')
    p.add_argument('--version',action='version',version=__version__)
    commands=p.add_subparsers(dest='command',required=True)
    for name in ('plan','doctor','audit','run','resume','status','report','reconcile-usage'):
        cmd=commands.add_parser(name)
        cmd.add_argument('path',nargs='?',default='.')
        cmd.add_argument('--state-dir',type=Path,help='External state root (must be outside target repository)')
        cmd.add_argument('--run',dest='run_id',help='Saved run ID; required if there are multiple')
        if name in ('plan','audit','run'):
            cmd.add_argument('--agents',type=int,choices=(2,4,8,16,32),default=None)
        if name in ('plan','doctor','audit','run'):
            cmd.add_argument('--config',type=Path)
        if name in ('audit','run'):
            cmd.add_argument('--task-file',type=Path)
            cmd.add_argument('--new',action='store_true',help='Start a new run instead of continuing an existing one')
        if name=='resume':
            cmd.add_argument('--retry-interrupted',action='store_true',help='Retry interrupted jobs; editor changes are backed up to recovery branches first')
            cmd.add_argument('--soft-tokens',type=int,help='Explicit new dispatch ceiling, at most saved emergency ceiling')
        if name in ('status','report','plan','doctor'):
            cmd.add_argument('--json',action='store_true')
        if name=='reconcile-usage':
            cmd.add_argument('--attempt',type=Path,required=True,help='Exact envelope path from usage.unknown_attempts')
            cmd.add_argument('--input-tokens',type=int,required=True)
            cmd.add_argument('--output-tokens',type=int,required=True)
            cmd.add_argument('--cached-input-tokens',type=int,default=0)
    return p


def doctor(config):
    help_result=execute([config['codex_bin'],'exec','--help'],Path.cwd(),timeout=15)
    version=execute([config['codex_bin'],'--version'],Path.cwd(),timeout=15)
    supported=all(flag in help_result['stdout'] for flag in ('--json','--output-schema','--output-last-message','--sandbox'))
    if help_result['returncode'] or version['returncode'] or not supported:
        raise ValueError('Installed Codex CLI lacks required capabilities; inspect codex exec --help')
    return {'codex_version':version['stdout'].strip(),'capabilities_ok':True,'model':config['model'],
            'model_access':'not tested; doctor makes no model calls','checks':[c['name'] for c in config['checks']]}


def state_root(repo,common,argument):
    root=(argument or Path(os.environ.get('XDG_STATE_HOME',Path.home()/'.local/state'))/'codex-arena').expanduser().resolve()
    if root.is_relative_to(repo):
        raise ValueError('State root must be outside the target checkout')
    key=hashlib.sha256(str(common).encode()).hexdigest()[:20]
    return root/key


def select_run(root, args):
    if args.run_id:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',args.run_id):
            raise ValueError('Invalid run ID')
        result=root/args.run_id
        if not (result/'state.sqlite').exists():
            raise ValueError('Run not found')
        return result
    runs=sorted(p for p in root.glob('*') if (p/'state.sqlite').is_file()) if root.exists() else []
    if len(runs)>1:
        raise ValueError('Multiple runs found; select --run '+', '.join(p.name for p in runs))
    return runs[0] if runs else None


def main(argv=None):
    CANCEL.clear()
    def interrupt(signum, frame):
        CANCEL.set()
        raise KeyboardInterrupt()
    signal.signal(signal.SIGINT,interrupt)
    signal.signal(signal.SIGTERM,interrupt)
    args=parser().parse_args(argv)
    try:
        repo,common=identity(Path(args.path).resolve())
        if args.command=='plan':
            agents=args.agents or 32
            payload={'agents':agents,'implementation_candidates':min(8,agents),'base_model_jobs':call_count(agents),
                     'audit_model_jobs':agents+5*max(0,agents-8)+1,'concurrency':2,
                     'stages':['baseline','independent audit','plan tournament to 8','implementation','code tournament','final audit'],
                     'token_estimate':'not measured; user planning range 8–12M, soft 15M, emergency 17M',
                     'no_model_calls':True}
            if args.config:
                config=load(args.config)
                payload.update(concurrency=config['concurrency'],checks=config['checks'])
            print(json.dumps(payload,ensure_ascii=False,indent=2))
            return 0
        if args.command=='doctor':
            print(json.dumps(doctor(load(args.config)),ensure_ascii=False,indent=2))
            return 0
        root=state_root(repo,common,args.state_dir)
        directory=None if getattr(args,'new',False) else select_run(root,args)
        if directory is None:
            if args.command not in ('audit','run'):
                raise ValueError('No run found; start with audit/run --config profile.toml')
            clean(repo)
            config=load(args.config)
            capabilities=doctor(config)
            run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
            directory=root/run_id
            create={'id':run_id,'repo':str(repo),'common_dir':str(common),'base_sha':git(repo,'rev-parse','HEAD'),
                    'config':config,'agents':args.agents or 32,'status':'created',
                    'mode':args.command,'capabilities':capabilities,
                    'task':args.task_file.read_text() if args.task_file else
                    'Audit and improve this project comprehensively. Preserve product intent and visual direction. '
                    'Prioritize reproducible defects, robust behavior and maintainability. '
                    'For a working visual prototype, verify the user flows and clearly distinguish mocks from real integrations.'}
        else:
            create=None
        with Store(directory) as store:
            if create:
                store.put('run',create)
            run=store.get('run')
            if run['common_dir']!=str(common) or run['repo']!=str(repo):
                raise ValueError('This run belongs to a different source checkout')
            if args.command=='resume' and args.soft_tokens is not None:
                if not 0 < args.soft_tokens <= run['config']['emergency_tokens']:
                    raise ValueError('soft-tokens must be positive and at most the saved emergency ceiling')
                history=store.get('budget_history',[])
                history.append({'old':run['config']['soft_tokens'],'new':args.soft_tokens})
                store.put('budget_history',history)
                run['config']['soft_tokens']=args.soft_tokens
                store.put('run',run)
            if args.command in ('audit','run') and not create:
                if args.agents and args.agents!=run['agents']:
                    raise ValueError('Agents changed; use --new')
                if args.config and load(args.config)!=run['config']:
                    raise ValueError('Configuration changed; use --new')
                if args.task_file and args.task_file.read_text()!=run['task']:
                    raise ValueError('Task changed; use --new')
            if args.command=='reconcile-usage':
                file=args.attempt.resolve()
                if not file.is_relative_to(directory.resolve()/'jobs') or not file.name.endswith('.envelope.json'):
                    raise ValueError('Attempt path must be an envelope inside this run')
                if min(args.input_tokens,args.output_tokens,args.cached_input_tokens)<0 or args.cached_input_tokens>args.input_tokens:
                    raise ValueError('Invalid token counts')
                data=json.loads(file.read_text())
                if data.get('usage') is not None:
                    raise ValueError('Usage is already recorded; refuse overwrite')
                data['usage']={'input_tokens':args.input_tokens,'output_tokens':args.output_tokens,'cached_input_tokens':args.cached_input_tokens}
                data['usage_source']='manual reconciliation by explicit CLI command'
                atomic_json(file,data)
            engine=Engine(store,retry=getattr(args,'retry_interrupted',False),progress=lambda line:print(line,file=sys.stderr,flush=True))
            if args.command in ('audit','run','resume'):
                try:
                    # Source drift does not invalidate pinned base, but never edit a dirty source checkout.
                    clean(repo)
                    audit_only=args.command=='audit' or (args.command=='resume' and run.get('mode')=='audit')
                    engine.execute(audit_only=audit_only)
                except (Paused,NeedsReview,KeyboardInterrupt,RuntimeError,ValueError,OSError) as error:
                    engine.run.update(status='paused' if isinstance(error,(Paused,KeyboardInterrupt)) else 'needs-review',
                                      reason=str(error) or 'Interrupted by user')
                    engine.save()
                    engine.report()
                    print(f'{engine.run["status"]}: {engine.run["reason"]}\nState: {directory}',file=sys.stderr)
                    return 2
            report=engine.report()
            if getattr(args,'json',False):
                print(json.dumps(report,ensure_ascii=False,indent=2))
            else:
                print(f'{report["status"]}: {report["run_id"]}\nReport: {directory/"report.md"}')
                if report['winner_branch']:
                    print('Winner: '+report['winner_branch'])
            return 0
    except (ValueError,RuntimeError,OSError,json.JSONDecodeError) as error:
        print(f'codex-arena: {error}',file=sys.stderr)
        return 2
