"""Public source export must retain build inputs and exclude account-specific QA."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import prepare_github_export as export


class GithubExportTests(unittest.TestCase):
    def test_selection_preserves_current_features_without_private_state(self):
        for name in ('README.md','frontend/localBuild.mjs','frontend/src/GuidedPractice.jsx',
                     'frontend/src/practiceAssets/candle-original.jpg','deployment/n8n/corrective-actions.json',
                     'deployment/supabase_auth_mfa.sql','docs/GUIDED_PRACTICE.md',
                     'docs/SETUP.md','docs/assets/hero.svg'):
            self.assertTrue(export.selected(name),name)
        for name in ('DEVELOPMENT_PROGRESS.md','supabase.txt','.env','models/model.safetensors',
                     'runtime/gallery-setup/gallery-key.txt','frontend/public/config.js',
                     'docs/SUPABASE_QUERY_CATALOG.md','docs/QA_ACCOUNT_REMOVAL.md',
                     'deployment/qa_account_backup_PRIVATE.sql','deployment/qa_account_cleanup_REVIEW_ONLY.sql',
                     'deployment/qa_account_deletion_preflight.sql','deployment/email_pending_qa_verification.sql',
                     'deployment/email_single_qa_verification.sql','results/private-qa/screen.png',
                     'docs/DEVELOPMENT_PROGRESS.previous.md','docs/zerogpu_phase5/cloud-batch.png',
                     'docs/EMAIL_503_ROOT_CAUSE.md','docs/PAUSE_CHECKPOINT_20261016.md',
                     'docs/future-internal-progress.md','GITHUB_EXPORT.json',
                     'deployment/Update-GitHub.ps1','scripts/checkpoint.py'):
            self.assertFalse(export.selected(name),name)

    def test_export_keeps_existing_installation_and_uses_blank_public_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);output=root/'development-support'/'new-public-export'
            files={'README.md':'# Public source','frontend/localBuild.mjs':'// receipt plugin',
                   'frontend/public/config.js':'PRIVATE SETTINGS',
                   'deployment/qa_account_backup_PRIVATE.sql':'PRIVATE ACCOUNT',
                   'docs/GUIDED_PRACTICE.md':'# Practice guide','supabase.txt':'PRIVATE KEY'}
            for name,value in files.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value)
            def git(args,**kwargs):
                if args[:2]==['git','ls-files']:return '\0'.join(files).encode()
                if args==['git','rev-parse','HEAD']:return b'a'*40+b'\n'
                raise AssertionError(args)
            with patch.object(export,'ROOT',root),patch.object(export.subprocess,'check_output',side_effect=git),patch('sys.argv',['export','--output',str(output)]),contextlib.redirect_stdout(io.StringIO()):
                export.main()
            self.assertTrue((output/'frontend/localBuild.mjs').is_file())
            self.assertNotIn('PRIVATE',(output/'frontend/public/config.js').read_text())
            self.assertFalse((output/'deployment/qa_account_backup_PRIVATE.sql').exists())
            self.assertFalse((output/'supabase.txt').exists())
            self.assertEqual((root/'frontend/public/config.js').read_text(),'PRIVATE SETTINGS')
            self.assertFalse((output/'GITHUB_EXPORT.json').exists())
            self.assertTrue(json.loads((output.parent/(output.name+'.export.json')).read_text())['public_config_blank'])


if __name__=='__main__':unittest.main()
