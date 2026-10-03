const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const MAX_IMAGE_BYTES = 20 * 1024 * 1024;
const ACCEPTED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/bmp']);

const escapeHtml = (value) => String(value ?? '').replace(
  /[&<>"']/g,
  (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]),
);

const formatBytes = (bytes) => {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / (1024 ** index);
  return `${value.toFixed(index === 0 || value >= 10 ? 0 : 1)} ${units[index]}`;
};

let selectedInspectionFile = null;
let previewUrl = null;
let toastTimer = null;
let progressTimers = [];
let elapsedTimer = null;
let progressStartedAt = 0;
let categoryCapabilities = new Map();

function setSidebar(open) {
  $('#app-sidebar').classList.toggle('open', open);
  $('#sidebar-backdrop').classList.toggle('open', open);
  $('#sidebar-toggle').setAttribute('aria-expanded', String(open));
  document.body.style.overflow = open && window.innerWidth < 1680 ? 'hidden' : '';
}

$('#sidebar-toggle').addEventListener('click', () => setSidebar(true));
$('#sidebar-close').addEventListener('click', () => setSidebar(false));
$('#sidebar-backdrop').addEventListener('click', () => setSidebar(false));
$('#app-sidebar').querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener('click', () => setSidebar(false));
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') setSidebar(false);
});

const observedSections = ['inspector', 'benchmark', 'knowledge', 'about', 'faq', 'support', 'contact'];
if ('IntersectionObserver' in window) {
  const sectionObserver = new IntersectionObserver((entries) => {
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    $$('#app-sidebar nav a').forEach((link) => link.classList.toggle('active', link.getAttribute('href') === `#${visible.target.id}`));
  }, { rootMargin: '-18% 0px -62% 0px', threshold: [0.01, 0.2] });
  observedSections.forEach((id) => {
    const section = document.getElementById(id);
    if (section) sectionObserver.observe(section);
  });
}

function showToast(message, type = 'info') {
  const toast = $('#toast');
  toast.querySelector('span').textContent = message;
  toast.classList.toggle('error', type === 'error');
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 5200);
}

function setButtonLoading(button, loading, label) {
  if (!button.dataset.defaultHtml) button.dataset.defaultHtml = button.innerHTML;
  button.disabled = loading;
  button.setAttribute('aria-busy', String(loading));
  button.innerHTML = loading
    ? `<span class="button-label"><span class="spinner"></span>${escapeHtml(label)}</span>`
    : button.dataset.defaultHtml;
}

async function readJson(response) {
  try {
    return await response.json();
  } catch (_error) {
    return {};
  }
}

function apiError(data, fallback) {
  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.map((item) => item.msg).filter(Boolean).join(' ') || fallback;
  return fallback;
}

async function initialize() {
  const status = $('#status');
  const select = $('#category');
  const readiness = $('#readiness');

  status.className = 'status-chip checking';
  status.innerHTML = '<span class="status-dot"></span><span>Connecting</span>';

  try {
    const response = await fetch('/api/health', { headers: { Accept: 'application/json' } });
    const data = await readJson(response);
    if (!response.ok) throw new Error('Health check failed.');

    const categories = Array.isArray(data.inspection_categories) ? data.inspection_categories : [];
    const readyCategories = categories.filter((item) => item.ready);
    const cloudMediaEnabled = Boolean(data.cloud?.media?.configured);
    $('#storage-consent-row').classList.toggle('hidden', !cloudMediaEnabled);
    $('#storage-consent').required = cloudMediaEnabled;
    select.innerHTML = '<option value="">Select a product category</option>' + categories.map((item) => (
      `<option value="${escapeHtml(item.id)}" ${item.ready ? '' : 'disabled'}>` +
      `${escapeHtml(item.label || item.id)}${item.ready ? '' : ' — normal memory missing'}</option>`
    )).join('');
    categoryCapabilities = new Map(categories.map((item) => [item.id, item.methods || data.scoring_methods || ['baseline']]));
    updateAvailableMethods();

    const fullyReady = Boolean(data.retrieval_ready && readyCategories.length);
    status.className = `status-chip ${fullyReady ? 'ready' : 'checking'}`;
    status.innerHTML = `<span class="status-dot"></span><span>${fullyReady ? `${readyCategories.length} categories ready` : 'Setup required'}</span>`;

    const warnings = [];
    if (!readyCategories.length) warnings.push('No compact memory banks or normal reference features were found. Check the mounted assets and features folders.');
    if (!data.retrieval_ready) warnings.push('The knowledge index is not ready. Build it before generating evidence-grounded reports.');
    if (warnings.length) {
      readiness.textContent = warnings.join(' ');
      readiness.classList.remove('hidden');
      readiness.classList.toggle('error', !readyCategories.length);
    } else {
      readiness.classList.add('hidden');
    }
  } catch (_error) {
    status.className = 'status-chip error';
    status.innerHTML = '<span class="status-dot"></span><span>API unavailable</span>';
    select.innerHTML = '<option value="">Service unavailable</option>';
    readiness.textContent = 'DefectRAG could not reach the API. Confirm the service is running, then refresh this page.';
    readiness.classList.add('error');
    readiness.classList.remove('hidden');
  }
}

