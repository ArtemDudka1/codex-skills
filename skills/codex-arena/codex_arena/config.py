"""Explicit portable profiles; no inference of mandatory project checks."""
import json
import math
from pathlib import Path
import re
import tomllib
from .checks import DEFAULT_PROTECTED

DEFAULTS = {'codex_bin':'codex','model':None,'concurrency':2,'job_timeout':1800,
            'wall_seconds':16200,'job_reserve_tokens':100000,
            'soft_tokens':15000000,'emergency_tokens':17000000,'max_attempts':2,
            'setup':[],'checks':[],'protected_paths':DEFAULT_PROTECTED}


def load(path=None):
    config=dict(DEFAULTS)
    if path:
        path=Path(path).resolve()
        data=json.loads(path.read_text()) if path.suffix=='.json' else tomllib.loads(path.read_text())
        config.update(data)
    if not isinstance(config['model'],str) or not config['model'].strip():
        raise ValueError('Set an explicit CLI model ID in --config (model = "..."); no automatic fallback')
    for key in ('concurrency','job_timeout','wall_seconds','job_reserve_tokens','soft_tokens','emergency_tokens','max_attempts'):
        if type(config[key]) is not int or config[key]<=0:
            raise ValueError(f'{key} must be a positive integer')
    if config['concurrency']>8:
        raise ValueError('concurrency must be at most 8 in this version')
    if config['soft_tokens']>config['emergency_tokens']:
        raise ValueError('soft_tokens must not exceed emergency_tokens')
    if not isinstance(config['codex_bin'],str) or not config['codex_bin']:
        raise ValueError('codex_bin must be a nonempty executable path/name')
    if not isinstance(config['protected_paths'],list) or any(not isinstance(p,str) for p in config['protected_paths']):
        raise ValueError('protected_paths must be a list of patterns')
    config['protected_paths']=list(dict.fromkeys(DEFAULT_PROTECTED+config['protected_paths']))
    names=set()
    for field in ('setup','checks'):
        if not isinstance(config[field],list):
            raise ValueError(f'{field} must be an array')
        for command in config[field]:
            argv=command.get('argv')
            if not isinstance(argv,list) or not argv or any(not isinstance(s,str) or not s for s in argv):
                raise ValueError(f'{field}: argv must be a nonempty list of strings')
            timeout=command.get('timeout',300)
            if type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<=0:
                raise ValueError('timeout must be positive and finite')
            if field=='checks':
                name=command.get('name','')
                if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',name) or name in names:
                    raise ValueError('Check names must be unique simple identifiers')
                names.add(name)
                if type(command.get('required',True)) is not bool:
                    raise ValueError('Check required must be boolean')
                codes=command.get('success_codes',[0])
                if not isinstance(codes,list) or not codes or any(type(c) is not int for c in codes):
                    raise ValueError('Check success_codes must be an integer list')
    return config
