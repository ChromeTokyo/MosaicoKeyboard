#!/usr/bin/env python3
"""Review the recovered proposal in temporary copies; never run main's generator.

Print a JSON evidence record to stdout. All generator writes and injected faults
remain in a TemporaryDirectory. Assertions describe observations, not acceptance.
"""
import csv
import hashlib
import io
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RECOVERY = json.loads((HERE / 'RECOVERY.json').read_text())
OUTPUTS = ('mosaico-dock-schematic.json', 'mosaico-dock-placement.json',
           'design-netlist.json', 'bom-review.csv', 'pin-net-review.csv')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {str(p.relative_to(root)): digest(p)
            for directory in ('design', 'references')
            for p in sorted((root / directory).rglob('*')) if p.is_file()}


def output_hashes(root):
    return {name: digest(root / name) for name in OUTPUTS}


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    authority_before = snapshot(REPO)
    result = {'input_commit': RECOVERY['main_at_claim'],
              'candidate_commit': RECOVERY['source_commit'],
              'python': platform.python_version(), 'checks': []}
    for entry in RECOVERY['files']:
        saved = HERE / entry['saved_path']
        assert digest(saved) == entry['sha256']
        source = subprocess.check_output(
            ['git', 'show', RECOVERY['source_commit'] + ':' + entry['source_path']], cwd=REPO)
        assert saved.read_bytes() == source
    result['candidate_source_bytes_match'] = True

    with tempfile.TemporaryDirectory(prefix='mosaico-t18-review-') as temporary:
        scratch = Path(temporary)
        template = scratch / 'template'
        archive = subprocess.check_output(
            ['git', 'archive', RECOVERY['main_at_claim'], 'design', 'references'], cwd=REPO)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for entry in tar.getmembers():
                path = Path(entry.name)
                assert not path.is_absolute() and '..' not in path.parts
                if entry.isdir():
                    continue
                assert entry.isfile(), 'Review fixture requires ordinary files'
                dest = template / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(tar.extractfile(entry).read())
        for entry in RECOVERY['files']:
            shutil.copyfile(HERE / entry['saved_path'], template / entry['source_path'])
        result['isolated_input_sha256'] = snapshot(template)

        def fresh(name):
            return Path(shutil.copytree(template, scratch / name))

        def run(root, *args, optimized=False):
            command = [sys.executable] + (['-O'] if optimized else [])
            command += ['design/build_design.py', *args]
            proc = subprocess.run(command, cwd=root, capture_output=True, text=True)
            return {'args': list(args), 'optimized': optimized, 'exit_code': proc.returncode,
                    'stdout': proc.stdout.replace(str(scratch), '<TEMP>'),
                    'stderr': proc.stderr.replace(str(scratch), '<TEMP>')}

        def add(name, **facts):
            result['checks'].append({'name': name, **facts})

        baseline = fresh('baseline_guard')
        before = snapshot(baseline)
        observed = run(baseline)
        assert observed['exit_code'] == 2 and snapshot(baseline) == before
        add('default_baseline_write_rejected', run=observed, inputs_unchanged=True)

        strict = fresh('strict')
        observed = run(strict, '--out-dir', 'out')
        assert observed['exit_code'] == 1 and 'R26' in observed['stderr']
        assert not (strict / 'out').exists()
        add('unresolved_R26_blocks_normal_generation', run=observed, no_outputs=True)

        research = fresh('research')
        runs = [run(research, '--out-dir', name, '--allow-missing', optimized=optimized)
                for name, optimized in (('out1', False), ('out2', False), ('optimized', True))]
        assert all(r['exit_code'] == 0 for r in runs)
        hashes = output_hashes(research / 'out1')
        assert hashes == output_hashes(research / 'out2') == output_hashes(research / 'optimized')
        assert hashes == output_hashes(REPO / 'review/claude/T18/regenerated')
        add('research_outputs_reproducible', runs=runs, sha256=hashes,
            matches_claude_checked_in_comparison=True, also_matches_python_optimized=True)

        missing = fresh('missing_cache')
        (missing / 'references/C45783.json').unlink()
        observed = run(missing, '--out-dir', 'out', '--allow-missing')
        assert observed['exit_code'] == 1 and 'C45783' in observed['stderr']
        assert not (missing / 'out').exists()
        add('cache_removal_blocked_even_with_allow_missing', run=observed, no_outputs=True)

        changed = fresh('changed_cache')
        cache = changed / 'references/C25804.json'
        cache.write_bytes(cache.read_bytes() + b'\n')
        observed = run(changed, '--out-dir', 'out', '--allow-missing')
        assert observed['exit_code'] == 1 and 'C25804' in observed['stderr']
        assert not (changed / 'out').exists()
        add('cache_hash_change_blocked', run=observed, no_outputs=True)

        absent = fresh('missing_policy_entry')
        path = absent / 'design/library-policy.json'
        policy = json.loads(path.read_text())
        policy['entries'] = [e for e in policy['entries'] if e['refdes'] != 'U3']
        write_json(path, policy)
        observed = run(absent, '--out-dir', 'out', '--allow-missing')
        assert observed['exit_code'] == 1 and 'U3' in observed['stderr']
        assert not (absent / 'out').exists()
        add('missing_ref_policy_blocked', run=observed, no_outputs=True)

        manual = fresh('manual_policy')
        path = manual / 'design/library-policy.json'
        policy = json.loads(path.read_text())
        row = next(e for e in policy['entries'] if e['refdes'] == 'R28')
        sentinels = {'reason': 'REVIEW_SENTINEL_REASON',
                     'placeholder_geometry': 'REVIEW_SENTINEL_GEOMETRY',
                     'review_state': 'REVIEW_SENTINEL_STATUS'}
        row.update(sentinels)
        write_json(path, policy)
        observed = run(manual, '--write-policy')
        after = next(e for e in json.loads(path.read_text())['entries'] if e['refdes'] == 'R28')
        assert observed['exit_code'] == 0
        assert after['reason'] == after['placeholder_geometry'] == ''
        assert after['review_state'] == '未审查'
        add('R01_manual_policy_fields_erased', run=observed, refdes='R28', before=sentinels,
            after={key: after[key] for key in sentinels}, issue_reproduced=True)

        pad = fresh('missing_pad')
        cache = pad / 'references/C25804.json'
        data = json.loads(cache.read_text())
        shape = data['result']['packageDetail']['dataStr']['shape']
        removed = [s for s in shape if s.startswith('PAD~') and s.split('~')[8] == '2']
        assert removed
        data['result']['packageDetail']['dataStr']['shape'] = [s for s in shape if s not in removed]
        write_json(cache, data)
        registration = run(pad, '--write-lock')
        observed = run(pad, '--out-dir', 'out', '--allow-missing')
        assert registration['exit_code'] == observed['exit_code'] == 0
        components = json.loads((pad / 'out/design-netlist.json').read_text())
        pcb = json.loads((pad / 'out/mosaico-dock-placement.json').read_text())
        mismatches = []
        for component, block in zip(components, pcb['shape']):
            if component['code'] != 'C25804':
                continue
            numbers = sorted({s.split('~')[8] for s in block.split('#@$')[1:] if s.startswith('PAD~')})
            expected = sorted(component['nets'])
            assert numbers == ['1'] and expected == ['1', '2']
            mismatches.append({'refdes': component['ref'], 'expected_pads': expected,
                               'actual_pads': numbers, 'status': component['footprint_status']})
        assert mismatches
        summary = json.loads(observed['stdout'])
        assert summary['allow_missing_released'] == ['R26']
        bom = list(csv.DictReader((pad / 'out/bom-review.csv').read_text(encoding='utf-8-sig').splitlines()))
        affected = {e['refdes'] for e in mismatches}
        assert all('UNRESOLVED' not in e['Geometry status'] for e in bom if e['Designator'] in affected)
        add('R02_missing_pad_accepted_after_truthful_lock_refresh', registration=registration,
            run=observed, cache='C25804', removed_pad_count=len(removed),
            affected=mismatches, allow_missing_released=summary['allow_missing_released'],
            issue_reproduced=True)

    result['authority_files_unchanged'] = snapshot(REPO) == authority_before
    assert result['authority_files_unchanged']
    result['review_conclusion'] = 'CHANGES_REQUIRED; proposal mechanics only, no hardware approval'
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
