"""Minimal HTML page for manually testing /summarize without curl or /docs.

Kept as a single inline template (no Jinja2, no static file build step) —
this is a demo aid for reviewers, not a production frontend, so the
simplest thing that works is the right amount of engineering here.
"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Tender Document Summarizer</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 640px; margin: 60px auto; padding: 0 20px; color: #1a1a1a; }
  h1 { font-size: 1.3rem; margin-bottom: 4px; }
  p.sub { color: #666; margin-top: 0; }
  #drop { border: 2px dashed #bbb; border-radius: 10px; padding: 40px; text-align: center; cursor: pointer; transition: border-color .15s; }
  #drop.drag { border-color: #333; background: #fafafa; }
  #drop p { margin: 0; color: #666; }
  input[type=file] { display: none; }
  #status { margin-top: 16px; font-size: .9rem; color: #666; }
  pre { background: #f5f5f5; border-radius: 8px; padding: 16px; overflow-x: auto; font-size: .85rem; margin-top: 16px; white-space: pre-wrap; }
  .error { color: #b00020; }
</style>
</head>
<body>
  <h1>Tender Document Summarizer</h1>
  <p class="sub">Загрузите PDF тендерной документации — сервис вернёт сумму контракта, сроки, требования и штрафы.</p>

  <div id="drop">
    <p>Перетащите PDF сюда или нажмите, чтобы выбрать файл</p>
    <input type="file" id="file" accept="application/pdf">
  </div>

  <div id="status"></div>
  <pre id="result" style="display:none"></pre>

<script>
const drop = document.getElementById('drop');
const fileInput = document.getElementById('file');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');

drop.addEventListener('click', () => fileInput.click());
drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('drag'); });
drop.addEventListener('dragleave', () => drop.classList.remove('drag'));
drop.addEventListener('drop', (e) => {
  e.preventDefault();
  drop.classList.remove('drag');
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
  resultEl.style.display = 'none';
  statusEl.textContent = `Обрабатываю ${file.name}... это может занять до пары минут на локальной модели.`;
  statusEl.classList.remove('error');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/summarize', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) {
      statusEl.textContent = `Ошибка: ${data.detail || res.statusText}`;
      statusEl.classList.add('error');
      return;
    }
    statusEl.textContent = 'Готово.';
    resultEl.textContent = JSON.stringify(data, null, 2);
    resultEl.style.display = 'block';
  } catch (err) {
    statusEl.textContent = `Не удалось связаться с сервером: ${err}`;
    statusEl.classList.add('error');
  }
}
</script>
</body>
</html>
"""
