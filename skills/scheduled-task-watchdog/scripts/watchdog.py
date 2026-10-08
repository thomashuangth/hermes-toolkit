"""Read normalized job receipts. Never schedules, repairs or sends messages."""
import argparse
import json
import math
import time


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Finite numeric timestamp required')
    return value


def inspect(jobs, now, self_id=None):
    number(now)
    if not isinstance(jobs, list):
        raise ValueError('List required')
    findings = []
    seen = set()
    for job in jobs:
        jid = job['id']
        if not isinstance(jid, str) or not jid or jid in seen:
            raise ValueError('Unique string IDs required')
        seen.add(jid)
        if not isinstance(job.get('enabled', True), bool):
            raise ValueError('Boolean enabled required')
        if jid == self_id or not job.get('enabled', True) or job.get('status') == 'completed':
            continue
        age = number(job['max_age_seconds'])
        if age <= 0:
            raise ValueError('Positive max age required')
        stamp = job.get('last_success')
        reason = None
        if stamp is None:
            reason = 'never_succeeded'
        elif number(stamp) > now:
            reason = 'future_timestamp'
        elif now - stamp > age:
            reason = 'stale'
        if job.get('status') == 'failed':
            reason = 'failed'
        if reason:
            findings.append({'id': jid, 'reason': reason})
    return findings


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--now', type=float)
    parser.add_argument('--self-id')
    args = parser.parse_args()
    try:
        with open(args.input, encoding='utf-8') as source:
            result = inspect(json.load(source), time.time() if args.now is None else args.now, args.self_id)
        if result:
            print(json.dumps({'findings': result}))
        raise SystemExit(1 if result else 0)
    except (ValueError, KeyError, TypeError, OSError):
        print(json.dumps({'error': 'Invalid or inaccessible normalized receipts'}))
        raise SystemExit(2)
