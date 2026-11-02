"""Guards for `publish --server-files`: only reviewed server files, no hidden drift."""
import subprocess
import sys
import types
from pathlib import Path

import pytest

from deployment.space import publish

ROOT = Path(__file__).resolve().parents[1]
NAME = 'backend/rag.py'


def committed(name):
    return subprocess.run(['git', 'show', 'HEAD:' + name], cwd=ROOT, capture_output=True, check=False).stdout


@pytest.fixture
def hub(tmp_path, monkeypatch):
    """A fake Space whose files are set per test; records any commit."""
    state = {'files': {}, 'commits': []}

    class Api:
        def space_info(self, repo):
            return types.SimpleNamespace(sha='a' * 40)

        def list_repo_files(self, repo, repo_type, revision):
            return list(state['files'])

        def create_commit(self, **kwargs):
            state['commits'].append(kwargs)
            return types.SimpleNamespace(oid='b' * 40)

    def download(repo, name, repo_type, revision):
        path = tmp_path / name.replace('/', '_')
        path.write_bytes(state['files'][name])
        return str(path)

    fake = types.SimpleNamespace(HfApi=Api, hf_hub_download=download,
                                 CommitOperationAdd=lambda path_in_repo, path_or_fileobj: (path_in_repo, path_or_fileobj))
    monkeypatch.setitem(sys.modules, 'huggingface_hub', fake)
    monkeypatch.setattr(publish, 'OUT', tmp_path / 'out')
    return state


@pytest.mark.skipif(not committed(NAME), reason='needs the git history of backend/rag.py')
def test_live_equal_to_last_commit_is_accepted_and_only_that_file_is_sent(hub, capsys):
    hub['files'] = {NAME: publish.unix_lines(committed(NAME))}
    publish.publish_server_files([NAME], dry_run=True)
    out = capsys.readouterr().out
    assert '"server_files_only": true' in out and not hub['commits']
    local = publish.unix_lines((ROOT / NAME).read_bytes())
    assert ('"changed_files": ["backend/rag.py"]' in out) == (local != hub['files'][NAME])


@pytest.mark.skipif(not committed(NAME), reason='needs the git history of backend/rag.py')
def test_unreviewed_live_drift_is_refused(hub):
    hub['files'] = {NAME: b'# changed directly on the Space\n'}
    with pytest.raises(SystemExit, match='differs from the last commit'):
        publish.publish_server_files([NAME])
    assert not hub['commits']


@pytest.mark.parametrize('name', ['models/x.py', 'backend/../.env', 'frontend/dist/index.html', 'backend/notes.txt'])
def test_only_server_python_files_are_allowed(hub, name):
    with pytest.raises(SystemExit, match='only backend'):
        publish.publish_server_files([name])


def test_new_files_need_a_full_publish(hub):
    hub['files'] = {}
    with pytest.raises(SystemExit, match='not on the Space'):
        publish.publish_server_files([NAME])