function updateAvailableMethods() {
  const category = $('#category').value;
  const methods = new Set(categoryCapabilities.get(category) || ['baseline']);
  $$('#method option').forEach((option) => { option.disabled = !methods.has(option.value); });
  if (!methods.has($('#method').value)) $('#method').value = 'baseline';
  $('#method-help').textContent = category && !methods.has('trained')
    ? 'Trained and fusion need this product’s compact memory bank and seed 42 head. Baseline remains available.'
    : 'Trained and fusion are research scores without calibrated anomaly verdicts. Baseline uses a demonstration threshold.';
}

$('#category').addEventListener('change', updateAvailableMethods);

function validateImage(file) {
  if (!file) return 'Choose an image to inspect.';
  if (!ACCEPTED_IMAGE_TYPES.has(file.type)) return 'Use a JPG, PNG, WebP, or BMP image.';
  if (file.size > MAX_IMAGE_BYTES) return 'The image must be 20 MB or smaller.';
  return '';
}

function clearSelectedImage() {
  selectedInspectionFile = null;
  $('#inspection-file').value = '';
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  $('#preview').removeAttribute('src');
  $('#preview-wrap').classList.add('hidden');
  $('#empty-upload').classList.remove('hidden');
  $('#file-meta').classList.add('hidden');
  $('#file-name').textContent = '';
  $('#file-size').textContent = '';
}

function selectImage(file) {
  const validationMessage = validateImage(file);
  if (validationMessage) {
    clearSelectedImage();
    showToast(validationMessage, 'error');
    return;
  }

  selectedInspectionFile = file;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  $('#preview').src = previewUrl;
  $('#preview-wrap').classList.remove('hidden');
  $('#empty-upload').classList.add('hidden');
  $('#file-meta').classList.remove('hidden');
  $('#file-name').textContent = file.name;
  $('#file-size').textContent = `${formatBytes(file.size)} · ${file.type.replace('image/', '').toUpperCase()}`;
}

const inspectionInput = $('#inspection-file');
const dropzone = $('#dropzone');

inspectionInput.addEventListener('change', (event) => selectImage(event.target.files?.[0]));
$('#remove-file').addEventListener('click', (event) => {
  event.preventDefault();
  event.stopPropagation();
  clearSelectedImage();
});

['dragenter', 'dragover'].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add('dragging');
  });
});

['dragleave', 'drop'].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove('dragging');
  });
});

dropzone.addEventListener('drop', (event) => {
  const file = event.dataTransfer?.files?.[0];
  if (!file) return;
  selectImage(file);
  try {
    const transfer = new DataTransfer();
    transfer.items.add(file);
    inspectionInput.files = transfer.files;
  } catch (_error) {
    // selectedInspectionFile remains the source of truth where DataTransfer is unavailable.
  }
});

dropzone.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    inspectionInput.click();
  }
});

function applyProgressStage(stageIndex, title, detail, percentage) {
  const stages = $$('#pipeline li');
  stages.forEach((stage, index) => {
    stage.classList.toggle('complete', index < stageIndex);
    stage.classList.toggle('active', index === stageIndex);
  });
  $('#progress-title').textContent = title;
  $('#progress-detail').textContent = detail;
  $('#progress-bar').style.width = `${percentage}%`;
}

