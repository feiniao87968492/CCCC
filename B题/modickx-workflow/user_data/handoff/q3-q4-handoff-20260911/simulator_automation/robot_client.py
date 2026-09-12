"""Official four-command API client. No password and no simulator internals."""
import json
import math
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


class RobotClient:
    def __init__(self, team, port=2026, log_path=None):
        self.team = str(team)
        self.url = f"http://127.0.0.1:{int(port)}"
        self.http = build_opener(ProxyHandler({}))
        self.log_path = Path(log_path) if log_path else None
        self.deadline = None
        self.entered = False

    def command(self, path, *, position=None, channel=None):
        if path not in ('/enter', '/measure', '/clear', '/exit'):
            raise ValueError('Unknown command')
        if path in ('/measure', '/clear'):
            if type(channel) is not int or not 1 <= channel <= 20:
                raise ValueError('Channel must be an integer from 1 to 20')
            if position is None or len(position) != 2 or any(
                not math.isfinite(v) or abs(v) > 2_000_000 for v in position
            ):
                raise ValueError('Invalid coordinates')
        payload = dict(arena_id='default', robot_id=self.team, request_id=uuid.uuid4().hex)
        if position is not None:
            payload['position'] = dict(zip(('x', 'y'), position))
        if channel is not None:
            payload['channel'] = channel
        encoded = json.dumps(payload, allow_nan=False).encode('utf-8')
        # Serialize actions; retries reuse exactly the same body and request_id.
        for attempt in range(3):
            request = Request(self.url + path, data=encoded,
                              headers={'Content-Type': 'application/json'}, method='POST')
            try:
                with self.http.open(request, timeout=5) as response:
                    result = json.load(response)
                break
            except HTTPError as exc:
                raise RuntimeError(f'{path}: HTTP {exc.code}; action stopped') from exc
            except (URLError, TimeoutError, ConnectionError):
                if attempt == 2:
                    raise
                time.sleep(0.3 * (attempt + 1))
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(dict(path=path, request=payload, response=result),
                                        ensure_ascii=False) + '\n')
        if result.get('accepted') is not True:
            raise RuntimeError(f'{path}: request rejected: {result}')
        if path == '/enter':
            self.entered = True
            self.deadline = time.monotonic() + result['remaining_real_duration_s']
        elif path == '/exit':
            self.entered = False
        return result

    def enter(self):
        return self.command('/enter')

    def measure(self, x, y, channel):
        if self.deadline is not None and time.monotonic() >= self.deadline - 5:
            raise TimeoutError('Runtime budget nearly exhausted; finish the test')
        return self.command('/measure', position=(x, y), channel=channel)

    def clear(self, x, y, channel):
        if self.deadline is not None and time.monotonic() >= self.deadline - 5:
            raise TimeoutError('Runtime budget nearly exhausted; finish the test')
        return self.command('/clear', position=(x, y), channel=channel)

    def exit(self):
        return self.command('/exit')
