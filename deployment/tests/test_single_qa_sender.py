"""Fake HTTP only: no real secrets, accounts, cloud calls or webhook submission."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error

p=Path(__file__).resolve().parents[1]/'n8n/run_single_qa_event.py'
spec=importlib.util.spec_from_file_location('qa_sender',p)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
EVENT='11111111-1111-4111-8111-111111111111'
LEASE='22222222-2222-4222-8222-222222222222'
CASE='33333333-3333-4333-8333-333333333333'
CAP={'event_id':EVENT,'lease_token':LEASE,'case_id':CASE,'kind':'created','version':1}


class Response:
    def __init__(self,body,status=200):self.body=body;self.status=status
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def close(self):pass
    def read(self,n):return json.dumps(self.body).encode()[:n]


class Opener:
    def __init__(self,steps):self.steps=list(steps);self.calls=[]
    def open(self,req,timeout):
        self.calls.append(req)
        step=self.steps.pop(0)
        if isinstance(step,Exception):raise step
        return step


class SenderTests(unittest.TestCase):
    def test_success_once_and_projection(self):
        o=Opener([Response(CAP),Response({'event_id':EVENT,'completed':True}),Response({'acknowledged':True})])
        r=m.dispatch(EVENT,'W'*40,'L'*40,o)
        self.assertTrue(r['acknowledged']);self.assertTrue(r['workflow_completed'])
        self.assertEqual([x.full_url for x in o.calls],[m.CLOUD,m.LOCAL,m.CLOUD])
        self.assertEqual(json.loads(o.calls[1].data),CAP)
        self.assertNotIn('Authorization',o.calls[1].headers)
        self.assertFalse(r['automatic_retry'])

    def test_claim_failure_never_submits_locally_or_retries(self):
        o=Opener([ValueError('PRIVATE BACKEND RESPONSE')])
        r=m.dispatch(EVENT,'W'*40,'L'*40,o)
        self.assertEqual(len(o.calls),1);self.assertEqual(r['local_submissions'],0)
        self.assertNotIn('PRIVATE',json.dumps(r))

    def test_extra_claim_data_never_forwarded(self):
        o=Opener([Response({**CAP,'private':'DO NOT FORWARD'})])
        r=m.dispatch(EVENT,'W'*40,'L'*40,o)
        self.assertEqual(r['local_submissions'],0)

    def test_local_failure_finishes_false_once(self):
        o=Opener([Response(CAP),ValueError('private header'),Response({'acknowledged':True})])
        r=m.dispatch(EVENT,'W'*40,'L'*40,o)
        self.assertFalse(json.loads(o.calls[2].data)['completed'])
        self.assertEqual(r['local_submissions'],1)
        self.assertNotIn(LEASE,json.dumps(r));self.assertNotIn('W'*40,json.dumps(r))

    def test_finalize_uncertain_never_resends(self):
        o=Opener([Response(CAP),Response({'event_id':EVENT,'completed':True}),ValueError('private')])
        r=m.dispatch(EVENT,'W'*40,'L'*40,o)
        self.assertEqual(len(o.calls),3);self.assertEqual(r['finalize_requests'],1)
        self.assertEqual(r['error'],'finalize_uncertain_do_not_retry')

    def test_invalid_key_no_network(self):
        o=Opener([])
        with self.assertRaises(ValueError):m.dispatch(EVENT,'bad\nkey','L'*40,o)
        self.assertEqual(o.calls,[])

    def test_readiness_never_sends_auth_and_refuses_unprotected_route(self):
        o=Opener([Response({},200)])
        self.assertFalse(m.wait_ready(o))
        self.assertNotIn('Authorization',o.calls[0].headers)
        self.assertNotIn('X-defectrag-ca-key',o.calls[0].headers)

    def test_readiness_404_then_403(self):
        o=Opener([Response({},404),Response({},403)])
        now=[0]
        self.assertTrue(m.wait_ready(o,clock=lambda:now[0],pause=lambda s:now.__setitem__(0,now[0]+s)))
        self.assertEqual(len(o.calls),2)

    def test_readiness_timeout_never_claims_or_submits(self):
        o=Opener([])
        with patch.object(m,'wait_ready',return_value=False) as readiness:
            r=m.dispatch(EVENT,'W'*40,'L'*40,o,wait_for_listener=True,listener_wait_seconds=600)
        readiness.assert_called_once_with(o,budget=600)
        self.assertEqual(o.calls,[])
        self.assertEqual([r[k] for k in ['claim_requests','local_submissions','finalize_requests']],[0,0,0])
        self.assertEqual(r['error'],'protected_local_listener_not_ready_no_claim_sent')

    def test_wait_budget_is_bounded_before_network(self):
        for value in [29,601,True,'600']:
            o=Opener([])
            with self.assertRaises(ValueError):m.dispatch(EVENT,'W'*40,'L'*40,o,wait_for_listener=True,listener_wait_seconds=value)
            self.assertEqual(o.calls,[])
        self.assertEqual(m.listener_budget('600'),600)
        for value in ['0','601','private']:
            with self.assertRaises(m.argparse.ArgumentTypeError):m.listener_budget(value)


if __name__=='__main__':unittest.main()