function startProgress() {
  const progress = $('#analysis-progress');
  progress.classList.remove('hidden');
  progressStartedAt = Date.now();
  $$('#pipeline li').forEach((stage) => stage.classList.remove('active', 'complete'));
  $('#progress-title').textContent = 'Inspection running';
  $('#progress-detail').textContent = 'Waiting for the server. The workflow stages are illustrative, not a live server trace.';
  $('#progress-bar').style.width = '100%';

  const updateElapsed = () => {
    const totalSeconds = Math.floor((Date.now() - progressStartedAt) / 1000);
    const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
    const seconds = String(totalSeconds % 60).padStart(2, '0');
    $('#elapsed').textContent = `${minutes}:${seconds}`;
    if (totalSeconds === 90) $('#progress-detail').textContent = 'This is taking longer than usual. The first request may load DINOv3 and Ollama models; the API log shows the active step.';
    if (totalSeconds === 180) $('#progress-detail').textContent = 'Still waiting for the server. Check the API and Ollama logs; this is not a live stage-by-stage progress indicator.';
  };
  updateElapsed();
  elapsedTimer = setInterval(updateElapsed, 1000);

}

function stopProgress(success = false) {
  progressTimers.forEach(clearTimeout);
  progressTimers = [];
  clearInterval(elapsedTimer);
  elapsedTimer = null;

  if (success) {
    $$('#pipeline li').forEach((stage) => {
      stage.classList.remove('active');
      stage.classList.add('complete');
    });
    $('#progress-title').textContent = 'Inspection complete';
    $('#progress-detail').textContent = 'Your localized report is ready.';
    $('#progress-bar').style.width = '100%';
    setTimeout(() => $('#analysis-progress').classList.add('hidden'), 650);
  } else {
    $('#analysis-progress').classList.add('hidden');
    $$('#pipeline li').forEach((stage) => stage.classList.remove('active', 'complete'));
    $('#progress-bar').style.width = '8%';
  }
}

function formatReport(report) {
  const escaped = escapeHtml(report || 'No inspection explanation was returned.');
  return escaped.split(/\r?\n/).map((line) => {
    const text = line.trim();
    if (!text) return '';
    const withCitations = text.replace(/\[(\d+)\]/g, '<span class="citation">[$1]</span>');
    if (/^\d+\.\s+/.test(text)) return `<h4>${withCitations}</h4>`;
    return `<p>${withCitations}</p>`;
  }).join('');
}

function displayValue(value) {
  if (Array.isArray(value)) return value.filter(Boolean).join(' · ') || 'Not provided';
  if (value && typeof value === 'object') return Object.entries(value).map(([key, item]) => `${key}: ${item}`).join(' · ');
  return String(value ?? '').trim() || 'Not provided';
}

function renderVisualReasoning(visual) {
  const entries = [
    ['Observation', visual.visual_observation],
    ['Local area', visual.local_observation],
    ['Suspected issue', visual.suspected_issue],
    ['Proposed type', visual.possible_anomaly_type],
    ['Evidence', visual.evidence],
    ['Confidence', visual.confidence],
    ['Uncertainty', visual.uncertainty],
  ];

  $('#visual-observation').innerHTML = entries.map(([label, value]) => {
    if (label === 'Confidence') {
      const raw = Number(value);
      const confidence = Number.isFinite(raw) ? Math.max(0, Math.min(1, raw > 1 ? raw / 100 : raw)) : null;
      if (confidence !== null) {
        return `<dt>${label}</dt><dd class="confidence-meter"><span><i style="width:${Math.round(confidence * 100)}%"></i></span><b>${Math.round(confidence * 100)}%</b></dd>`;
      }
    }
    return `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(displayValue(value))}</dd>`;
  }).join('');
}

function renderSources(sources) {
  const safeSources = Array.isArray(sources) ? sources : [];
  $('#source-count').textContent = `${safeSources.length} ${safeSources.length === 1 ? 'SOURCE' : 'SOURCES'}`;
  $('#source-list').innerHTML = safeSources.length ? safeSources.map((source, index) => {
    const rank = Number(source.rank) || index + 1;
    const score = Number(source.score);
    const metadata = [
      source.source || 'Unknown source',
      Number.isFinite(score) ? `retrieval score ${score.toFixed(4)}` : null,
    ].filter(Boolean).join(' · ');
    let verifiedUrl = '';
    try {
      const parsed = new URL(source.source_url);
      if (['https:', 'http:'].includes(parsed.protocol)) verifiedUrl = parsed.href;
    } catch (_error) { /* Text-only sources remain visible without a link. */ }
    return `<details class="source-card">
      <summary><span class="source-title"><span class="source-rank">${String(rank).padStart(2, '0')}</span><b>${escapeHtml(source.title || 'Untitled evidence')}</b></span><i>+</i></summary>
      <div class="source-body">${escapeHtml(source.text || 'No excerpt available.')}
        ${source.evidence_excerpt ? `<p><strong>Reviewed excerpt:</strong> ${escapeHtml(source.evidence_excerpt)}</p>` : ''}
        <div class="source-meta">${escapeHtml(metadata)} ${verifiedUrl ? `<a href="${escapeHtml(verifiedUrl)}" target="_blank" rel="noopener noreferrer">View source ↗</a>` : ''}</div></div>
    </details>`;
  }).join('') : '<div class="inline-alert">No supporting sources were returned for this inspection.</div>';
}

