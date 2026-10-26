"""Printable inspection evidence; presentation only, no model or storage writes."""
import html
import math
from urllib.parse import urlsplit
from .reviews import parse_review


def esc(value):
    return html.escape(str(value),quote=True)


def number(value):
    return f'{value:.5f}' if isinstance(value,(int,float)) and math.isfinite(value) else '—'


def image_url(value):
    value=str(value or '')
    parsed=urlsplit(value)
    # Preserve scoped capability/signed URLs without allowing executable schemes.
    return esc(value) if (value.startswith('/api/') and not parsed.netloc) or parsed.scheme=='https' else ''


STYLE='''
:root{color-scheme:light;--ink:#202744;--muted:#697797;--line:#e0e4f2;--purple:#6554ed}
*{box-sizing:border-box}body{margin:0;background:#f5f6fc;color:var(--ink);font:15px/1.6 system-ui,sans-serif}
main{max-width:1120px;margin:36px auto;padding:0 24px}header{background:linear-gradient(115deg,#202442,#454893);color:white;padding:32px;border-radius:20px}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:700}.header-row,.section-heading{display:flex;justify-content:space-between;align-items:center;gap:20px}
h1{font-size:32px;line-height:1.2;margin:12px 0}header p{color:#e0e2ff;margin:8px 0}h2{font-size:20px;margin:0 0 18px}h3{font-size:15px}
button{background:white;color:#343663;border:0;border-radius:10px;padding:12px 18px;font:inherit;font-weight:650;cursor:pointer;white-space:nowrap}
.card{background:white;border:1px solid var(--line);border-radius:18px;padding:26px;margin:20px 0}.summary{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:20px}.metric small,.muted,figcaption{color:var(--muted)}.metric strong{display:block;font-size:25px;line-height:1.4;font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:5px 12px;border-radius:30px;background:#f0ecff;color:#5b45bb;font-weight:700}.good{background:#e7f8f2;color:#08785b}.anomalous{background:#fff0e5;color:#a44814}.uncertain{background:#fff6d6;color:#826300}
.note{background:#f6f4ff;border:1px solid #e1dcff;border-radius:10px;padding:14px 18px}.images{display:grid;grid-template-columns:1fr 1fr;gap:22px}figure{margin:0;min-width:0}img{display:block;width:100%;height:300px;object-fit:contain;background:#f5f6fc;border-radius:12px}figcaption{font-size:13px;margin-top:8px}
table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{text-align:left;border-bottom:1px solid var(--line);padding:11px 12px;vertical-align:top;overflow-wrap:anywhere}th{width:30%;font-size:13px;color:var(--muted);font-weight:600}.section-no{font-size:12px;color:var(--purple);letter-spacing:.1em}
article{border-left:3px solid #d7d0ff;padding:2px 18px;margin:18px 0}article p{white-space:pre-wrap;overflow-wrap:anywhere}footer{color:var(--muted);font-size:12px;padding:8px 2px 30px}.empty{color:var(--muted)}
@media(max-width:700px){main{padding:0 14px;margin:14px auto}header,.card{padding:20px}.header-row{align-items:flex-start;flex-direction:column}.summary,.images{grid-template-columns:1fr 1fr}h1{font-size:26px}img{height:220px}}
@media(max-width:440px){.images{grid-template-columns:1fr}.summary{gap:18px}.metric strong{font-size:20px}th{width:38%}}
@media print{@page{margin:14mm}body{background:white;font-size:11px}main{margin:0;padding:0;max-width:none}header{background:white;color:var(--ink);border-bottom:3px solid var(--purple);border-radius:0;padding:0 0 18px}header p{color:var(--muted)}button{display:none}.card{border-radius:0;padding:16px 0;border:0;border-bottom:1px solid var(--line)}.summary,.images,article,tr{break-inside:avoid}img{height:240px}h2,h3{break-after:avoid}.note{background:white}}
'''


