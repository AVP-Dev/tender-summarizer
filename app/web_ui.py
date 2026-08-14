"""Minimal HTML page for manually testing /summarize without curl or /docs.

Compact layout: all controls in a single card, result inline, history
as a short list. Designed to fit on one screen without scrolling.
"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%232563eb'/><text x='16' y='23' font-size='20' font-weight='bold' text-anchor='middle' fill='white' font-family='system-ui'>T</text></svg>">
<title>Tender Document Summarizer</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f2f5; color: #1a1a1a; padding: 24px; }
  .card { background: #fff; border-radius: 12px; padding: 20px; margin: 0 auto; max-width: 640px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
  h1 { font-size: 1.15rem; margin-bottom: 4px; }
  .sub { font-size: .82rem; color: #888; margin-bottom: 14px; }

  .row { display: flex; gap: 8px; margin-bottom: 10px; align-items: flex-end; }
  .row > label { flex: 1; }
  .row > label.wide { flex: none; width: 200px; }
  label { font-size: .75rem; color: #666; display: flex; flex-direction: column; gap: 3px; }
  select, input[type=text], input[type=password] { width: 100%; padding: 6px 8px; border: 1px solid #d0d0d0; border-radius: 6px; font-size: .88rem; }
  select { cursor: pointer; }

  #drop { border: 1.5px dashed #bbb; border-radius: 8px; padding: 16px; text-align: center; cursor: pointer; transition: border-color .12s; margin-bottom: 10px; }
  #drop.drag { border-color: #333; background: #fafafa; }
  #drop p { color: #666; font-size: .85rem; }
  input[type=file] { display: none; }

  #status { font-size: .82rem; color: #666; margin-bottom: 6px; }
  .error { color: #b00020; }

  #result { background: #f8f9fa; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px 16px; font-size: .88rem; line-height: 1.5; white-space: pre-wrap; display: none; margin-bottom: 12px; max-height: 320px; overflow-y: auto; }

  .loading { display: none; align-items: center; gap: 10px; margin-bottom: 10px; }
  .loading.active { display: flex; }
  .spinner { width: 18px; height: 18px; border: 2.5px solid #e0e0e0; border-top-color: #2563eb; border-radius: 50%; animation: spin .7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-text { font-size: .82rem; color: #666; }
  .loading-text::after { content: ''; animation: dots 1.4s steps(4, end) infinite; }
  @keyframes dots {
    0%   { content: ''; }
    25%  { content: '.'; }
    50%  { content: '..'; }
    75%  { content: '...'; }
    100% { content: ''; }
  }

  .hist-title { font-size: .82rem; font-weight: 600; color: #666; margin-bottom: 6px; border-top: 1px solid #eee; padding-top: 10px; }
  .hist-item { font-size: .78rem; padding: 6px 8px; border-bottom: 1px solid #f3f3f3; cursor: pointer; border-radius: 4px; transition: background .1s; overflow: hidden; }
  .hist-item:hover { background: #f0f4ff; }
  .hist-item:last-child { border-bottom: none; }
  .hist-item.active { background: #e8eeff; }
  .hist-hdr { display: flex; justify-content: space-between; gap: 8px; color: #888; margin-bottom: 2px; }
  .hist-hdr b { color: #333; }
  .hist-fname { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; flex: 1; }
  .hist-time { white-space: nowrap; flex-shrink: 0; }
  .hist-txt { color: #555; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .empty { color: #bbb; font-size: .78rem; }
</style>
</head>
<body>
<div class="card">
  <h1>Tender Summarizer</h1>
  <p class="sub">PDF тендерной документации → сумма, сроки, требования, штрафы</p>

  <div class="row">
    <label class="wide">Провайдер
      <select id="provider">
        <option value="ollama">Ollama (локально)</option>
        <option value="nvidia">NVIDIA NIM (Step 3.7)</option>
        <option value="deepseek">DeepSeek</option>
      </select>
    </label>
  </div>

  <div id="ollama-fields" class="row">
    <label>Адрес
      <input type="text" id="host" placeholder="http://localhost:11434">
    </label>
    <label>Модель
      <input type="text" id="model" placeholder="llama3.1:8b">
    </label>
  </div>

  <div id="nvidia-fields" class="row" style="display:none">
    <label>API-ключ NVIDIA
      <input type="password" id="nvidiaKey" placeholder="ключ с build.nvidia.com">
    </label>
    <label>Модель
      <input type="text" id="nvidiaModel" value="stepfun-ai/step-3.7-flash">
    </label>
  </div>

  <div id="deepseek-fields" class="row" style="display:none">
    <label>API-ключ DeepSeek
      <input type="password" id="deepseekKey" placeholder="ключ с platform.deepseek.com">
    </label>
    <label>Модель
      <input type="text" id="deepseekModel" value="deepseek-ai/deepseek-v4-flash">
    </label>
    <label>Base URL
      <input type="text" id="deepseekUrl" value="https://api.deepseek.com">
    </label>
  </div>

  <div id="drop">
    <p>Перетащите PDF сюда или нажмите</p>
    <input type="file" id="file" accept="application/pdf">
  </div>

  <div id="status"></div>
  <div class="loading" id="loading"><div class="spinner"></div><span class="loading-text">Обрабатываю документ</span></div>
  <div id="result"></div>

  <div id="history">
    <div class="hist-title">История</div>
    <div id="historyList"></div>
  </div>
</div>

<script>
const providerEl = document.getElementById('provider');
const ollamaFields = document.getElementById('ollama-fields');
const nvidiaFields = document.getElementById('nvidia-fields');
const deepseekFields = document.getElementById('deepseek-fields');
const drop = document.getElementById('drop');
const fileInput = document.getElementById('file');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const historyList = document.getElementById('historyList');
const loadingEl = document.getElementById('loading');
let history = [];

function updateFields() {
  const v = providerEl.value;
  ollamaFields.style.display = v === 'ollama' ? 'flex' : 'none';
  nvidiaFields.style.display = v === 'nvidia' ? 'flex' : 'none';
  deepseekFields.style.display = v === 'deepseek' ? 'flex' : 'none';
}
providerEl.addEventListener('change', updateFields);
updateFields();

drop.addEventListener('click', () => fileInput.click());
drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('drag'); });
drop.addEventListener('dragleave', () => drop.classList.remove('drag'));
drop.addEventListener('drop', (e) => { e.preventDefault(); drop.classList.remove('drag'); if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]); });
fileInput.addEventListener('change', () => { if (fileInput.files.length) uploadFile(fileInput.files[0]); });

function renderHistory() {
  if (!history.length) { historyList.innerHTML = '<span class="empty">нет запросов</span>'; return; }
  historyList.innerHTML = '';
  history.slice().reverse().forEach((item, idx) => {
    const d = document.createElement('div');
    d.className = 'hist-item';
    d.onclick = () => showHistoryItem(history.length - 1 - idx, d);

    const hdr = document.createElement('div');
    hdr.className = 'hist-hdr';

    const prov = document.createElement('span');
    prov.innerHTML = '<b>' + item.provider + '</b>';

    const fname = document.createElement('span');
    fname.className = 'hist-fname';
    fname.textContent = item.filename;
    fname.title = item.filename;

    const time = document.createElement('span');
    time.className = 'hist-time';
    time.textContent = item.time;

    hdr.appendChild(prov);
    hdr.appendChild(fname);
    hdr.appendChild(time);

    const txt = document.createElement('div');
    txt.className = 'hist-txt';
    txt.textContent = (item.summary || '').slice(0, 120) + ((item.summary || '').length > 120 ? '…' : '');

    d.appendChild(hdr);
    d.appendChild(txt);
    historyList.appendChild(d);
  });
}

function showHistoryItem(idx, el) {
  const item = history[idx];
  if (!item) return;
  document.querySelectorAll('.hist-item').forEach(e => e.classList.remove('active'));
  el.classList.add('active');
  statusEl.textContent = item.filename + ' · ' + item.provider;
  statusEl.classList.remove('error');
  resultEl.textContent = item.summary || '(пустой ответ)';
  resultEl.style.display = 'block';
}
renderHistory();

function addToHistory(filename, provider, model, summary) {
  history.push({ filename, provider, model, summary, time: new Date().toLocaleTimeString() });
  renderHistory();
}

async function uploadFile(file) {
  resultEl.style.display = 'none';
  statusEl.textContent = '';
  loadingEl.classList.add('active');

  const fd = new FormData();
  fd.append('file', file);
  fd.append('provider', providerEl.value);

  const v = providerEl.value;
  if (v === 'ollama') {
    fd.append('host', document.getElementById('host').value);
    fd.append('model', document.getElementById('model').value);
  } else if (v === 'nvidia') {
    fd.append('api_key', document.getElementById('nvidiaKey').value);
    fd.append('model', document.getElementById('nvidiaModel').value);
    fd.append('base_url', 'https://integrate.api.nvidia.com/v1');
  } else if (v === 'deepseek') {
    fd.append('api_key', document.getElementById('deepseekKey').value);
    fd.append('model', document.getElementById('deepseekModel').value);
    fd.append('base_url', document.getElementById('deepseekUrl').value);
  }

  try {
    const res = await fetch('/summarize', { method: 'POST', body: fd });
    const data = await res.json();
    loadingEl.classList.remove('active');
    if (!res.ok) { statusEl.textContent = 'Ошибка: ' + (data.detail || res.statusText); statusEl.classList.add('error'); return; }
    statusEl.textContent = 'Готово.';
    resultEl.textContent = data.summary || '(пустой ответ)';
    resultEl.style.display = 'block';
    const usedModel = v === 'ollama' ? document.getElementById('model').value
      : v === 'nvidia' ? document.getElementById('nvidiaModel').value
      : document.getElementById('deepseekModel').value;
    addToHistory(file.name, providerEl.value, usedModel, data.summary || '');
  } catch (err) {
    loadingEl.classList.remove('active');
    statusEl.textContent = 'Не удалось связаться с сервером: ' + err;
    statusEl.classList.add('error');
  }
}
</script>
</body>
</html>
"""