function renderInspection(data) {
  const verdict = String(data.verdict || 'Inspection complete');
  const normalizedVerdict = verdict.toLowerCase();
  const calibrated = data.threshold !== null && data.threshold !== undefined;
  const isAnomaly = !normalizedVerdict.startsWith('no ') && normalizedVerdict.includes('anomal');
  const score = Number(data.anomaly_score);
  const threshold = calibrated ? Number(data.threshold) : NaN;
  const row = data.max_patch?.row ?? '—';
  const column = data.max_patch?.column ?? '—';

  $('#result-summary').className = `result-summary ${!calibrated ? 'status-research' : isAnomaly ? 'status-anomaly' : 'status-normal'}`;
  $('#verdict').textContent = verdict;
  $('#verdict-subtitle').textContent = !calibrated
    ? 'Experimental score only. The highlighted area is a model response, not a confirmed defect.'
    : isAnomaly
      ? 'The image exceeds this category’s operating threshold. Review the located region and evidence below.'
      : 'The image remains within this category’s normal operating threshold.';
  $('#score').textContent = Number.isFinite(score) ? score.toFixed(5) : '—';
  $('#threshold').textContent = Number.isFinite(threshold) ? threshold.toFixed(5) : '—';
  $('#score-track-wrap').classList.toggle('hidden', !calibrated);
  $('#score-note').textContent = calibrated
    ? 'The score measures feature distance from normal references. It is not a probability.'
    : 'No threshold has been calibrated for this method. The score is not a probability or an anomaly verdict.';
  const comparison = data.comparison_scores || {};
  $('#method-comparison').innerHTML = Object.keys(comparison).length
    ? `<strong>Same image · method scores</strong><div>${['baseline', 'trained', 'fusion'].filter((name) => Number.isFinite(Number(comparison[name]))).map((name) => `<span>${escapeHtml(name)}: <b>${Number(comparison[name]).toFixed(5)}</b></span>`).join('')}</div><small>Score scales differ between methods; do not compare their raw values as probabilities.</small>`
    : '';
  $('#patch').textContent = row === '—' ? '—' : `R${row} · C${column}`;

  if (data.artifacts?.location) $('#location-image').src = `${data.artifacts.location}?v=${Date.now()}`;
  if (data.artifacts?.heatmap) $('#heatmap-image').src = `${data.artifacts.heatmap}?v=${Date.now()}`;

  const reference = data.reference_example || {};
  if (reference.available && reference.url) {
    $('#reference-image').src = `${reference.url}${reference.url.includes('?') ? '&' : '?'}v=${Date.now()}`;
    $('#reference-caption').textContent = reference.disclaimer || 'A dataset-verified normal comparison image.';
    $('#reference-card').classList.remove('hidden');
    $('#visual-grid').classList.add('has-reference');
  } else {
    $('#reference-card').classList.add('hidden');
    $('#visual-grid').classList.remove('has-reference');
  }

  const pixelBox = data.bounding_box?.pixel;
  $('#bbox-label').textContent = pixelBox
    ? `Box ${pixelBox.x_min},${pixelBox.y_min} → ${pixelBox.x_max},${pixelBox.y_max}`
    : 'Strongest deviation';

  const scorePosition = Number.isFinite(score) && Number.isFinite(threshold) && threshold > 0
    ? Math.min(Math.max((score / (threshold * 1.5)) * 100, 2), 98)
    : 2;
  $('#score-fill').style.width = `${scorePosition}%`;
  $('#score-marker').style.left = `${scorePosition}%`;
  $('#score-marker').style.borderColor = isAnomaly ? 'var(--red)' : 'var(--teal)';
  $('#threshold-marker').style.left = '66.66%';

  $('#explanation').innerHTML = formatReport(data.explanation);
  const evidenceStatus = data.evidence_status;
  $('#evidence-status').textContent = evidenceStatus?.message || 'Source coverage was not reported by this deployment.';
  $('#evidence-status').classList.toggle('limited', !evidenceStatus?.product_rules_available);
  const timing = data.timing_seconds;
  $('#inspection-timing').textContent = timing?.total != null ? `Space processing: ${Number(timing.total).toFixed(1)} s · network/queue additional` : '';
  renderVisualReasoning(data.visual_reasoning || {});
  renderSources(data.sources);
  const assurance = data.reasoning_assurance || {};
  $('#assurance-detector').textContent = assurance.detector_claim || 'The box marks the strongest feature deviation.';
  $('#assurance-visual').textContent = assurance.visual_claim || 'Visible details are separated from interpretation.';
  $('#assurance-evidence').textContent = assurance.evidence_claim || 'Product rules require a numbered source.';
  $('#result').classList.remove('hidden');
  setTimeout(() => $('#result').scrollIntoView({ behavior: 'smooth', block: 'start' }), 180);
}

