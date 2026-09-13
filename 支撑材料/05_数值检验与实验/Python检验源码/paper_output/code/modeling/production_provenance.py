"""Small, auditable provenance and publication helpers; no model computation.

The worker owns one immutable version directory. Only its supervising parent
may publish, after observing exit code zero and validating input/output hashes.
Publication temporarily invalidates the global manifest, writes the contracts,
checks their bytes, and commits the manifest last. Previous files are retained
for rollback. The optional selfcheck uses an isolated fixture workspace.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

SOURCE = Path(__file__).resolve()
ROOT = SOURCE.parents[3]
LOADED_CODE_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def within(root, path):
    root, path = Path(root).resolve(), Path(path).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Path is outside the intended workspace: ' + str(path))
    return path


def file_record(path, root=ROOT):
    path = within(root, path)
    before = path.stat()
    digest = sha256(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError('File changed while hashing: ' + str(path))
    return {'path': path.relative_to(Path(root).resolve()).as_posix(),
            'bytes': after.st_size, 'sha256': digest, 'exists': True}


def assert_records(records, root=ROOT):
    for expected in records:
        path = within(root, Path(root) / expected['path'])
        actual = file_record(path, root)
        for key in ('sha256', 'bytes'):
            if key in expected and actual[key] != expected[key]:
                raise RuntimeError('Artifact/input changed: ' + expected['path'])


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_json(path, value):
    atomic_bytes(path, json_bytes(value))


def exclusive_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def runtime_record():
    versions = {}
    for name in ('numpy', 'scipy', 'openpyxl', 'matplotlib'):
        versions[name] = importlib.metadata.version(name)
    return {'executable': sys.executable, 'implementation': platform.python_implementation(),
            'version': platform.python_version(), 'platform': platform.platform(),
            'installed_library_versions': versions,
            'thread_environment': {name: os.environ.get(name) for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')},
            'scope': 'Installed distributions; actual imported module paths are recorded by worker.'}


def pointer(document, json_pointer):
    current = document
    if not json_pointer.startswith('/'):
        raise ValueError('Expected an absolute JSON pointer')
    for token in json_pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def validate_metric_evidence(metrics, root=ROOT):
    cache = {}
    for metric in metrics:
        path = within(root, Path(root) / metric['evidence_path'])
        if path not in cache:
            cache[path] = json.loads(path.read_text(encoding='utf-8'))
        actual = pointer(cache[path], metric['evidence_json_pointer'])
        if actual != metric['value']:
            raise ValueError('Metric does not equal its saved evidence: ' + metric['metric_name'])
    return {'status': 'PASS', 'checked_metric_count': len(metrics),
            'scope': 'Exact equality to the identified saved JSON value, not physical accuracy.'}


def figure_artifact_records(figure, root=ROOT):
    candidates = []
    primary = figure.get('path') or figure.get('output_path')
    if primary:
        candidates.append({key: figure[key] for key in ('path', 'bytes', 'sha256') if key in figure}
                          if figure.get('path') else {'path': primary})
    artifacts = figure.get('artifacts', {})
    candidates.extend(artifacts.values() if isinstance(artifacts, dict) else artifacts)
    for name in ('plot_data', 'metadata'):
        if isinstance(figure.get(name), dict) and figure[name].get('path'):
            candidates.append(figure[name])
    checked = {}
    for expected in candidates:
        if not isinstance(expected, dict) or not expected.get('path'):
            raise ValueError('Invalid figure artifact record')
        actual = file_record(Path(root) / expected['path'], root)
        if not actual['bytes']:
            raise ValueError('Empty figure artifact: ' + actual['path'])
        if expected.get('sha256') and actual['sha256'] != expected['sha256']:
            raise RuntimeError('Existing figure hash mismatch: ' + actual['path'])
        checked[actual['path']] = actual
    if not checked:
        raise ValueError('Computed figure has no usable artifact')
    return list(checked.values())


def merge_figure_index(existing, new_figures, root=ROOT):
    merged, omitted, replaced, preserved = {}, [], [], []
    for figure in (existing or {}).get('figures', []):
        status = str(figure.get('status', '')).lower()
        if (figure.get('placeholder') or figure.get('planned') or
                status in ('planned', 'pending', 'not_started') or figure.get('ok') is False):
            omitted.append({'figure_id': figure.get('figure_id'), 'reason': 'not an existing usable computed figure'})
            continue
        figure_artifact_records(figure, root)
        if not figure.get('figure_id'):
            raise ValueError('Existing computed figure needs figure_id')
        merged[figure['figure_id']] = copy.deepcopy(figure)
        preserved.append(figure['figure_id'])
    seen = set()
    for figure in new_figures:
        identity = figure['figure_id']
        if identity in seen:
            raise ValueError('Duplicate new figure_id: ' + identity)
        seen.add(identity)
        figure_artifact_records(figure, root)
        if identity in merged:
            replaced.append(identity)
        merged[identity] = copy.deepcopy(figure)
    return list(merged.values()), {'preserved_existing_ids': [v for v in preserved if v not in replaced],
        'replaced_same_ids': replaced, 'omitted_noncomputed_entries': omitted,
        'prior_index_retained_in_publication_backup': True}


@contextmanager
def publication_lock(root, run_id):
    path = within(root, Path(root) / 'paper_output/results/.production_publish.lock')
    identity = {'run_id': run_id, 'pid': os.getpid(), 'created_at': utc_now(), 'token': uuid.uuid4().hex}
    exclusive_json(path, identity)
    try:
        yield
    finally:
        if path.exists() and json.loads(path.read_text(encoding='utf-8')) == identity:
            path.unlink()


def publish_transaction(root, directory, updates, manifest):
    """Caller holds publication_lock and has verified an actual worker exit 0.

    Updates maps root-relative JSON paths to their final documents. The old
    global manifest is invalidated before any contract changes; it is restored
    on rollback. Only the final manifest constitutes committed publication.
    """
    root, directory = Path(root).resolve(), within(root, directory)
    if manifest['runs'][0]['returncode'] != 0:
        raise ValueError('Cannot publish a nonzero worker return code')
    manifest_name = 'paper_output/results/run_manifest.json'
    if manifest_name in updates:
        raise ValueError('The manifest must be committed last')
    paths = [*updates, manifest_name]
    previous = {}
    backup = directory / 'publication_previous'
    for relative in paths:
        target = within(root, root / relative)
        previous[relative] = target.read_bytes() if target.exists() else None
        if previous[relative] is not None:
            atomic_bytes(backup / relative, previous[relative])
    write_json(backup / 'inventory.json', {'saved_at': utc_now(),
        'files': [{'path': p, 'previously_existed': b is not None} for p, b in previous.items()]})
    intended = {relative: json_bytes(document) for relative, document in updates.items()}
    changed = False
    try:
        # Readers must require PASS and the recorded hashes, never just the
        # existence of model_results.json or an old workflow-memory status.
        write_json(root / manifest_name, {'status': 'PUBLISHING', 'run_id': manifest['runs'][0]['run_id'],
            'generated_at': utc_now(), 'version_directory': directory.relative_to(root).as_posix()})
        changed = True
        for relative, content in intended.items():
            atomic_bytes(root / relative, content)
        for relative, content in intended.items():
            if sha256(root / relative) != hashlib.sha256(content).hexdigest():
                raise RuntimeError('Published contract bytes differ: ' + relative)
        # This is an actual read of every listed output, including global copies.
        assert_records(manifest['runs'][0]['output_artifacts'], root)
        assert_records(manifest['runs'][0].get('input_files', []), root)
        font = manifest['runs'][0].get('font')
        if font and sha256(font['path']) != font['sha256']:
            raise RuntimeError('Font changed before publication commit')
        write_json(directory / 'run_manifest.json', manifest)
        write_json(root / manifest_name, manifest)
    except Exception as error:
        rollback_errors = []
        if changed:
            # Restore the manifest after the other files, so no old PASS is
            # visible while its old contracts are still being restored.
            for relative in updates:
                try:
                    target = root / relative
                    if previous[relative] is None:
                        if target.exists():
                            target.unlink()
                    else:
                        atomic_bytes(target, previous[relative])
                except Exception as rollback_error:
                    rollback_errors.append({'path': relative, 'error': repr(rollback_error)})
            if not rollback_errors:
                try:
                    target = root / manifest_name
                    if previous[manifest_name] is None:
                        if target.exists():
                            target.unlink()
                    else:
                        atomic_bytes(target, previous[manifest_name])
                except Exception as rollback_error:
                    rollback_errors.append({'path': manifest_name, 'error': repr(rollback_error)})
        if rollback_errors:
            write_json(root / manifest_name, {'status': 'FAILED_PUBLICATION', 'error': repr(error),
                'rollback_errors': rollback_errors, 'generated_at': utc_now()})
        write_json(directory / 'publication_failure.json', {'status': 'FAIL', 'error': repr(error),
            'rollback_errors': rollback_errors, 'prior_publication_restored': changed and not rollback_errors,
            'generated_at': utc_now()})
        raise


def measured_process(command, cwd, log_path):
    """Observe a real child exit; preserve its complete merged stdout/stderr."""
    started = utc_now()
    stream_error = None
    with Path(log_path).open('x', encoding='utf-8') as log:
        process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='replace')
        try:
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(line, end='', flush=True)
        except BaseException as error:
            stream_error = error
            # Keep draining the child pipe so a log/console error cannot leave
            # it blocked on a full stdout buffer while the parent waits.
            for unused in process.stdout:
                pass
        finally:
            # The parent must not release publication responsibility while an
            # unobserved child is still writing. No child is killed here.
            code = process.wait()
            process.stdout.close()
    result = {'pid': process.pid, 'returncode': code, 'started_at': started,
              'finished_at': utc_now(), 'command': subprocess.list2cmdline(command),
              'argv': command, 'cwd': str(Path(cwd).resolve())}
    if stream_error is not None:
        result['stdout_capture_error'] = repr(stream_error)
    # Preserve an observed exit even if forwarding output failed and the caller
    # will raise instead of receiving this function's return value.
    write_json(Path(log_path).with_name('process_result.json'), result)
    if stream_error is not None:
        raise RuntimeError('Child exited, but stdout capture failed') from stream_error
    return result


def entry_sequence_selfcheck(directory):
    """Tiny injected services verify lifetime/ownership; no PDE is solved."""
    from types import SimpleNamespace
    from unittest.mock import patch
    import numpy as np
    import run_modeling as entry

    source = file_record(entry.SOURCE)
    start = {'input_files': [source], 'runtime': {}, 'font': {}, 'worker_command': 'fixture only; no model solve'}
    global_paths = [ROOT / p for p in entry.CONTRACT_TARGETS.values()]
    global_before = {str(p): sha256(p) if p.exists() else None for p in global_paths}
    active, events, identities = set(), [], {}
    class FixtureRun:
        def __init__(self, name, intervals):
            if active:
                raise AssertionError('Two Runs are retained simultaneously')
            self.name, self.intervals = name, intervals
            self.end_s = 1800. if name == 'Q1' else 15002.
            active.add(id(self))
            events.append('solve:' + name)
        def fields(self, times, material_x):
            shape = (len(times), len(material_x))
            return np.full(shape, 310.), np.full(shape, .1499)
        def close(self):
            events.append('close:' + self.name)
            active.remove(id(self))
    def save_fixture(run, output):
        return {'settings': {'intervals': run.intervals},
                'diagnostics': {'max_mass_balance_abs_kg_per_kg': 0.}}
    def fixture_completion(run):
        return {'reported_time_s': 15000.12, 'reported_drying_time_h': 15000.12 / 3600.,
                'critical_event_h': 15000. / 3600., 'max_C_at_reported_time': .1499}
    def export_fixture(run, qid, output):
        events.append('export:' + qid)
        identities[qid] = id(run)
        path = output / (qid + '_fixture.json')
        write_json(path, {'fixture_only': True, 'qid': qid})
        return {'question_id': qid, 'artifacts': [file_record(path)], 'size': {},
                'manifest_path': str(path)}
    def validate_fixture(exports, runs):
        export = exports[0]
        path = Path(export['manifest_path']).with_suffix('.validation.json')
        write_json(path, {'fixture_only': True})
        return {'status': 'PASS', 'fully_verified_with_live_Run': True, 'exports': [{'report_path': str(path)}]}
    def plot_fixture(run, qid, output):
        events.append('plot:' + qid)
        path = output / (qid + '_fixture.bin')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixture bytes; not a scientific figure')
        return {'figure_id': 'fixture_' + qid, 'question_id': qid, **file_record(path)}
    mappings = {'drying_core': SimpleNamespace(ROOT=ROOT, save_run=save_fixture),
        'q3_model': SimpleNamespace(completion=fixture_completion),
        'export_outputs': SimpleNamespace(export_question=export_fixture, validate_exports=validate_fixture),
        'publication_plots': SimpleNamespace(make_question_plot=plot_fixture)}
    for key, name in [('Q1', 'q1_model'), ('Q23', 'q2_model'), ('Q4', 'q4_model')]:
        mappings[name] = SimpleNamespace(solve=lambda n, key=key: FixtureRun(key, n))
    original_import = importlib.import_module
    def importer(name, *args, **kwargs):
        return mappings[name] if name in mappings else original_import(name, *args, **kwargs)
    args = SimpleNamespace(version='fixture_sequence', n1=2, n23=2, n4=2, review=False)
    with patch.object(entry, 'assert_dependencies'), patch.object(entry, 'imported_model_records', return_value=[]), \
            patch.object(entry.importlib, 'import_module', side_effect=importer):
        entry.worker(args, directory / 'entry_fixture_success', start)
        assert not active and identities['Q2'] == identities['Q3']
        assert events == ['solve:Q1', 'export:Q1', 'plot:Q1', 'close:Q1',
            'solve:Q23', 'export:Q2', 'plot:Q2', 'export:Q3', 'plot:Q3', 'close:Q23',
            'solve:Q4', 'export:Q4', 'plot:Q4', 'close:Q4']
        def fail_q3(run, qid, output):
            if qid == 'Q3':
                raise RuntimeError('injected fixture Q3 export failure')
            return export_fixture(run, qid, output)
        mappings['export_outputs'].export_question = fail_q3
        try:
            entry.worker(args, directory / 'entry_fixture_failure', start)
        except RuntimeError as error:
            assert 'injected fixture' in str(error)
        else:
            raise AssertionError('Fixture failure was not propagated')
        assert not active and events[-1] == 'close:Q23'
    global_after = {str(p): sha256(p) if p.exists() else None for p in global_paths}
    assert global_after == global_before
    return ['entry_one_run_at_a_time_and_Q2_Q3_same_identity',
            'entry_closes_run_after_export_failure', 'worker_does_not_publish_global_contracts']


def selfcheck():
    """Exercise failure paths on tiny files and real exit-0/exit-7 subprocesses."""
    import tempfile
    from unittest.mock import patch

    base = ROOT / 'notes/A-modeling/2026-09-10/data/production_entry_contract_selfcheck'
    base.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='check-', dir=base))
    fixture = directory / 'fixture'
    fixture.mkdir()
    checks = []
    original = fixture / 'input.txt'
    original.write_text('observed bytes', encoding='utf-8')
    rec = file_record(original, fixture)
    assert_records([rec], fixture)
    original.write_text('changed bytes', encoding='utf-8')
    try:
        assert_records([rec], fixture)
    except RuntimeError:
        checks.append('hash_mutation_rejected')
    else:
        raise AssertionError('Changed input was accepted')
    lock = fixture / 'launch.json'
    exclusive_json(lock, {'version': 'one'})
    try:
        exclusive_json(lock, {'version': 'two'})
    except FileExistsError:
        checks.append('duplicate_version_marker_rejected')
    else:
        raise AssertionError('Existing marker overwritten')
    evidence = fixture / 'summary.json'
    write_json(evidence, {'metric_samples': {'Q3': {'C': [[.1499]], 'time_s': 123.48}}})
    metric = {'metric_name': 'center_C', 'evidence_path': 'summary.json',
        'evidence_json_pointer': '/metric_samples/Q3/C/0/0', 'value': .1499}
    validate_metric_evidence([metric], fixture)
    metric['value'] = .1
    try:
        validate_metric_evidence([metric], fixture)
    except ValueError:
        checks.append('metric_mismatch_rejected')
    else:
        raise AssertionError('Wrong evidence accepted')
    image_path = fixture / 'observed.png'
    image_path.write_bytes(b'fixture-artifact-only-not-a-real-figure')
    figure = {'figure_id': 'observed', 'path': 'observed.png', 'status': 'computed',
              'sha256': sha256(image_path), 'placeholder': False}
    merged, note = merge_figure_index({'figures': [figure, {'figure_id': 'planned', 'planned': True}]}, [], fixture)
    assert len(merged) == 1 and note['preserved_existing_ids'] == ['observed']
    checks.append('existing_artifact_preserved_planned_not_promoted')
    old_contract = {'generation': 'old'}
    write_json(fixture / 'paper_output/results/model_results.json', old_contract)
    write_json(fixture / 'paper_output/results/run_manifest.json', {'status': 'PASS', 'old': True})
    version = fixture / 'paper_output/results/production/test'
    version.mkdir(parents=True)
    updates = {'paper_output/results/model_results.json': {'generation': 'new'}}
    intended_bytes = json_bytes(updates['paper_output/results/model_results.json'])
    intended_record = {'path': 'paper_output/results/model_results.json', 'bytes': len(intended_bytes),
                       'sha256': hashlib.sha256(intended_bytes).hexdigest()}
    manifest = {'status': 'PASS', 'runs': [{'run_id': 'test', 'returncode': 0,
        'input_files': [file_record(original, fixture)], 'output_artifacts': [intended_record]}]}
    real_write = atomic_bytes
    fired = False
    def fail_contract_once(path, data):
        nonlocal fired
        if Path(path) == fixture / 'paper_output/results/model_results.json' and not fired:
            fired = True
            raise OSError('injected fixture publication failure')
        real_write(path, data)
    with patch.object(sys.modules[__name__], 'atomic_bytes', fail_contract_once):
        try:
            publish_transaction(fixture, version, updates, manifest)
        except OSError:
            pass
        else:
            raise AssertionError('Injected failure was swallowed')
    assert json.loads((fixture / 'paper_output/results/model_results.json').read_text()) == old_contract
    assert json.loads((fixture / 'paper_output/results/run_manifest.json').read_text()) == {'status': 'PASS', 'old': True}
    checks.append('publication_failure_rolls_back_old_contract_and_manifest')
    publish_transaction(fixture, version, updates, manifest)
    assert json.loads((fixture / 'paper_output/results/model_results.json').read_text()) == {'generation': 'new'}
    checks.append('successful_publication_commits_manifest_last')
    exits = [measured_process([sys.executable, '-c', 'import sys; print("tiny-process"); sys.exit(' + str(code) + ')'],
                             fixture, directory / ('exit-' + str(code) + '.log')) for code in (0, 7)]
    assert [p['returncode'] for p in exits] == [0, 7]
    checks.append('actual_process_zero_and_nonzero_exits_observed')
    checks.extend(entry_sequence_selfcheck(directory))
    report = {'status': 'PASS', 'scope': 'Isolated tiny-file contracts; no model solve or real production publication.',
        'checks': checks, 'processes': exits, 'source': file_record(SOURCE), 'generated_at': utc_now(),
        'visual_studio_gui': 'pending', 'human_review': 'pending'}
    write_json(directory / 'selfcheck.json', report)
    print(json.dumps({'status': report['status'], 'checks': len(checks), 'report': str(directory / 'selfcheck.json')}))


if __name__ == '__main__':
    if sys.argv[1:] != ['--selfcheck']:
        raise SystemExit('Use --selfcheck for isolated contract validation only')
    if Path.cwd().resolve() != ROOT:
        raise SystemExit('Use the competition workspace as cwd')
    selfcheck()
