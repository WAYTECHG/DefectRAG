"""UI/API software fixtures; no inference or cloud database changes."""
from backend.batch_names import batch_name_available
from backend.inspection_report import render_report
from tests.test_application import client,upload


def test_batch_name_preflight_covers_normalized_active_and_archived_names(client):
    record=upload(client,batch='  QA   Batch ').json()['data']
    assert client.get('/api/batch-name',params={'name':'qa batch'}).json()['data']=={'available':False}
    assert client.get('/api/batch-name',params={'name':'QA BATCH 2'}).json()['data']=={'available':True}
    client.post('/api/history/archive',json={'confirmation':'ARCHIVE'})
    assert client.get('/api/batch-name',params={'name':'ＱＡ batch'}).json()['data']=={'available':False}
    assert client.get('/api/batch-name',params={'name':'   '}).status_code==422
    assert client.get('/api/batch-name',params={'name':'x'*81}).status_code==422
    assert client.get('/api/archives').json()['data'][0]['id']==record['id']


def test_name_check_is_paginated_and_scoped_to_supplied_repository():
    class Scoped:
        def list(self,limit,offset,archived):
            if not archived:return [{'batch':'Other'}]*500 if offset==0 else [{'batch':'End of history'}]
            return [{'batch':'Archive only'}]
    assert not batch_name_available(Scoped(),'end of history')
    assert not batch_name_available(Scoped(),'archive only')
    assert batch_name_available(Scoped(),'another account name')


def test_name_check_does_not_reveal_another_guest_workspaces_history(tmp_path):
    from deployment.space.sessions import SessionRepository,identity
    repo=SessionRepository(tmp_path)
    with identity('a'*64):
        repo.save({'id':'1'*32,'created_at':'2026-10-23','category':'pcb1','verdict':'Good','batch':'Private batch'})
        assert not batch_name_available(repo,'private batch')
    with identity('b'*64):
        assert batch_name_available(repo,'private batch')


def test_report_preserves_evidence_and_escapes_untrusted_content(client):
    record=upload(client,batch='<script>alert(1)</script>').json()['data']
    report=client.get(f'/api/inspections/{record["id"]}/report')
    assert report.status_code==200
    for text in ('Inspection evidence report','Image and localization','Inspection measurements','Human review','Evidence conversation','Retrieved documentation','Print / save PDF','@media print','name="viewport"','not accuracy'):
        assert text in report.text
    assert '<script>alert' not in report.text
    assert '&lt;script&gt;' in report.text
    assert record['image_url'] in report.text and record['heatmap_url'] in report.text
    assert report.headers['cache-control']=='private, no-store'
    assert client.get('/api/inspections/'+'a'*32+'/report').status_code==404


def test_report_does_not_inject_script_urls_or_hide_saved_dialogue():
    html=render_report({'id':'a'*32,'category':'pcb1','verdict':'Anomalous','score':.2,'image_url':'javascript:alert(1)','heatmap_url':'https://example.test/image?a=1&b=2'},[],[],[
        {'role':'user','question':'<img src=x onerror=alert(1)>'},
        {'role':'assistant','answer':'Saved answer','evidence':[{'chunk_id':'id','title':'<script>','text':'Passage','url':'javascript:alert(1)','scope':'Project screening policy'}]}])
    assert 'src="javascript:' not in html and 'href="javascript:' not in html
    assert '&lt;img src=x' in html and '<strong>Question</strong>' in html
    assert 'Saved answer' in html and 'Passage' in html and '&lt;script&gt;' in html
    assert 'https://example.test/image?a=1&amp;b=2' in html