$('#inspect-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const file = selectedInspectionFile || inspectionInput.files?.[0];
  const category = $('#category').value;
  const method = $('#method').value;
  const validationMessage = validateImage(file);
  if (validationMessage) {
    showToast(validationMessage, 'error');
    dropzone.focus();
    return;
  }
  if (!category) {
    showToast('Select the product category that matches the image.', 'error');
    $('#category').focus();
    return;
  }
  if (!$('#storage-consent-row').classList.contains('hidden') && !$('#storage-consent').checked) {
    showToast('Confirm the cloud image-retention notice before inspection.', 'error');
    $('#storage-consent').focus();
    return;
  }

  const form = new FormData();
  form.append('file', file);
  $('#result').classList.add('hidden');
  setButtonLoading($('#inspect-button'), true, 'Inspecting image…');
  startProgress();

  try {
    const response = await fetch(`/api/inspect?category=${encodeURIComponent(category)}&method=${encodeURIComponent(method)}`, { method: 'POST', body: form });
    const data = await readJson(response);
    if (!response.ok) throw new Error(apiError(data, `Inspection failed (HTTP ${response.status}). Check the API logs for the cause.`));
    renderInspection(data);
    stopProgress(true);
    showToast('Inspection complete. The localized report is ready.');
  } catch (error) {
    stopProgress(false);
    showToast(error.message || 'The inspection could not be completed.', 'error');
  } finally {
    setButtonLoading($('#inspect-button'), false);
  }
});

$('#ask-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = $('#ask-button');
  const answer = $('#answer');
  const question = $('#question').value.trim();
  if (!question) return;

  setButtonLoading(button, true, 'Searching knowledge…');
  answer.classList.remove('hidden', 'error');
  answer.textContent = 'Retrieving relevant evidence and generating an answer…';
  try {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, category: $('#ask-category').value, top_k: 5 }),
    });
    const data = await readJson(response);
    if (!response.ok) throw new Error(apiError(data, 'The knowledge request failed.'));
    const references = Array.isArray(data.sources) ? data.sources : [];
    answer.textContent = (data.answer || 'No answer was returned.') +
      (references.length ? '\n\nSources: ' + references.map((source, index) => `[${index + 1}] ${source.title || source.source || 'Untitled'}`).join(' · ') : '');
  } catch (error) {
    answer.textContent = error.message;
    answer.classList.add('error');
  } finally {
    setButtonLoading(button, false);
  }
});

$('#contact-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = $('#contact-button');
  const responseBox = $('#contact-response');
  const payload = {
    name: $('#contact-name').value.trim(),
    email: $('#contact-email').value.trim(),
    topic: $('#contact-topic').value,
    message: $('#contact-message').value.trim(),
  };
  if (payload.name.length < 2 || !/^\S+@\S+\.\S+$/.test(payload.email) || payload.message.length < 10) {
    responseBox.textContent = 'Enter your name, a valid email address, and at least 10 characters in the message.';
    responseBox.classList.remove('hidden');
    responseBox.classList.add('error');
    return;
  }

  setButtonLoading(button, true, 'Sending message…');
  responseBox.textContent = 'Saving your support request securely…';
  responseBox.classList.remove('hidden', 'error');
  try {
    const response = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await readJson(response);
    if (!response.ok) throw new Error(apiError(data, 'Your message could not be sent.'));
    responseBox.textContent = `Message received. Reference: ${data.message_id}`;
    $('#contact-form').reset();
    showToast('Your support message was received.');
  } catch (error) {
    responseBox.textContent = error.message;
    responseBox.classList.add('error');
  } finally {
    setButtonLoading(button, false);
  }
});

$('#toast button').addEventListener('click', () => {
  clearTimeout(toastTimer);
  $('#toast').classList.remove('show');
});

initialize();
