"""No network: bound the UI-only release and preserve existing cloud settings."""
import hashlib
import json
import tempfile
import types
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch
from deployment.space import publish


class FrontendPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.out=self.root/'release'
        self.ui=self.out/'ui-dist'
        self.ui.mkdir(parents=True)
        self.contents={'config.js':b'public settings unchanged','index.html':b'new UI','assets/current.js':b'tested bundle'}
        for name,data in self.contents.items():
            path=self.ui/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        self.frontend={'files':{name:hashlib.sha256(data).hexdigest() for name,data in self.contents.items()}}
        self.remote=self.root/'remote';self.remote.mkdir()
        (self.remote/'config.js').write_bytes(self.contents['config.js'])
        (self.remote/'index.html').write_bytes(b'previous UI')
        self.api=Mock()
        self.api.space_info.return_value=types.SimpleNamespace(sha='a'*40)
        self.api.list_repo_files.return_value=['frontend/dist/config.js','frontend/dist/index.html','backend/main.py']
        self.api.create_commit.return_value=types.SimpleNamespace(oid='b'*40)
        package=types.ModuleType('huggingface_hub')
        package.HfApi=lambda:self.api
        package.CommitOperationAdd=lambda **args:types.SimpleNamespace(**args)
        package.hf_hub_download=lambda repo,name,**kwargs:str(self.remote/Path(name).name)
        stack=ExitStack();self.addCleanup(stack.close)
        stack.enter_context(patch.dict('sys.modules',{'huggingface_hub':package}))
        stack.enter_context(patch.object(publish,'OUT',self.out))
        stack.enter_context(patch.object(publish,'ROOT',self.root))
        stack.enter_context(patch.object(publish,'checked_frontend',return_value=self.frontend))
        stack.enter_context(patch.object(publish.subprocess,'check_output',return_value='source-checkpoint\n'))
        stack.enter_context(patch('builtins.print'))

    def test_dry_run_never_uploads_or_creates_rollback(self):
        publish.publish_frontend(self.frontend,dry_run=True)
        self.api.create_commit.assert_not_called()
        self.assertFalse(list(self.out.glob('frontend-rollback-*')))

    def test_only_changed_frontend_assets_upload_and_previous_entry_is_saved(self):
        publish.publish_frontend(self.frontend)
        call=self.api.create_commit.call_args.kwargs
        self.assertEqual(call['parent_commit'],'a'*40)
        self.assertEqual({op.path_in_repo for op in call['operations']},{'frontend/dist/index.html','frontend/dist/assets/current.js'})
        self.assertEqual((self.out/('frontend-rollback-'+'a'*12)/'index.html').read_bytes(),b'previous UI')
        self.assertEqual(json.loads((self.out/'publish-frontend.json').read_text())['commit'],'b'*40)

    def test_live_configuration_difference_blocks_upload(self):
        (self.remote/'config.js').write_bytes(b'other live settings')
        with self.assertRaisesRegex(SystemExit,'Live public configuration differs'):
            publish.publish_frontend(self.frontend)
        self.api.create_commit.assert_not_called()

    def test_changed_bundle_blocks_upload(self):
        (self.ui/'index.html').write_bytes(b'untested change')
        with self.assertRaisesRegex(SystemExit,'Frontend changed'):
            publish.publish_frontend(self.frontend)
        self.api.create_commit.assert_not_called()

    def test_cache_fix_changes_only_two_responses_and_is_idempotent(self):
        original=b"# Existing server/auth/model code stays unchanged\r\nreturn FileResponse(UI/'index.html')\r\nreturn FileResponse(UI/'config.js')\r\n# Existing API routes\r\n"
        fixed=publish.entry_cache_headers(original)
        self.assertEqual(fixed.replace(b",headers={'Cache-Control':'no-store'}",b''),original)
        self.assertEqual(publish.entry_cache_headers(fixed),fixed)
        with self.assertRaisesRegex(SystemExit,'Live entry response changed'):
            publish.entry_cache_headers(b'unknown server response code')

    def test_cache_patch_is_separate_from_unrelated_local_server_changes(self):
        original=b"# Installed server\nreturn FileResponse(UI/'index.html')\nreturn FileResponse(UI/'config.js')\n"
        (self.remote/'app.py').write_bytes(original)
        publish.publish_frontend(self.frontend,refresh_html_cache=True)
        operations=self.api.create_commit.call_args.kwargs['operations']
        server=next(op for op in operations if op.path_in_repo=='deployment/space/app.py')
        self.assertEqual(server.path_or_fileobj,publish.entry_cache_headers(original))
        self.assertEqual((self.out/('frontend-rollback-'+'a'*12)/'server-entry-cache.py').read_bytes(),original)


if __name__=='__main__':
    unittest.main()
