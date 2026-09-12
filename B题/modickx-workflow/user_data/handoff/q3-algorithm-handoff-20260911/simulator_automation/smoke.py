"""Exercise the official API in a UI-verified practice session, not a solver."""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from robot_client import RobotClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--problem', type=int, choices=(3, 4), required=True)
    parser.add_argument('--team', default='202611102016')
    parser.add_argument('--port', type=int, default=2026)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    # UI guard prevents accidentally using this diagnostic on a formal attempt.
    inspect = subprocess.run(
        ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         str(root / 'ui.ps1'), '-Action', 'Inspect'], capture_output=True, timeout=90)
    # Windows PowerShell uses the system's console encoding when redirected.
    text = inspect.stdout.decode('utf-8', errors='replace')
    if '演练' not in text:
        text = inspect.stdout.decode('gb18030', errors='replace')
    expected = f'问题{args.problem} 演练 测试'
    if (inspect.returncode or f'ControlType.Text|test-run-title|{expected}' not in text
            or 'ControlType.Text||等待机器狗进入' not in text
            or f'ControlType.Text||队号 {args.team}' not in text):
        raise RuntimeError('Expected practice test is not active. No API action sent.')
    out = root / 'evidence' / (datetime.now().strftime('%Y%m%d-%H%M%S') + f'-p{args.problem}')
    out.mkdir(parents=True, exist_ok=False)
    (out / 'ui-before.txt').write_text(text, encoding='utf-8')
    client = RobotClient(args.team, args.port, out / 'requests.jsonl')
    responses = []
    try:
        responses.append(client.enter())
        responses.append(client.measure(0, 0, 1))
        responses.append(client.measure(0, 0, 2))
        # Exercise /clear without a localization claim; the result may be either code.
        responses.append(client.clear(0, 0, 1))
        responses.append(client.measure(0, 0, 2))
    finally:
        if client.entered:
            responses.append(client.exit())
    assert all(r['accepted'] for r in responses)
    times = [r['virtual_time_s'] for r in responses]
    clear_cost = 5 if responses[3]['clear_result'] == 'success' else 3
    assert times == [0, 5, 11, 11 + clear_cost, 16 + clear_cost, 16 + clear_cost], times
    assert responses[-1]['exit_reason'] == 'user_exit'
    summary = dict(problem=args.problem, purpose='API smoke test, not strategy evaluation',
                   commands=6, virtual_times=times, exit_reason='user_exit', passed=True)
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    after = subprocess.run(
        ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         str(root / 'ui.ps1'), '-Action', 'Inspect'], capture_output=True, timeout=90)
    (out / 'ui-after.txt').write_bytes(after.stdout)
    print(json.dumps(summary, ensure_ascii=False))
    print(f'Evidence: {out}')


if __name__ == '__main__':
    main()
