"""INACTIVE manual QA sender. Requires separately approved SQL/Edge activation.

No privileged Supabase key, secret argv/env/file, proxy, redirect or private retry.
Local n8n calls the separate cloud QA callback; cloud never calls Windows.
"""
import argparse
import getpass
import json
import sys
import time
import urllib.error
import urllib.request
import uuid

CLOUD = 'https://zrzqpbcomlorfzszolrs.supabase.co/functions/v1/corrective-actions-qa'
LOCAL = 'http://127.0.0.1:5678/webhook-test/defectrag-ca-live-qa'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def valid_key(value):
    return isinstance(value, str) and 32 <= len(value) <= 256 and all(33 <= ord(c) <= 126 for c in value)


def post(opener, url, body, headers, timeout):
    request = urllib.request.Request(url, data=json.dumps(body).encode('utf8'),
                                    headers={'Content-Type': 'application/json', **headers}, method='POST')
    with opener.open(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError('request_not_accepted')
        raw = response.read(4097)
        if len(raw) > 4096:
            raise ValueError('response_limit')
        return json.loads(raw)


def wait_ready(opener, budget=120, clock=time.monotonic, pause=time.sleep):
    deadline = clock() + budget
    while clock() < deadline:
        request = urllib.request.Request(LOCAL, data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
        try:
            response = opener.open(request, timeout=min(3, max(.01, deadline-clock())))
        except urllib.error.HTTPError as error:
            response = error
        except (urllib.error.URLError, OSError):
            response = None
        if response is not None:
            try:
                if response.status == 403:
                    return True  # Header-protected listener exists. No key submitted.
                if response.status != 404:
                    return False  # Never send a capability to an unprotected route.
            finally:
                response.close()  # Do not read headers/body.
        pause(min(2, max(0, deadline-clock())))
    return False


def dispatch(event_id, worker_key, local_key, opener=None, wait_for_listener=False, listener_wait_seconds=120):
    # Validate before building requests. Never echo keys or a capability response.
    event_id = str(uuid.UUID(event_id))
    if not valid_key(worker_key) or not valid_key(local_key):
        raise ValueError('invalid_private_key_format')
    if type(listener_wait_seconds) is not int or not 30 <= listener_wait_seconds <= 600:
        raise ValueError('invalid_listener_wait_budget')
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    report = {'event_id': event_id, 'claim_requests': 0, 'local_submissions': 0,
              'finalize_requests': 0, 'workflow_completed': False, 'acknowledged': False,
              'automatic_retry': False, 'real_email_authorized': False}
    headers = {'Authorization': 'Bearer ' + worker_key}
    if wait_for_listener and not wait_ready(opener, budget=listener_wait_seconds):
        report['error'] = 'protected_local_listener_not_ready_no_claim_sent'
        return report
    try:
        report['claim_requests'] = 1
        event = post(opener, CLOUD, {'event_id': event_id},
                     {**headers, 'X-DefectRAG-Operation': 'claim'}, 15)
        if not isinstance(event, dict) or set(event) != {'event_id', 'lease_token', 'case_id', 'kind', 'version'} or event['event_id'] != event_id:
            raise ValueError('unexpected_capability')
        for field in ('lease_token', 'case_id'):
            uuid.UUID(event[field])
        if event['kind'] not in ('created', 'updated') or type(event['version']) is not int or event['version'] < 1:
            raise ValueError('unexpected_capability')
    except Exception:
        report['error'] = 'claim_denied_or_uncertain_do_not_retry'
        return report
    try:
        report['local_submissions'] = 1
        result = post(opener, LOCAL, event, {'X-DefectRAG-CA-Key': local_key}, 60)
        report['workflow_completed'] = isinstance(result, dict) and result.get('event_id') == event_id and result.get('completed') is True
    except Exception:
        report['error'] = 'local_workflow_failed_or_uncertain'
    try:
        report['finalize_requests'] = 1
        result = post(opener, CLOUD, {'event_id': event_id, 'lease_token': event['lease_token'],
                      'completed': report['workflow_completed']}, {**headers, 'X-DefectRAG-Operation': 'finalize'}, 15)
        report['acknowledged'] = isinstance(result, dict) and result.get('acknowledged') is True
        if not report['acknowledged']:
            report['error'] = 'finalize_not_acknowledged_do_not_retry'
    except Exception:
        report['error'] = 'finalize_uncertain_do_not_retry'
    return report


def listener_budget(value):
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError('Use 30 to 600 seconds') from None
    if not 30 <= seconds <= 600:
        raise argparse.ArgumentTypeError('Use 30 to 600 seconds')
    return seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event', required=True, type=lambda s: str(uuid.UUID(s)))
    parser.add_argument('--confirm-approved-sink-qa', action='store_true')
    parser.add_argument('--listener-wait-seconds', type=listener_budget, default=600)
    args = parser.parse_args()
    if not args.confirm_approved_sink_qa or not sys.stdin.isatty():
        raise SystemExit('Private interactive terminal and explicit approved sink-QA confirmation required')
    print('Only run after separate live approval. Keep production/global automation OFF.')
    worker = getpass.getpass('QA worker bearer (hidden, not service-role key): ')
    local = getpass.getpass('Existing LOCAL inbound Header Auth value (hidden): ')
    print('Waiting for the protected LOCAL QA listener (up to '+str(args.listener_wait_seconds)+' seconds). Leave this terminal running, then arm the QA webhook.')
    try:
        report = dispatch(args.event, worker, local, wait_for_listener=True,
                          listener_wait_seconds=args.listener_wait_seconds)
    except Exception:
        raise SystemExit('Invalid input; no private value will be displayed') from None
    print(json.dumps(report, indent=2))
    print('Do not retry a denied/uncertain run; inspect cloud metadata first. Keep global automation OFF.')


if __name__ == '__main__':
    main()
