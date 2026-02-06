const logEl = document.getElementById('log');
const tableWrap = document.getElementById('tableWrap');
const runBtn = document.getElementById('runBtn');
const downloadBtn = document.getElementById('downloadBtn');

let latestResult = null;

function log(msg) {
  logEl.textContent += `${new Date().toLocaleTimeString()} ${msg}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

async function fileToText(file) {
  const lower = file.name.toLowerCase();
  if (lower.endsWith('.txt') || lower.endsWith('.md') || lower.endsWith('.csv')) {
    return await file.text();
  }

  if (lower.endsWith('.pdf') || lower.endsWith('.doc') || lower.endsWith('.docx')) {
    const buf = await file.arrayBuffer();
    const view = new Uint8Array(buf);
    const head = Array.from(view.slice(0, 1600)).map((n) => (n >= 32 && n <= 126 ? String.fromCharCode(n) : ' ')).join('');
    return `[文件名] ${file.name}\n[提示] 浏览器端无法稳定提取该格式全文，已附带文件头特征用于AI推断，请用户尽量补充标准条文文本。\n[头部特征]\n${head}`;
  }

  return `[文件名] ${file.name}\n[提示] 该格式未适配文本抽取，请将关键内容粘贴到“补充审查要求”。`;
}

function buildPrompt(reportTexts, standardTexts) {
  return `你是一名严谨的工程咨询文档审查专家。请对给定报告逐条审查，覆盖但不限于：\n- 各类规划报告\n- 交通影响评价报告\n- 招标材料\n\n请结合用户提供的审查标准/意见；若标准不足，可补充常见公开规范通行要求（需说明“通行做法”）。\n\n输出必须为 JSON 数组，不要输出其它文字。\n每个数组元素字段：\n- item: 审查条目\n- basis: 依据（标准条款/通行做法）\n- issue: 发现的问题\n- reason: 问题原因\n- fix: 修改措施\n- example: 修改示范（示例文本）\n- conclusion: 结论（通过/需修改/重大问题）\n\n报告内容：\n${reportTexts.join('\n\n---\n\n')}\n\n审查标准与意见：\n${standardTexts.join('\n\n---\n\n')}`;
}

function renderTable(items) {
  const headers = ['审查条目', '依据', '问题', '原因', '修改措施', '修改示范', '结论'];
  const keys = ['item', 'basis', 'issue', 'reason', 'fix', 'example', 'conclusion'];
  const rows = items.map((it) => `<tr>${keys.map((k) => `<td>${(it[k] || '').toString().replace(/</g, '&lt;')}</td>`).join('')}</tr>`).join('');
  tableWrap.innerHTML = `<table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
}

function downloadWord(items) {
  const html = `<!doctype html><html><head><meta charset="utf-8"></head><body>
  <h2>文档审查报告</h2>
  <p>生成时间：${new Date().toLocaleString()}</p>
  <table border="1" style="border-collapse:collapse;width:100%">
    <tr><th>审查条目</th><th>依据</th><th>问题</th><th>原因</th><th>修改措施</th><th>修改示范</th><th>结论</th></tr>
    ${items.map((it) => `<tr><td>${it.item || ''}</td><td>${it.basis || ''}</td><td>${it.issue || ''}</td><td>${it.reason || ''}</td><td>${it.fix || ''}</td><td>${it.example || ''}</td><td>${it.conclusion || ''}</td></tr>`).join('')}
  </table></body></html>`;

  const blob = new Blob(['\ufeff', html], { type: 'application/msword' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '审查报告.doc';
  a.click();
  URL.revokeObjectURL(url);
}

async function runReview() {
  logEl.textContent = '';
  tableWrap.innerHTML = '';
  downloadBtn.disabled = true;

  const apiKey = document.getElementById('apiKey').value.trim();
  const baseUrl = document.getElementById('baseUrl').value.trim().replace(/\/$/, '');
  const model = document.getElementById('model').value;

  if (!apiKey) {
    alert('请填写 DeepSeek API Key');
    return;
  }

  const reportFiles = [...document.getElementById('reportFiles').files];
  const standardFiles = [...document.getElementById('standardFiles').files];
  const standardText = document.getElementById('standardText').value.trim();

  if (!reportFiles.length) {
    alert('请至少上传一个待审查报告文件');
    return;
  }

  log('读取报告文件...');
  const reportTexts = [];
  for (const f of reportFiles) {
    reportTexts.push(await fileToText(f));
  }

  log('读取审查标准文件...');
  const standardTexts = [];
  for (const f of standardFiles) {
    standardTexts.push(await fileToText(f));
  }
  if (standardText) standardTexts.push(standardText);

  const prompt = buildPrompt(reportTexts, standardTexts.length ? standardTexts : ['未提供明确标准，请基于常见规范做法审查并标注通行做法。']);

  log('调用 DeepSeek 审查中...');
  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      temperature: 0.2,
      messages: [
        { role: 'system', content: '你输出严格 JSON，不得包含 markdown 代码块。' },
        { role: 'user', content: prompt },
      ],
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`DeepSeek 请求失败: ${response.status} ${errText}`);
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content || '[]';

  let items;
  try {
    items = JSON.parse(content);
  } catch {
    const start = content.indexOf('[');
    const end = content.lastIndexOf(']');
    items = JSON.parse(content.slice(start, end + 1));
  }

  if (!Array.isArray(items)) {
    throw new Error('模型输出不是 JSON 数组');
  }

  latestResult = items;
  renderTable(items);
  log(`审查完成，共 ${items.length} 条。`);
  downloadBtn.disabled = false;
}

runBtn.addEventListener('click', async () => {
  runBtn.disabled = true;
  try {
    await runReview();
  } catch (err) {
    log(`错误：${err.message}`);
  } finally {
    runBtn.disabled = false;
  }
});

downloadBtn.addEventListener('click', () => {
  if (!latestResult) return;
  downloadWord(latestResult);
});