def render_report(record,reviews,notes,messages,local=False):
    fields=('id','created_at','category','batch','filename','verdict','score','threshold',
            'uncertainty_margin','model_id','profile','model_sha256','inference_ms',
            'total_model_ms','localization','scope','storage','sync_version','alert_acknowledged')
    rows=''.join(f'<tr><th scope="row">{esc(key.replace("_"," ").capitalize())}</th><td>{esc(record[key])}</td></tr>' for key in fields if key in record)
    review_html=''.join(f'<article><strong>{esc(r["status"])} · {esc(r["decision"])}</strong><p class="muted">{esc(r["reviewer"])} · {esc(r["created_at"])}</p><p>{esc(r["note"])}</p></article>' for r in reviews)
    review_html+=''.join(f'<article><strong>Review note</strong><p class="muted">{esc(n["reviewer"])} · {esc(n["created_at"])}</p><p>{esc(n["body"])}</p></article>' for n in notes if not parse_review(n['body']))
    review_html=review_html or '<p class="empty">No human review decision has been recorded. A model verdict is not human acceptance.</p>'
    evidence=''.join(f'<article><strong>{"Question" if m.get("role")=="user" else "Evidence Assistant"}</strong><p>{esc(m.get("answer",m.get("question","")))}</p></article>' for m in messages) or '<p class="empty">No saved conversation yet. Ask the Evidence Assistant a question for this inspection, then refresh this report.</p>'
    sources={s['chunk_id']:s for m in messages for s in m.get('evidence',[])}
    source_html=''.join(f'<article><h3>{esc(key)} · {esc(s["title"])}</h3><p>{esc(s["text"])}</p><p class="muted">{esc(s["url"])} · {esc(s["scope"])}</p></article>' for key,s in sources.items()) or '<p class="empty">No document passages saved. Measurement-only answers use the saved inspection directly.</p>'
    verdict=record.get('verdict','Uncertain');tone={'Good':'good','Anomalous':'anomalous','Uncertain':'uncertain'}.get(verdict,'uncertain')
    images=''.join(f'<figure><img src="{image_url(record.get(kind+"_url"))}" alt="{alt}"><figcaption>{caption}</figcaption></figure>' for kind,alt,caption in (
        ('image','Original inspected image','Original image · retained inspection input'),
        ('heatmap','Model anomaly heatmap','Heatmap · feature distance from normal reference patches, not a defect diagnosis')))
    storage=record.get('storage','local_device')
    storage_copy={'supabase_personal':'Private account · Supabase','supabase':'Shared Team · Supabase','browser_session':'Temporary guest workspace · not durable Personal cloud storage','local_account':'Private local mirror · check synchronization for cloud persistence'}.get(storage,'Local device · not automatically cloud-saved')
    if local and storage=='browser_session':storage_copy='Guest inspection · local device only, outside a cloud account'
    def section(index,title,content):
        return f'<section class="card"><div class="section-heading"><h2>{title}</h2><span class="section-no">{index}</span></div>{content}</section>'
    summary=f'<section class="card summary"><div class="metric"><small>Model verdict</small><div><span class="badge {tone}">{esc(verdict)}</span></div></div><div class="metric"><small>Anomaly score</small><strong>{number(record.get("score"))}</strong></div><div class="metric"><small>Decision threshold</small><strong>{number(record.get("threshold"))}</strong></div><div class="metric"><small>Review margin</small><strong>±{number(record.get("uncertainty_margin"))}</strong></div></section>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><title>DefectRAG · Inspection {esc(record.get('id','')[:8])}</title><style>{STYLE}</style></head><body><main>
<header><div class="header-row"><div><div class="eyebrow">DefectRAG · Inspection intelligence</div><h1>Inspection evidence report</h1><p>{esc(record.get('category','').replace('_',' ').title())} · {esc(record.get('created_at',''))}</p></div><button type="button" onclick="window.print()">Print / save PDF</button></div><p>{esc(storage_copy)}</p></header>
{summary}<p class="note">Anomaly scores are feature distances, not accuracy, confidence or defect probability. Localization highlights unusual appearance; it does not establish a defect type or cause. Human review remains necessary.</p>
{section('01','Image and localization','<div class="images">'+images+'</div>')}
{section('02','Inspection measurements','<table aria-label="Saved inspection measurements"><tbody>'+rows+'</tbody></table>')}
{section('03','Human review',review_html)}{section('04','Evidence conversation',evidence)}{section('05','Retrieved documentation',source_html)}
<footer>Report snapshot of saved inspection evidence. Refresh to include later reviews and conversation. Private reports and downloaded PDFs may contain inspection images, filenames, batch labels and staff notes; they are not Community Gallery publications.</footer>
</main></body></html>'''
