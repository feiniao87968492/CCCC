"""Rebuild source extracts and clean observed simulator records; no simulator calls."""
import csv
import hashlib
import json
import math
import re
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data_preparation' / 'output'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def doc_text(node):
    """Keep OMML fractions and scripts explicit instead of silently joining operands."""
    tag = node.tag.split('}')[-1]
    if tag in ('t', 'instrText'):
        return node.text or ''
    if node.tag == f'{{{M}}}f':
        return '(' + doc_text(node.find(f'{{{M}}}num')) + ')/(' + doc_text(node.find(f'{{{M}}}den')) + ')'
    if node.tag in (f'{{{M}}}sSup', f'{{{M}}}sSub'):
        suffix = 'sup' if tag == 'sSup' else 'sub'
        return doc_text(node.find(f'{{{M}}}e')) + ('^' if suffix == 'sup' else '_') + '{' + doc_text(node.find(f'{{{M}}}{suffix}')) + '}'
    if tag in ('tab', 'br'):
        return ' '
    return ''.join(doc_text(child) for child in node)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def strict_json(text):
    return json.loads(text, object_pairs_hook=unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Non-finite JSON')))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clean_session(path):
    session = path.parent.name
    rows, issues, seen, detections = [], [], {}, set()
    position, tuned, virtual, entered, exited = (0., 0.), 1, 0., False, False
    last_stamp = None
    team = None
    for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = strict_json(line)
            command, q, r = entry['path'], entry['request'], entry['response']
            require(command in ('/enter', '/measure', '/clear', '/exit'), 'Unknown endpoint')
            require(q['arena_id'] == 'default', 'Unexpected arena')
            for key, limit in [('robot_id', 64), ('request_id', 128)]:
                value = q[key]
                require(isinstance(value, str) and 1 <= len(value.encode('utf-8')) <= limit,
                        f'Invalid {key}')
                require(not any(unicodedata.category(c) in ('Cc', 'Cf') for c in value),
                        f'Control/format character in {key}')
            require(type(r['accepted']) is bool, 'accepted is not boolean')
            require(finite(r['real_timestamp_ms']) and finite(r['virtual_time_s']), 'Invalid clock')
            rid = q['request_id']
            row = dict(session_id=session, source_file=path.relative_to(ROOT).as_posix(),
                       source_line=line_no, request_id=rid, command=command,
                       accepted=r['accepted'], idempotent_replay=False, x_m=None, y_m=None,
                       channel=None, receiver_channel_after=tuned,
                       measure_result=r.get('measure_result'), clear_result=r.get('clear_result'),
                       bearing_deg=None, bearing_rad=None, bearing_missing_reason='not_measurement',
                       repeated_site_channel=False, virtual_time_response_s=r['virtual_time_s'],
                       effective_virtual_time_s=virtual, reconstructed_delta_s=0.,
                       timing_residual_s=None, real_timestamp_ms=r['real_timestamp_ms'])
            if not r['accepted']:
                row['bearing_missing_reason'] = 'request_rejected'
                rows.append(row)
                continue
            signature = json.dumps([command, q], sort_keys=True)
            if rid in seen:
                require(seen[rid] == (signature, r), 'Conflicting accepted request_id replay')
                row['idempotent_replay'] = True
                row['bearing_missing_reason'] = 'idempotent_replay_not_new_observation'
                rows.append(row)
                continue
            seen[rid] = (signature, r)
            require(not exited, 'Accepted action after exit')
            require(team is None or q['robot_id'] == team, 'Team changed inside session')
            team = q['robot_id']
            stamp = r['real_timestamp_ms']
            require(last_stamp is None or stamp >= last_stamp, 'Response timestamps decreased')
            last_stamp = stamp
            expected_fields = {'arena_id', 'robot_id', 'request_id'}
            if command in ('/measure', '/clear'):
                expected_fields |= {'position', 'channel'}
            require(set(q) == expected_fields, 'Unexpected/missing request fields')
            delta = 0.
            if command == '/enter':
                require(not entered, 'Second accepted enter')
                require(finite(r['remaining_real_duration_s']) and 0 <= r['remaining_real_duration_s'] <= 1200,
                        'Invalid remaining duration')
                entered = True
            else:
                require(entered, 'Action before accepted enter')
            if command in ('/measure', '/clear'):
                require(set(q['position']) == {'x', 'y'}, 'Invalid position fields')
                new_pos = (q['position']['x'], q['position']['y'])
                require(all(finite(v) and abs(v) <= 2_000_000 for v in new_pos), 'Invalid coordinate')
                ch = q['channel']
                require(finite(ch) and int(ch) == ch and 1 <= ch <= 20, 'Invalid channel')
                ch = int(ch)
                row.update(x_m=new_pos[0], y_m=new_pos[1], channel=ch)
                delta = math.dist(position, new_pos) / 5
                if command == '/measure':
                    result = r['measure_result']
                    require(result in ('direction', 'near', 'no_signal'), 'Invalid measure result')
                    delta += 5 + int(ch != tuned)
                    tuned = ch
                    obs_key = (*new_pos, ch)
                    row['repeated_site_channel'] = obs_key in detections
                    detections.add(obs_key)
                    if result == 'direction':
                        angle = r.get('svd_deg')
                        require(finite(angle) and 0 <= angle < 360, 'Invalid direction bearing')
                        row.update(bearing_deg=angle, bearing_rad=math.radians(angle), bearing_missing_reason='')
                    else:
                        require('svd_deg' not in r, 'Bearing unexpectedly present')
                        row['bearing_missing_reason'] = result
                else:
                    require(r['clear_result'] in ('success', 'no_target_in_range'), 'Invalid clear result')
                    delta += 5 if r['clear_result'] == 'success' else 3
                position = new_pos
            if command == '/exit':
                require(r['exit_reason'] == 'user_exit', 'Unexpected exit reason')
                exited = True
            residual = r['virtual_time_s'] - (virtual + delta)
            require(abs(residual) <= 2e-6, f'Timing mismatch: {residual}')
            virtual = r['virtual_time_s']
            row.update(receiver_channel_after=tuned, effective_virtual_time_s=virtual,
                       reconstructed_delta_s=delta, timing_residual_s=residual)
            rows.append(row)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            # State may be incomplete after an invalid row; quarantine the whole session.
            return [], [dict(session_id=session, source_line=line_no, error=str(exc))], None
    require(bool(rows), 'Empty session')
    active = [r for r in rows if r['accepted'] and not r['idempotent_replay']]
    cleared = sum(r['clear_result'] == 'success' for r in active)
    if not exited:
        issues.append(dict(session_id=session, source_line=None, error='Incomplete session: no exit'))
    summary = dict(session_id=session, rows=len(rows), unique_accepted_actions=len(active),
                   complete=exited, final_virtual_time_s=virtual, cleared_count=cleared,
                   mean_clear_time_s=virtual / cleared if cleared else None,
                   api_response_span_s=(active[-1]['real_timestamp_ms'] - active[0]['real_timestamp_ms']) / 1000,
                   purpose='automation_smoke_only_not_strategy_evaluation')
    return rows, issues, summary


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    extracts = OUT / 'source_text'
    extracts.mkdir(exist_ok=True)
    sources = [ROOT / 'B题.pdf', ROOT / '附件/附件1.docx', ROOT / '附件/附件2.docx']
    logs = sorted((ROOT / 'simulator_automation/evidence').glob('*/requests.jsonl'))
    manifest = []
    for path in sources + logs:
        raw = path.read_bytes()
        manifest.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=len(raw),
                             sha256=hashlib.sha256(raw).hexdigest(),
                             role='official_specification' if path in sources else 'observed_smoke_transcript'))
    write_json(OUT / 'source_manifest.json', manifest)
    for source in sources:
        if source.suffix == '.pdf':
            text = '\n\n'.join(f'[PAGE {i}]\n{p.extract_text()}' for i, p in enumerate(PdfReader(source).pages, 1))
        else:
            with zipfile.ZipFile(source) as archive:
                root = ET.fromstring(archive.read('word/document.xml'))
            paragraphs = [doc_text(p) for p in root.iter(f'{{{W}}}p')]
            text = '\n'.join(f'[P{i:04}] {t}' for i, t in enumerate(paragraphs, 1) if t.strip())
        (extracts / (source.stem + '.txt')).write_text(text, encoding='utf-8')
    rows, issues, sessions = [], [], []
    for log in logs:
        batch, errors, summary = clean_session(log)
        rows.extend(batch)
        issues.extend(errors)
        if summary:
            sessions.append(summary)
    if rows:
        write_csv(OUT / 'observations_clean.csv', rows, list(rows[0]))
    if sessions:
        write_csv(OUT / 'sessions_clean.csv', sessions, list(sessions[0]))
    write_json(OUT / 'issues.json', issues)
    counts = Counter(r['measure_result'] for r in rows if r['command'] == '/measure')
    audit = dict(source_documents=len(sources), source_sessions=len(logs), clean_rows=len(rows),
                 issues=len(issues), measurement_results=dict(counts),
                 bearings_present=sum(r['bearing_deg'] is not None for r in rows),
                 structural_bearing_blanks=sum(r['bearing_deg'] is None for r in rows),
                 repeated_site_channel_actions=sum(r['repeated_site_channel'] for r in rows),
                 idempotent_replays=sum(r['idempotent_replay'] for r in rows),
                 cleaned_data_scope='Observed actions only; no hidden cases or credentials read',
                 http_status='Original transcripts omit HTTP status; not independently auditable',
                 source_extraction='DOCX paragraphs retain basic OMML fractions/scripts; consult originals for figures and complex formulas')
    write_json(OUT / 'audit_summary.json', audit)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit('Audit issues found; see issues.json')


if __name__ == '__main__':
    main()
