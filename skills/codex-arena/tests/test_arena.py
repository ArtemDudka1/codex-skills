import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


class ArenaFixture:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'project with spaces'
        self.repo.mkdir()
        git(self.repo, 'init', '-b', 'main')
        git(self.repo, 'config', 'user.name', 'Test')
        git(self.repo, 'config', 'user.email', 'test@example.invalid')
        (self.repo / 'app.py').write_text('VALUE = 1\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'base')
        self.base = git(self.repo, 'rev-parse', 'HEAD')
        self.calls = self.root / 'calls.jsonl'
        self.fake = self.root / 'fake-codex'
        self.fake.write_text('''#!/usr/bin/env python3
import json, sys
from pathlib import Path
args = sys.argv[1:]
if '--help' in args:
    print('--json --output-schema --output-last-message --sandbox'); sys.exit()
if '--version' in args:
    print('fake-codex 1'); sys.exit()
context = json.loads(sys.stdin.read().split('ARENA_CONTEXT_JSON\\n')[1])
role = context['role']
with open(context['config']['call_log'], 'a') as f: f.write(json.dumps({'id':context['job_id'], 'role':role})+'\\n')
mode = context['config'].get('fake_mode', '')
if mode == 'fail': print('quota exhausted', file=sys.stderr); sys.exit(1)
if role == 'audit' or (role == 'defend' and context['phase'] == 'audit'):
    result = {'summary':'Audit', 'findings':[{'title':'Value is wrong','severity':'medium','file':'app.py','line':1,'evidence':'VALUE = 1','reproduction':'Read app.py','recommendation':'Use 2'}], 'plan':['Fix value']}
elif role == 'consolidate':
    result = {'summary':'All evidence preserved', 'groups':[]}
elif role == 'attack':
    result = {'summary':'Review', 'issues':[], 'carry_forward':[]}
elif role in ('implement', 'defend'):
    if mode != 'no_edit': Path('app.py').write_text('VALUE = 2\\n')
    result = {'summary':'Fixed value','addressed_ids':[], 'unresolved_ids':[]}
elif role == 'judge':
    result = {'summary':'Comparable candidates', 'scores':[{'candidate':n,'coverage':8,'correctness':8,'verification':8,'maintainability':8} for n in ['A','B']]}
else:
    result = {'summary':'Final review','blocking_issues':['Regression'] if mode == 'final_block' else [], 'findings':[]}
if mode == 'malformed': result = {'summary':'missing required fields'}
Path(args[args.index('-o')+1]).write_text(json.dumps(result))
print(json.dumps({'type':'thread.started','thread_id':'test-session'}))
if mode != 'unknown_usage': print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':60,'output_tokens':20}}))
''')
        self.fake.chmod(0o755)
        self.config = self.root / 'arena.json'
        self.settings = {'model':'test-model','codex_bin':str(self.fake), 'call_log':str(self.calls),
                         'concurrency':2, 'checks':[{'name':'tests','argv':[sys.executable,'-c',
                         'import app; assert app.VALUE in (1, 2)'],'required':True,'timeout':10}],
                         'job_reserve_tokens':100, 'soft_tokens':1000000, 'emergency_tokens':2000000}
        self.save_config()
        self.state = self.root / 'state'

    def save_config(self):
        self.config.write_text(json.dumps(self.settings))

    def cli(self, command, *args, ok=True):
        p = subprocess.run([sys.executable, '-m', 'codex_arena', command, str(self.repo),
                            '--state-dir', str(self.state), *args], cwd=ROOT, text=True, capture_output=True)
        if ok:
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def start(self, command='run', agents=2, ok=True):
        return self.cli(command, '--agents', str(agents), '--config', str(self.config), ok=ok)

    def report(self):
        return json.loads(self.cli('report', '--json').stdout)


class ArenaTests(ArenaFixture, unittest.TestCase):
    def test_full_32_tournament_preserves_main_and_resume_does_not_repeat(self):
        self.start(agents=32)
        report = self.report()
        self.assertEqual(report['status'], 'ready')
        self.assertEqual(report['completed_model_jobs'], 197)
        self.assertEqual(len(report['findings']), 32)
        self.assertEqual(report['finding_counts']['raw'],32)
        self.assertEqual(report['finding_counts']['verified_fixed_by_final_review'],0)
        self.assertEqual(report['usage']['raw_tokens'], 23640)
        self.assertEqual(git(self.repo,'rev-parse','HEAD'), self.base)
        self.assertEqual(git(self.repo,'branch','--show-current'), 'main')
        self.assertEqual((self.repo/'app.py').read_text(), 'VALUE = 1\n')
        self.assertEqual(git(self.repo,'status','--porcelain'), '')
        self.assertEqual(git(self.repo,'show', report['winner_branch']+':app.py'), 'VALUE = 2')
        count = len(self.calls.read_text().splitlines())
        self.cli('resume')
        self.assertEqual(len(self.calls.read_text().splitlines()), count)
        self.assertTrue(Path(report['diff_path']).exists())

    def test_audit_then_run_reuses_findings(self):
        self.start('audit', agents=4)
        self.assertEqual(self.report()['status'], 'audited')
        self.assertIsNone(self.report()['winner_branch'])
        self.cli('run')
        self.assertEqual(self.report()['status'], 'ready')
        rows = [json.loads(x) for x in self.calls.read_text().splitlines()]
        self.assertEqual(sum(r['role']=='audit' for r in rows),4)

    def test_dirty_repository_is_rejected_before_any_calls(self):
        (self.repo/'app.py').write_text('unsaved\n')
        self.assertNotEqual(self.start(ok=False).returncode, 0)
        self.assertFalse(self.calls.exists())

    def test_malformed_output_never_enters_bracket(self):
        self.settings['fake_mode']='malformed'; self.save_config()
        self.assertNotEqual(self.start(ok=False).returncode, 0)
        self.assertNotEqual(self.report()['status'], 'ready')
        self.assertIsNone(self.report()['winner_branch'])

    def test_unknown_usage_pauses_and_is_not_repeated(self):
        self.settings['fake_mode']='unknown_usage'; self.save_config()
        self.start(ok=False)
        self.assertEqual(self.report()['status'], 'paused')
        count = len(self.calls.read_text().splitlines())
        self.cli('resume', ok=False)
        self.assertEqual(len(self.calls.read_text().splitlines()), count)

    def test_budget_stops_before_dispatch(self):
        self.settings['soft_tokens']=99; self.save_config()
        self.start(ok=False)
        self.assertEqual(self.report()['status'], 'paused')
        self.assertFalse(self.calls.exists())

    def test_failed_checks_prevent_winner(self):
        self.settings['checks'][0]['argv']=[sys.executable,'-c','import app; assert app.VALUE == 1']
        self.save_config(); self.start(ok=False)
        self.assertEqual(self.report()['status'], 'needs-review')
        self.assertIsNone(self.report()['winner_branch'])

    def test_final_blocker_prevents_ready(self):
        self.settings['fake_mode']='final_block'; self.save_config()
        self.start(ok=False)
        self.assertEqual(self.report()['status'], 'needs-review')

    def test_missing_checks_prevents_editing(self):
        self.settings['checks']=[]; self.save_config()
        self.start(ok=False)
        self.assertNotEqual(self.report()['status'], 'ready')
        if self.calls.exists():
            self.assertNotIn('implement', self.calls.read_text())


class CoreTests(unittest.TestCase):
    def test_gate_requires_pass_and_protects_checks(self):
        from codex_arena.checks import eligible
        self.assertFalse(eligible({'tests':{'status':'failed'}}, []))
        self.assertFalse(eligible({'tests':{'status':'passed'}}, ['tests/test_app.py']))
        self.assertTrue(eligible({'tests':{'status':'passed'}}, ['app.py']))

    def test_schema_rejects_extra_fields_and_wrong_types(self):
        from codex_arena.schemas import validate, schema_for
        with self.assertRaises(ValueError):
            validate({'summary':'s','scores':[],'winner':'bad'}, schema_for('judge'))
        with self.assertRaises(ValueError):
            validate({'summary':'s','scores':[{'candidate':'A','coverage':True,'correctness':8,'verification':8,'maintainability':8}]}, schema_for('judge'))

    def test_check_timeout_kills_process(self):
        from codex_arena.process import execute
        with tempfile.TemporaryDirectory() as directory:
            result = execute([sys.executable,'-c','import time; time.sleep(20)'], Path(directory), timeout=.05)
            self.assertTrue(result['timeout'])

    def test_state_lock_and_artifact_recovery(self):
        from codex_arena.state import Store
        with tempfile.TemporaryDirectory() as directory:
            with Store(Path(directory)) as first:
                with self.assertRaises(RuntimeError):
                    with Store(Path(directory)): pass
                first.put('test', {'a':1})
            with Store(Path(directory)) as second:
                self.assertEqual(second.get('test'), {'a':1})


class RecoveryTests(ArenaFixture, unittest.TestCase):
    # Run focused contracts without inheriting the integration suite a second time.
    def test_completed_envelope_is_recovered_after_ledger_interruption(self):
        self.start('audit',agents=2)
        report=self.report()
        from codex_arena.state import Store
        with Store(Path(report['state_dir'])) as store:
            store.db.execute("UPDATE jobs SET status='running', result=NULL WHERE id='audit-c01'")
            store.db.commit()
        count=len(self.calls.read_text().splitlines())
        self.cli('resume')
        self.assertEqual(len(self.calls.read_text().splitlines()),count)
        self.assertEqual(self.report()['status'],'audited')

    def test_candidate_drift_blocks_resume_without_any_calls(self):
        self.start()
        report=self.report()
        from codex_arena.state import Store
        directory=Path(report['state_dir'])
        with Store(directory) as store:
            run=store.get('run'); run['status']='paused'; store.put('run',run)
        Path(report['candidate_for_review']['path'],'app.py').write_text('VALUE = 999\n')
        count=len(self.calls.read_text().splitlines())
        self.assertNotEqual(self.cli('resume',ok=False).returncode,0)
        self.assertEqual(len(self.calls.read_text().splitlines()),count)
        self.assertEqual(self.report()['status'],'needs-review')
        self.assertIsNone(self.report()['winner_branch'])

    def test_failed_readonly_call_has_unknown_usage_and_requires_reconciliation(self):
        self.settings['fake_mode']='fail'; self.save_config()
        self.start('audit',ok=False)
        report=self.report()
        self.assertTrue(report['usage']['unknown_attempts'])
        count=len(self.calls.read_text().splitlines())
        self.cli('resume',ok=False)
        self.assertEqual(len(self.calls.read_text().splitlines()),count)

    def test_new_run_required_for_changed_configuration(self):
        self.start('audit')
        self.settings['model']='another-model'; self.save_config()
        self.assertNotEqual(self.start('run',ok=False).returncode,0)

    def test_cli_plan_has_no_side_effects(self):
        result=json.loads(self.cli('plan','--agents','32','--json').stdout)
        self.assertEqual(result['base_model_jobs'],197)
        self.assertFalse(self.state.exists())
        self.assertFalse(self.calls.exists())

    def test_required_check_failure_is_recorded_with_evidence(self):
        self.settings['checks'][0]['argv']=[sys.executable,'-c','raise SystemExit(7)']
        self.save_config(); self.start(ok=False)
        report=self.report()
        self.assertEqual(report['status'],'needs-review')
        candidate_checks=[]
        from codex_arena.state import Store
        with Store(Path(report['state_dir'])) as store:
            candidate_checks=list(store.get('candidates',{}).values())
        self.assertTrue(candidate_checks)
        self.assertTrue(all(c['checks']['tests']['returncode']==7 for c in candidate_checks))
        self.assertTrue(all(Path(c['checks']['tests']['stderr_path']).exists() for c in candidate_checks))


    def test_crash_after_commit_is_recovered_without_repeating_editor(self):
        from unittest.mock import patch
        from codex_arena.state import Store
        from codex_arena.engine import Engine
        from codex_arena import git as vcs
        self.start('audit')
        directory=Path(self.report()['state_dir'])
        real_commit=vcs.commit
        def commit_then_crash(*args, **kwargs):
            real_commit(*args, **kwargs)
            raise KeyboardInterrupt()
        with Store(directory) as store:
            engine=Engine(store)
            with patch('codex_arena.engine.vcs.commit', side_effect=commit_then_crash):
                with self.assertRaises(KeyboardInterrupt):
                    engine.execute()
        before=[json.loads(x) for x in self.calls.read_text().splitlines()]
        self.cli('resume')
        self.assertEqual(self.report()['status'],'ready')
        after=[json.loads(x) for x in self.calls.read_text().splitlines()]
        self.assertEqual(sum(r['id']=='implement-c01' for r in after),1)

    def test_recovered_judge_must_still_score_both_sides(self):
        from codex_arena.state import Store, atomic_json, digest
        from codex_arena.adapter import prepare
        context={'job_id':'broken-judge','role':'judge','phase':'audit','cwd':str(self.repo)}
        with Store(self.root/'ledger') as store:
            store.start('broken-judge',digest(context))
            directory=store.directory/'jobs'/'broken-judge'; directory.mkdir(parents=True,exist_ok=True)
            result={'summary':'invalid judge','scores':[]}
            atomic_json(directory/'0001.envelope.json',{
                'fingerprint':digest(context),'result':result,'result_hash':digest(result),
                'usage':{'input_tokens':100,'output_tokens':1},'returncode':0,'valid':True})
            with self.assertRaises((ValueError,RuntimeError)):
                prepare(store,self.settings,context)

    def test_live_worker_cannot_be_retried(self):
        from codex_arena.state import Store, atomic_json, digest
        from codex_arena.adapter import prepare
        import subprocess
        context={'job_id':'live-audit','role':'audit','phase':'audit','cwd':str(self.repo)}
        with Store(self.root/'ledger') as store:
            store.start('live-audit',digest(context))
            directory=store.directory/'jobs'/'live-audit'; directory.mkdir(parents=True,exist_ok=True)
            birth=subprocess.check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True).strip()
            atomic_json(directory/'0001.process.json',{'pid':os.getpid(),'birth':birth})
            with self.assertRaises(RuntimeError):
                prepare(store,self.settings,context,retry=True)

    def test_mutating_checks_do_not_leave_reusable_pass_records(self):
        from codex_arena.state import Store
        from codex_arena.checks import run_checks
        marker=self.root/'mutated-once'
        script=("from pathlib import Path; marker=Path("+repr(str(marker))+"); "
                "p=Path('app.py'); first=not marker.exists(); "
                "p.write_text('VALUE = 2\\n') if first else None; marker.touch()")
        commands=[{'name':'mutate','argv':[sys.executable,'-c',script]},
            {'name':'test','argv':[sys.executable,'-c','import app; assert app.VALUE == 2']}]
        with Store(self.root/'ledger') as store:
            with self.assertRaises(RuntimeError):
                run_checks(store,self.repo,commands,'batch')
            # Identical commands and original snapshot: only the first execution mutates.
            (self.repo/'app.py').write_text('VALUE = 1\n')
            result=run_checks(store,self.repo,commands,'batch')
            self.assertEqual(result['test']['status'],'failed')

    def test_incomplete_attempt_remains_unknown_in_usage(self):
        from codex_arena.state import Store, digest
        from codex_arena.adapter import prepare
        from codex_arena.config import load
        context={'job_id':'pending-audit','role':'audit','phase':'audit','cwd':str(self.repo),'reasoning':'medium'}
        with Store(self.root/'ledger') as store:
            prepare(store,load(self.config),context)
            self.assertEqual(len(store.usage()['unknown_attempts']),1)

    def test_test_runner_configuration_changes_cannot_win(self):
        from codex_arena.checks import eligible
        for path in ['conftest.py','src/conftest.py','pytest.ini','tox.ini','setup.cfg','Makefile']:
            with self.subTest(path=path):
                self.assertFalse(eligible({'tests':{'status':'passed'}},[path]))

    def test_additional_tests_are_allowed_but_existing_tests_are_protected(self):
        from codex_arena.checks import eligible
        checks={'tests':{'status':'passed'}}
        self.assertTrue(eligible(checks,['tests/test_regression.py'],added_files=['tests/test_regression.py']))
        self.assertFalse(eligible(checks,['tests/test_existing.py']))
        self.assertFalse(eligible(checks,['conftest.py'],added_files=['conftest.py']))

    def test_interrupted_editor_retry_preserves_backup_and_completes(self):
        self.settings['fake_mode']='malformed_edit'; self.save_config()
        text=self.fake.read_text().replace("if mode == 'malformed': result", "if mode == 'malformed' or (mode == 'malformed_edit' and role == 'implement'): result")
        self.fake.write_text(text)
        self.start(ok=False)
        report=self.report()
        count=len(self.calls.read_text().splitlines())
        self.assertEqual(report['status'],'paused')
        self.fake.write_text(text.replace("mode == 'malformed_edit' and role == 'implement'", "False"))
        self.cli('resume','--retry-interrupted',ok=True)
        self.assertEqual(self.report()['status'],'ready')
        refs=git(self.repo,'for-each-ref','--format=%(refname:short)','refs/heads/arena/').splitlines()
        backups=[r for r in refs if '/recovery-' in r]
        self.assertEqual(len(backups),2)
        self.assertEqual(git(self.repo,'show',backups[0]+':app.py'),'VALUE = 2')

    def test_explicit_usage_reconciliation_unblocks_next_stage(self):
        self.settings['fake_mode']='unknown_usage'; self.save_config()
        self.start('audit',ok=False)
        report=self.report()
        for path in report['usage']['unknown_attempts']:
            self.cli('reconcile-usage','--attempt',path,'--input-tokens','100','--output-tokens','20')
        self.fake.write_text(self.fake.read_text().replace("if mode != 'unknown_usage':", 'if True:'))
        count=len(self.calls.read_text().splitlines())
        self.cli('resume')
        self.assertEqual(self.report()['status'],'audited')
        self.assertEqual(len(self.calls.read_text().splitlines()), count+1)

    def test_cancellation_stops_a_long_running_command(self):
        import threading
        from codex_arena.process import execute
        cancel=threading.Event()
        timer=threading.Timer(.05,cancel.set)
        timer.start()
        try:
            result=execute([sys.executable,'-c','import time; time.sleep(20)'],self.repo,
                           timeout=30,cancel_event=cancel)
        finally:
            timer.cancel()
        self.assertTrue(result['cancelled'])
        self.assertLess(result['seconds'],3)

    def test_known_failed_response_is_not_imported_as_success(self):
        from codex_arena.state import Store, atomic_json, digest
        from codex_arena.adapter import prepare
        context={'job_id':'failed-judge','role':'judge','phase':'audit','cwd':str(self.repo)}
        result={'summary':'verdict','scores':[{'candidate':n,'coverage':8,'correctness':8,'verification':8,'maintainability':8} for n in ['A','B']]}
        with Store(self.root/'ledger') as store:
            store.start('failed-judge',digest(context))
            directory=store.directory/'jobs'/'failed-judge'
            atomic_json(directory/'0001.response.json',result)
            (directory/'0001.events.jsonl').write_text(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'output_tokens':10}})+'\n')
            atomic_json(directory/'0001.envelope.json',{'fingerprint':digest(context),'valid':False,
                'returncode':1,'result':None,'usage':{'input_tokens':100,'output_tokens':10}})
            store.fail('failed-judge','CLI failed')
            with self.assertRaises(RuntimeError):
                prepare(store,self.settings,context)
            self.assertEqual(store.job('failed-judge')['status'],'interrupted')

    def test_check_stage_is_bound_to_the_actual_revision(self):
        from codex_arena.state import Store
        from codex_arena.engine import Engine
        self.start('audit')
        directory=Path(self.report()['state_dir'])
        with Store(directory) as store:
            engine=Engine(store)
            tree=engine.tree('freshness-test')
            good=engine.stage_checks(tree,'same-stage')
            self.assertEqual(good['tests']['status'],'passed')
            (tree/'app.py').write_text('VALUE = 999\n')
            from codex_arena import git as vcs
            sha=vcs.commit(tree,'break value')
            bad=engine.stage_checks(tree,'same-stage')
            self.assertEqual(bad['tests']['sha'],sha)
            self.assertEqual(bad['tests']['status'],'failed')

    def test_cross_review_findings_survive_elimination(self):
        text=self.fake.read_text().replace("result = {'summary':'Review', 'issues':[], 'carry_forward':[]}",
            "result = {'summary':'Review', 'issues':[{'severity':'medium','evidence':'app.py:1 requires more cases','finding_id':''}], 'carry_forward':[]}")
        self.fake.write_text(text)
        self.start()
        findings=self.report()['findings']
        self.assertEqual(len(findings),4)
        self.assertEqual(sum(f['source_stage']=='cross-review' for f in findings),2)

    def test_budget_pause_does_not_create_an_unstarted_unknown_attempt(self):
        self.settings['soft_tokens']=150; self.settings['job_reserve_tokens']=100
        self.save_config(); self.start('audit',ok=False)
        report=self.report()
        self.assertEqual(report['status'],'paused')
        self.assertEqual(report['usage']['unknown_attempts'],[])
        self.assertFalse(self.calls.exists())

    def test_exported_diff_is_an_applicable_patch_with_blank_context(self):
        (self.repo/'app.py').write_text('VALUE = 1\n\n\n')
        git(self.repo,'add','app.py'); git(self.repo,'commit','-qm','add blank context')
        self.fake.write_text(self.fake.read_text().replace("write_text('VALUE = 2\\n')", "write_text('VALUE = 2\\n\\n\\n')"))
        self.start()
        diff=self.report()['diff_path']
        check=subprocess.run(['git','-C',str(self.repo),'apply','--check',diff],text=True,capture_output=True)
        self.assertEqual(check.returncode,0,check.stderr)


if __name__ == '__main__':
    unittest.main()
