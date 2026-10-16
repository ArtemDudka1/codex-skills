"""Deterministic tournament; all expensive work has stable durable job identities."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time
from . import git as vcs
from .adapter import NeedsReview, Paused, activate, perform, prepare
from .checks import eligible, run_checks
from .state import atomic_json, digest

LENSES = ['architecture','business logic','edge cases','state and concurrency','API contracts',
          'data and migrations','security','dependencies','test quality','performance',
          'typing','error handling','UI and accessibility','maintainability',
          'build and operations','documentation']


def call_count(agents):
    finalists = min(8, agents)
    return agents + 5*(agents-1) + finalists + 2


class Engine:
    def __init__(self, store, retry=False, progress=None):
        self.store = store
        self.run = store.get('run')
        self.config = self.run['config']
        self.retry = retry
        self.progress = progress or (lambda message: None)
        self.started = time.monotonic()

    def save(self):
        self.store.put('run',self.run)

    def context(self, job_id, role, phase, cwd, **extra):
        existing = self.store.get('context:'+job_id)
        if existing is not None:
            return existing
        reasoning = 'high' if phase == 'code' and role in ('attack','judge','defend','final') else 'medium'
        context = {'job_id':job_id,'role':role,'phase':phase,'cwd':str(cwd),
                   'task':self.run['task'],'base_sha':self.run['base_sha'],
                   'reasoning':reasoning, 'config':self.config, **extra}
        self.store.put('context:'+job_id,context)
        return context

    def budget(self, count=1, ignored_attempts=()):
        usage = self.store.usage()
        if set(usage['unknown_attempts']) - set(ignored_attempts):
            raise Paused('Usage unknown for an earlier attempt; inspect JSONL and reconcile-usage before dispatch')
        if time.monotonic()-self.started >= self.config['wall_seconds']:
            raise Paused('Wall-time dispatch limit reached')
        reserve = count*self.config['job_reserve_tokens']
        if usage['raw_tokens']+reserve > min(self.config['soft_tokens'],self.config['emergency_tokens']):
            raise Paused('Token dispatch limit reached; completed work retained')

    def jobs(self, contexts):
        results = {}
        pending = []
        for context in contexts:
            # Only budget fresh calls, never prevent recovery of completed results.
            job = self.store.job(context['job_id'])
            if not job:
                self.budget(len(pending)+1,[t['prefix']+'.envelope.json' for t in pending])
            result, task = prepare(self.store,self.config,context,self.retry,
                                   allowed_pending=[t['prefix']+'.envelope.json' for t in pending],defer_start=True)
            if task is None:
                results[context['job_id']] = result
            else:
                pending.append(task)
        if pending:
            self.budget(len(pending),[t['prefix']+'.envelope.json' for t in pending])
            for task in pending:
                activate(self.store,task)
            errors = []
            with ThreadPoolExecutor(max_workers=self.config['concurrency']) as pool:
                future_tasks = {pool.submit(perform, task):task for task in pending}
                for future in as_completed(future_tasks):
                    task = future_tasks[future]
                    data = future.result()
                    if data['valid']:
                        self.store.finish(task['job_id'],data['result'])
                        results[task['job_id']] = data['result']
                    else:
                        self.store.fail(task['job_id'],data['error'])
                        errors.append(task['job_id']+': '+data['error'])
                    self.progress(f'{task["job_id"]}: {"saved" if data["valid"] else "interrupted"}')
            if errors:
                raise Paused('; '.join(errors))
            self.budget(0)
        return results

    def wave(self, contexts):
        # Submit only one concurrency-sized wave; never queue a full phase across a budget check.
        results = {}
        size = self.config['concurrency']
        for offset in range(0,len(contexts),size):
            results.update(self.jobs(contexts[offset:offset+size]))
        return results

    def one(self, context):
        return self.jobs([context])[context['job_id']]

    def tree(self, candidate=None):
        name = candidate or 'baseline'
        branch = f'arena/{self.run["id"]}/{candidate}' if candidate else None
        path = vcs.worktree(self.run['repo'],self.store.directory/'worktrees'/name,
                            self.run['base_sha'],branch)
        if vcs.identity(path)[1] != Path(self.run['common_dir']):
            raise NeedsReview('Worktree belongs to a different repository')
        if branch and vcs.git(path,'branch','--show-current') != branch:
            raise NeedsReview(f'Wrong worktree branch: {path}')
        return path

    def check_candidate_drift(self):
        for candidate, state in self.store.get('candidates',{}).items():
            path = Path(state['path'])
            if not path.exists():
                raise NeedsReview(f'Missing candidate worktree: {candidate}')
            if vcs.git(path,'rev-parse','HEAD') != state['sha']:
                intent = self.store.get('commit-intent:'+str(state.get('pending')))
                if not self.matches_commit_intent(path,intent):
                    raise NeedsReview(f'Candidate HEAD changed externally: {candidate}')
                state.update(sha=vcs.git(path,'rev-parse','HEAD'),snapshot=vcs.snapshot(path))
                candidates=self.store.get('candidates',{})
                candidates[candidate]=state
                self.store.put('candidates',candidates)
            if vcs.snapshot(path) != state['snapshot']:
                # A saved editor result authorizes accepting its edits during recovery only.
                pending = state.get('pending')
                job = self.store.job(pending) if pending else None
                envelope_path = (self.store.directory/'jobs'/pending/f'{job["attempt"]:04d}.envelope.json') if job else None
                envelope = json.loads(envelope_path.read_text()) if envelope_path and envelope_path.exists() else {}
                current_snapshot=vcs.snapshot(path)
                saved_editor_snapshot=envelope.get('workspace_snapshot')
                if not job or (current_snapshot != saved_editor_snapshot and not self.retry):
                    raise NeedsReview(f'Candidate sources changed externally: {candidate}')

    def matches_commit_intent(self, path, intent):
        return bool(intent and vcs.git(path,'rev-parse','HEAD^') == intent['parent']
                    and vcs.git(path,'rev-parse','HEAD^{tree}') == intent['tree']
                    and vcs.git(path,'log','-1','--format=%s') == intent['message']
                    and vcs.git(path,'branch','--show-current') == intent['branch']
                    and not vcs.git(path,'status','--porcelain'))

    def stage_checks(self, path, label):
        fingerprint=vcs.snapshot(path)
        cached = self.store.get('stagechecks:'+label)
        if cached is not None and cached['snapshot']==fingerprint:
            return cached['results']
        checks = run_checks(self.store,path,self.config['checks'],label)
        self.store.put('stagechecks:'+label,{'snapshot':fingerprint,'results':checks})
        return checks

    def capture(self, candidate, path, job_id):
        key = 'edit:'+job_id
        cached = self.store.get(key)
        if cached:
            return cached
        candidates = self.store.get('candidates',{})
        state = candidates[candidate]
        if vcs.git(path,'rev-parse','HEAD') != state['sha']:
            raise NeedsReview(f'Editor changed Git HEAD: {candidate}')
        if vcs.git(path,'branch','--show-current') != state['branch']:
            raise NeedsReview(f'Editor changed Git branch: {candidate}')
        intent=self.store.get('commit-intent:'+job_id)
        if intent and self.matches_commit_intent(path,intent):
            sha=vcs.git(path,'rev-parse','HEAD')
        else:
            vcs.git(path,'add','--all')
            intent={'parent':state['sha'],'tree':vcs.git(path,'write-tree'),
                    'message':f'Arena {self.run["id"]}: {job_id}','branch':state['branch']}
            self.store.put('commit-intent:'+job_id,intent)
            sha = vcs.commit(path,intent['message'])
        # Checkpoint the Git result before running any potentially failing external commands.
        state.update(sha=sha,snapshot=vcs.snapshot(path))
        candidates[candidate]=state
        self.store.put('candidates',candidates)
        files = vcs.changed(path,self.run['base_sha'])
        additions = vcs.git(path,'diff','--name-only','--diff-filter=A',self.run['base_sha'],'HEAD').splitlines()
        checks = self.stage_checks(path,job_id)
        if any(check['sha'] != sha for check in checks.values()):
            raise NeedsReview('Verification evidence belongs to a different revision')
        candidate_result = {'id':candidate,'path':str(path),'branch':state['branch'],'sha':sha,
                            'snapshot':vcs.snapshot(path),'checks':checks,'changed_files':files,'added_files':additions,
                            'eligible':eligible(checks,files,self.config['protected_paths'],additions)}
        candidates[candidate] = {**candidate_result,'pending':None}
        self.store.put('candidates',candidates)
        self.store.put(key,candidate_result)
        return candidate_result

    def edits(self, candidates, contexts):
        states = self.store.get('candidates',{})
        for candidate, context in zip(candidates,contexts):
            if self.store.get('edit:'+context['job_id']):
                continue
            path = Path(context['cwd'])
            if candidate not in states:
                states[candidate] = {'id':candidate,'path':str(path),
                                     'branch':f'arena/{self.run["id"]}/{candidate}',
                                     'sha':vcs.git(path,'rev-parse','HEAD'),'snapshot':vcs.snapshot(path)}
            if states[candidate].get('pending') not in (None,context['job_id']):
                raise NeedsReview('Candidate has another pending editor')
            states[candidate]['pending'] = context['job_id']
        self.store.put('candidates',states)
        answers = self.wave(contexts)
        result = {}
        for candidate, context in zip(candidates,contexts):
            record = self.capture(candidate,Path(context['cwd']),context['job_id'])
            result[candidate] = {**record,'report':answers[context['job_id']]}
        return result

    def registry(self, reports, source):
        registry = self.store.get('findings',{})
        for candidate, report in reports.items():
            for index, finding in enumerate(report.get('findings',[]),1):
                if source != 'initial' and any(all(old.get(k)==v for k,v in finding.items()) for old in registry.values()):
                    continue
                identifier = f'{source}-{candidate}-f{index:03d}'
                registry[identifier] = {**finding,'id':identifier,'source':candidate,
                                        'status':'unconfirmed','source_stage':source}
        self.store.put('findings',registry)
        return list(registry.values())

    def match(self, a, b, data, round_no, phase, baseline):
        label = f'r{round_no:02d}-{a}-{b}'
        stored = self.store.get('match:'+label)
        if stored:
            return stored
        sides = {'A':data[a],'B':data[b]}
        attacks = []
        for own, other in ((a,b),(b,a)):
            attacks.append(self.context(label+'-attack-'+own,'attack',phase,baseline,
                                        candidate=own,opponent=other,candidates=sides,
                                        findings=self.store.get('findings',{})))
        attack_results = self.wave(attacks)
        registry=self.store.get('findings',{})
        for attack_id, attack in attack_results.items():
            if any(identifier not in registry for identifier in attack['carry_forward']):
                raise NeedsReview('Cross-review references an unknown carry-forward finding')
            for index, issue in enumerate(attack['issues'],1):
                identifier=issue['finding_id']
                if identifier and identifier not in registry:
                    raise NeedsReview('Cross-review references an unknown finding')
                if not identifier:
                    identifier=f'{attack_id}-f{index:03d}'
                    registry[identifier]={'id':identifier,'title':issue['evidence'],
                        'severity':issue['severity'],'file':'(cross-review; see evidence)','line':1,
                        'evidence':issue['evidence'],'reproduction':issue['evidence'],
                        'recommendation':'Investigate and reproduce this cross-review issue',
                        'source':attack_id,'source_stage':'cross-review','status':'unconfirmed'}
                else:
                    reviews=registry[identifier].get('cross_reviews',{})
                    reviews[attack_id]=issue
                    registry[identifier]['cross_reviews']=reviews
        self.store.put('findings',registry)
        defenses = []
        for candidate, other in ((a,b),(b,a)):
            defenses.append(self.context(label+'-defend-'+candidate,'defend',phase,
                                         data[candidate]['path'] if phase=='code' else baseline,
                                         candidate=candidate,own=data[candidate],opponent=data[other],
                                         attack=attack_results[label+'-attack-'+other],
                                         findings=self.store.get('findings',{})))
        if phase == 'code':
            revised = self.edits([a,b],defenses)
        else:
            answers = self.wave(defenses)
            revised = {c:{'id':c,'report':answers[label+'-defend-'+c]} for c in (a,b)}
            self.registry({c:v['report'] for c,v in revised.items()},label)
        verdict = self.one(self.context(label+'-judge','judge',phase,baseline,
                                       candidates={'A':revised[a],'B':revised[b]},attacks=attack_results))
        allowed = [c for c in (a,b) if phase=='audit' or revised[c]['eligible']]
        if not allowed:
            raise NeedsReview(f'{label}: both candidates failed mandatory gates; no winner selected')
        weights = {'coverage':35,'correctness':30,'verification':20,'maintainability':15}
        totals = {a:0,b:0}
        for score in verdict['scores']:
            candidate = a if score['candidate']=='A' else b
            totals[candidate] = sum(score[k]*weight for k,weight in weights.items())/10
        winner = sorted(allowed,key=lambda c:(-totals[c],c))[0]
        record = {'winner':winner,'revised':revised,'scores':totals,'judge':verdict,'phase':phase,
                  'tie_break':'stable candidate ID','allowed':allowed}
        self.store.put('match:'+label,record)
        return record

    def execute(self, audit_only=False):
        if self.run['status']=='ready':
            return
        self.check_candidate_drift()
        self.run['status']='running'
        self.run.pop('reason',None)
        self.run['mode']='audit' if audit_only else 'run'
        self.save()
        baseline = self.tree()
        if vcs.git(baseline,'rev-parse','HEAD') != self.run['base_sha']:
            raise NeedsReview('Baseline HEAD changed')
        vcs.clean(baseline)
        if not audit_only and not any(c.get('required',True) for c in self.config['checks']):
            raise NeedsReview('At least one required external check is needed before editing')
        # Setup commands are explicit, bounded and run once per worktree before checks/agents.
        self.setup(baseline)
        baseline_results = self.stage_checks(baseline,'baseline')
        self.run['baseline_checks']=baseline_results
        self.save()
        agents = [f'c{i:02d}' for i in range(1,self.run['agents']+1)]
        contexts = [self.context('audit-'+c,'audit','audit',baseline,
                    lens=LENSES[index%16],strategy='reproduce failures first' if index<16 else 'trace invariants and adversarial inputs')
                    for index,c in enumerate(agents)]
        reports = self.wave(contexts)
        data = {c:{'id':c,'report':reports['audit-'+c]} for c in agents}
        findings = self.registry({c:v['report'] for c,v in data.items()},'initial')
        consolidation = self.one(self.context('consolidate','consolidate','audit',baseline,findings=findings))
        known_ids = set(self.store.get('findings',{}))
        if any(not set(group['ids']).issubset(known_ids) for group in consolidation['groups']):
            raise NeedsReview('Consolidation references nonexistent findings')
        self.store.put('groups',consolidation)
        round_no = 1
        while len(agents)>8:
            next_agents = []
            for a,b in zip(agents[::2],agents[1::2]):
                result = self.match(a,b,data,round_no,'audit',baseline)
                data.update(result['revised'])
                next_agents.append(result['winner'])
            agents=next_agents
            self.progress(f'Audit round {round_no}: {len(agents)} remain')
            round_no+=1
        if audit_only:
            self.run.update(status='audited',audit_finalists=agents)
            self.save()
            return
        contexts = []
        for candidate in agents:
            path = self.tree(candidate)
            self.setup(path)
            contexts.append(self.context('implement-'+candidate,'implement','code',path,
                                         candidate=candidate,plan=data[candidate]['report'],
                                         findings=self.store.get('findings',{}),baseline_checks=baseline_results))
        data.update(self.edits(agents,contexts))
        while len(agents)>1:
            next_agents = []
            for a,b in zip(agents[::2],agents[1::2]):
                result = self.match(a,b,data,round_no,'code',baseline)
                data.update(result['revised'])
                next_agents.append(result['winner'])
            agents=next_agents
            self.progress(f'Code round {round_no}: {len(agents)} remain')
            round_no+=1
        champion = data[agents[0]]
        final = self.one(self.context('final','final','code',baseline,candidate=champion,
                                      findings=self.store.get('findings',{}),baseline_checks=baseline_results))
        self.store.put('final',final)
        known_ids = set(self.store.get('findings',{}))
        if any(f['finding_id'] not in known_ids for f in final['findings']):
            raise NeedsReview('Final audit references nonexistent finding')
        self.run['champion']=champion
        if final['blocking_issues'] or not champion['eligible']:
            raise NeedsReview('Final audit found blockers; candidate retained for review')
        # Fresh final checks, separately from per-round cached evidence.
        final_checks = self.stage_checks(Path(champion['path']),'final-'+champion['sha'])
        if not eligible(final_checks,champion['changed_files'],self.config['protected_paths'],champion['added_files']):
            raise NeedsReview('Final external checks failed')
        self.run.update(status='ready',winner_branch=champion['branch'],winner_sha=champion['sha'],final_checks=final_checks)
        self.save()

    def setup(self, path):
        from .process import execute
        key = 'setup:'+str(path)
        if self.store.get(key):
            return
        for index, command in enumerate(self.config['setup']):
            before = vcs.snapshot(path)
            directory = self.store.directory/'setup'
            directory.mkdir(exist_ok=True)
            label = digest(str(path))[:12]+f'-{index}'
            result = execute(command['argv'],path,timeout=command.get('timeout',600),
                             stdout_path=directory/(label+'.stdout'),stderr_path=directory/(label+'.stderr'))
            if result['returncode'] or result['timeout']:
                raise NeedsReview(f'Setup failed for {path}; inspect setup logs')
            if vcs.snapshot(path)!=before:
                raise NeedsReview(f'Setup changed tracked/untracked sources: {path}')
        self.store.put(key,True)

    def report(self):
        self.run=self.store.get('run')
        jobs=self.store.jobs()
        champion=self.run.get('champion')
        winner=self.run.get('winner_branch') if self.run['status']=='ready' else None
        diff_path=None
        if champion:
            diff_path=str(self.store.directory/'final.diff')
            # Do not regenerate from a possibly drifted checkout; commits are immutable.
            diff=vcs.git(self.run['repo'],'diff','--binary',self.run['base_sha'],champion['sha'],raw=True)
            Path(diff_path).write_text(diff)
        final=self.store.get('final',{})
        findings=list(self.store.get('findings',{}).values())
        findings_by_id={f['id']:f for f in findings}
        for verification in final.get('findings',[]):
            if verification['finding_id'] in findings_by_id:
                findings_by_id[verification['finding_id']]['final_review']=verification
        counts={'raw':len(findings),'reviewed_by_final_auditor':0,'verified_fixed_by_final_review':0,
                'unresolved_by_final_review':0,'unconfirmed':0}
        for finding in findings:
            status=finding.get('final_review',{}).get('status','unconfirmed')
            if 'final_review' in finding:
                counts['reviewed_by_final_auditor']+=1
            if status=='verified_fixed':
                counts['verified_fixed_by_final_review']+=1
            elif status=='unresolved':
                counts['unresolved_by_final_review']+=1
            else:
                counts['unconfirmed']+=1
        report={'run_id':self.run['id'],'status':self.run['status'],'reason':self.run.get('reason'),
                'base_sha':self.run['base_sha'],'repo':self.run['repo'],
                'winner_branch':winner,'winner_sha':self.run.get('winner_sha') if winner else None,
                'candidate_for_review':champion,'diff_path':diff_path,
                'completed_model_jobs':sum(j['status']=='succeeded' for j in jobs),
                'model_attempts':sum(j['attempt'] for j in jobs),'usage':self.store.usage(),
                'findings':findings,'finding_counts':counts,'duplicate_groups':self.store.get('groups',{}),
                'change_summary':final.get('summary',champion.get('report',{}).get('summary','') if champion else ''),
                'baseline_checks':self.run.get('baseline_checks',{}),'final_checks':self.run.get('final_checks',{}),
                'final_review':final,'state_dir':str(self.store.directory),
                'limitations':['Code-return gates require every mandatory check to pass; no baseline-failure waiver.',
                               'Existing tests/config changes require manual review under protected_paths.',
                               'Finding fixes are independently model-reviewed, not automatically reproduced per finding.',
                               'Benchmarks are external commands; no statistical comparison engine.',
                               'Worktrees are not an OS isolation boundary.']}
        atomic_json(self.store.directory/'report.json',report)
        lines=['# Codex Arena',f'Status: {report["status"]}',f'Run: {report["run_id"]}',
               f'Base: {report["base_sha"]}',f'Winner: {winner or "none"}',
               f'Completed model jobs: {report["completed_model_jobs"]}',
               f'Raw tokens: {report["usage"]["raw_tokens"]}',
               f'Unknown usage attempts: {len(report["usage"]["unknown_attempts"])}',
               f'Findings (before deduplication): {len(findings)}',
               f'Fixed (independent model review): {counts["verified_fixed_by_final_review"]}',
               f'Unresolved (final review): {counts["unresolved_by_final_review"]}',
               f'Unconfirmed: {counts["unconfirmed"]}',
               f'Diff: {diff_path or "not available"}',f'Reason: {report["reason"] or "—"}',
               '\n## Checks\n','| Check | Baseline | Final |','| --- | --- | --- |']
        for name in sorted(set(report['baseline_checks'])|set(report['final_checks'])):
            lines.append(f'| {name} | {report["baseline_checks"].get(name,{}).get("status","not run")} | {report["final_checks"].get(name,{}).get("status","not run")} |')
        lines+=['\n## Final review\n',final.get('summary','Not run')]
        lines += ['- '+issue for issue in final.get('blocking_issues',[])]
        lines+=['\n## Findings\n']
        for finding in findings:
            verification=finding.get('final_review',{})
            lines.append(f'- {finding["id"]}: {finding["severity"]} — {finding["title"]} ({finding["file"]}:{finding["line"]}); {verification.get("status","unconfirmed")}')
        lines+=['\n## Limits\n']+['- '+line for line in report['limitations']]
        (self.store.directory/'report.md').write_text('\n\n'.join(lines)+'\n')
        return report
