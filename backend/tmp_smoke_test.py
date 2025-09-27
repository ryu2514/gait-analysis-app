"""
Lightweight backend smoke test without running an HTTP server.
Validates that the FastAPI app imports and registers expected routes.
"""
import importlib


EXPECTED_PATHS = {
    '/',
    '/api/v1/health',
    '/api/v1/gait-analysis/capabilities',
}


def run():
    try:
        m = importlib.import_module('main')
        app = m.app
    except Exception as e:
        print("IMPORT_FAIL", str(e))
        return 1

    try:
        paths = set()
        for r in app.routes:
            if hasattr(r, 'path'):
                paths.add(r.path)
        missing = sorted(EXPECTED_PATHS - paths)
        print('ROUTES_FOUND', len(paths))
        print('MISSING', missing)
        return 0 if not missing else 2
    except Exception as e:
        print('INTROSPECT_FAIL', str(e))
        return 1

if __name__ == '__main__':
    raise SystemExit(run())
