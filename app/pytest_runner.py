"""Executed in a disposable working directory by the parent process.

This is a convenience process boundary, NOT an OS security sandbox.
"""
from pathlib import Path
import json
import os
import sys
import traceback


def main():
    root = Path.cwd()
    sys.path.insert(0, str(root))
    import pytest
    output = root / '.lab-report.json'
    data = {'records': {}, 'collection_errors': [], 'collected': 0, 'exit_code': None}

    def flush():
        temporary = output.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        temporary.replace(output)

    class ReportPlugin:
        def pytest_collection_finish(self, session):
            data['collected'] = len(session.items)
            flush()

        def pytest_collectreport(self, report):
            if report.failed:
                data['collection_errors'].append(str(report.longrepr)[-16000:])
                flush()

        def pytest_runtest_logreport(self, report):
            if report.when == 'call' or report.failed or report.skipped:
                old = data['records'].get(report.nodeid)
                if old and old['outcome'] == 'failed':
                    return
                data['records'][report.nodeid] = {
                    'nodeid': report.nodeid,
                    'outcome': report.outcome,
                    'phase': report.when,
                    'duration': round(report.duration, 5),
                    'detail': str(report.longrepr)[-10000:] if report.longrepr else '',
                    'stdout': getattr(report, 'capstdout', '')[-3000:],
                }
                flush()

    try:
        result = pytest.main([
            '-q', '--tb=short', '--color=no', '-c', '.lab-pytest.ini',
            '-p', 'pytest_asyncio.plugin', *sys.argv[1:]
        ], plugins=[ReportPlugin()])
        data['exit_code'] = int(result)
        flush()
        return int(result)
    except BaseException:
        data['collection_errors'].append(traceback.format_exc()[-16000:])
        data['exit_code'] = 3
        flush()
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
