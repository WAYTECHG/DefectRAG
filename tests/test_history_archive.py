from tests.test_application import client, upload


def test_archive_preserves_inspection_conversation_alert_and_can_restore(client):
    record=upload(client).json()['data']
    client.post('/api/assistant',json={'inspection_id':record['id'],'question':'Explain the score'})
    archived=client.post('/api/history/archive',json={'confirmation':'ARCHIVE','batch':'LINE-A'}).json()['data']
    assert archived['archived']==1
    assert client.get('/api/inspections').json()['data']==[]
    assert client.get('/api/alerts').json()['data']==[]
    assert client.get('/api/stats').json()['data']['archived_total']==1
    assert client.get('/api/inspections/'+record['id']).status_code==404
    assert client.get('/api/archives').json()['data'][0]['id']==record['id']
    assert client.post('/api/history/restore',json={'ids':[record['id']]}).json()['data']['restored']==1
    assert client.get('/api/inspections/'+record['id']).json()['data']['score']==record['score']
    assert len(client.get('/api/inspections/'+record['id']+'/messages').json()['data'])==2
    assert len(client.get('/api/alerts').json()['data'])==1


def test_archive_requires_explicit_confirmation_and_respects_filters(client):
    upload(client)
    assert client.post('/api/history/archive',json={}).status_code==422
    assert client.post('/api/history/archive',json={'confirmation':'ARCHIVE','category':'capsules'}).json()['data']['archived']==0
    assert len(client.get('/api/inspections').json()['data'])==1
