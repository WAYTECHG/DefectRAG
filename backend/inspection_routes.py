"""Shared read-only inspection UX routes for local FastAPI and the Space host.

The host's existing middleware establishes the account/browser and workspace.
Repository reads retain that boundary; these routes never grant access or write.
"""
from fastapi import HTTPException, Query
from fastapi.responses import HTMLResponse
from .batch_names import batch_name_available
from .inspection_report import render_report

INSPECTION_UX_PATHS = frozenset(('/api/batch-name', '/api/inspections/{identifier}/report'))


def mount_inspection_experience(app, repo, *, local=False):
    @app.get('/api/batch-name')
    def check_batch_name(name: str = Query(..., min_length=1, max_length=80)):
        if not name.strip():
            raise HTTPException(422, 'Add a batch name')
        return {'data': {'available': batch_name_available(repo, name)}}

    @app.get('/api/inspections/{identifier}/report')
    def inspection_report(identifier: str):
        record = repo.get(identifier)
        if not record:
            raise HTTPException(404, 'Inspection not found')
        return HTMLResponse(
            render_report(record, repo.review_history(identifier), repo.review_notes(identifier),
                          repo.messages(identifier), local=local),
            headers={'Cache-Control': 'private, no-store', 'Referrer-Policy': 'no-referrer',
                     'X-Content-Type-Options': 'nosniff'})
