"""Offline publisher/preflight checks: no migration, Supabase or HF call."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from deployment.space import publish


def test_publisher_offline_frontend_check_does_not_import_huggingface(monkeypatch,capsys):
    monkeypatch.setattr('sys.argv',['publish','--check-frontend'])
    monkeypatch.setattr(publish,'checked_frontend',lambda:{'files':{'index.html':'fixture'},'source_fingerprint':'fixture-hash'})
    publish.main()
    assert json.loads(capsys.readouterr().out)=={'verified':True,'files':1,'source_fingerprint':'fixture-hash'}
    assert 'HfApi' not in vars(publish)


def test_invalid_frontend_blocks_before_publisher_can_contact_hf(monkeypatch):
    monkeypatch.setattr('sys.argv',['publish','--phase','5'])
    def fail():raise SystemExit('Frontend release blocked')
    monkeypatch.setattr(publish,'checked_frontend',fail)
    with pytest.raises(SystemExit,match='Frontend release blocked'):publish.main()
    assert 'HfApi' not in vars(publish)


def test_frontend_validation_uses_offline_node_guard_not_remote_configuration(monkeypatch):
    calls=[]
    def run(command,**kwargs):
        calls.append((command,kwargs));return SimpleNamespace(returncode=1,stderr='Source changed',stdout='')
    monkeypatch.setattr(publish.subprocess,'run',run)
    with pytest.raises(SystemExit,match='Source changed'):publish.checked_frontend()
    assert calls[0][0][0]=='node' and calls[0][0][-2]=='check'


def test_preflight_contains_only_readonly_metadata_statements():
    import re
    sql=Path('deployment/supabase_auth_preflight.sql').read_text(encoding='utf8')
    clean=re.sub(r'--[^\n]*','',sql)
    assert clean.strip().startswith('begin read only;') and clean.strip().endswith('rollback;')
    assert not re.search(r'\b(create|alter|drop|insert|update|delete|grant|revoke|truncate|execute|call)\b',clean,re.I)
    assert 'aclexplode(coalesce(p.proacl,acldefault(' in sql
    assert "('auth.uid()'),('auth.jwt()'),('auth.role()')" in sql
    assert 'from auth.users' not in clean and 'from auth.mfa_factors' not in clean


def test_reviewed_auth_migration_remains_exactly_the_same():
    import hashlib
    normalized=Path('deployment/supabase_auth_mfa.sql').read_text(encoding='utf8').encode()
    assert hashlib.sha256(normalized).hexdigest()=='cea1e451073fad9f47aca26292cb83a5d337854eef437d97f8c80b79c121e983'
