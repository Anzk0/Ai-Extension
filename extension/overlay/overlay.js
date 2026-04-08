const SERVER = 'http://localhost:5000';

const panel = document.getElementById('panel');
const miniBtn = document.getElementById('mini-btn');
const topicSelect = document.getElementById('topic-select');
const chatArea = document.getElementById('chat-area');
const questionInput = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');
const minimiseBtn = document.getElementById('minimise-btn');
const closeBtn = document.getElementById('close-btn');
const indexBtn = document.getElementById('index-btn');
const serverWarning = document.getElementById('server-warning');

// --- Server health check ---

async function checkServer() {
  try {
    const res = await fetch(`${SERVER}/status`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) {
      serverWarning.classList.add('hidden');
      return true;
    }
  } catch {
    // fall through
  }
  serverWarning.classList.remove('hidden');
  return false;
}

// --- Topic loading ---

async function loadTopics() {
  try {
    const res = await fetch(`${SERVER}/topics`);
    const data = await res.json();
    const current = topicSelect.value;
    topicSelect.innerHTML = '<option value="">Select a topic...</option>';
    (data.topics || []).sort().forEach(topic => {
      const opt = document.createElement('option');
      opt.value = topic;
      opt.textContent = topic;
      if (topic === current) opt.selected = true;
      topicSelect.appendChild(opt);
    });
  } catch (e) {
    console.error('[StudyAI] Failed to load topics', e);
  }
}

// --- Chat rendering ---

function addMessage(role, text, sources = []) {
  // Remove welcome text on first message
  const welcome = chatArea.querySelector('.welcome');
  if (welcome) welcome.remove();

  const div = document.createElement('div');
  div.className = `message ${role}`;

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  div.appendChild(bubble);

  if (sources.length > 0) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'sources';
    sourcesDiv.innerHTML = `Sources: ${sources.map(s => `<span class="source-name">${s}</span>`).join(', ')}`;
    div.appendChild(sourcesDiv);
  }

  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
  return div;
}

// --- Send question ---

async function sendQuestion() {
  const question = questionInput.value.trim();
  if (!question) return;

  const topic = topicSelect.value;
  if (!topic) {
    addMessage('assistant', 'Please select a topic from the dropdown first.');
    return;
  }

  questionInput.value = '';
  addMessage('user', question);

  const loadingDiv = addMessage('assistant', 'Thinking...');
  loadingDiv.querySelector('.bubble').style.color = '#666';
  loadingDiv.querySelector('.bubble').style.fontStyle = 'italic';

  try {
    const res = await fetch(`${SERVER}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, topic })
    });
    const data = await res.json();
    loadingDiv.remove();
    if (data.error) {
      addMessage('assistant', `Error: ${data.error}`);
    } else {
      addMessage('assistant', data.answer, data.sources || []);
    }
  } catch {
    loadingDiv.remove();
    addMessage('assistant', 'Could not reach the companion server. Make sure it is running.');
  }
}

// --- Event listeners ---

sendBtn.addEventListener('click', sendQuestion);
questionInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendQuestion(); });

minimiseBtn.addEventListener('click', () => {
  panel.classList.add('hidden');
  miniBtn.classList.remove('hidden');
  window.parent.postMessage({ type: 'MINIMISE_OVERLAY' }, '*');
});

miniBtn.addEventListener('click', () => {
  miniBtn.classList.add('hidden');
  panel.classList.remove('hidden');
  window.parent.postMessage({ type: 'EXPAND_OVERLAY' }, '*');
});

closeBtn.addEventListener('click', () => {
  window.parent.postMessage({ type: 'CLOSE_OVERLAY' }, '*');
});

indexBtn.addEventListener('click', async () => {
  indexBtn.disabled = true;
  indexBtn.textContent = '...';
  try {
    const res = await fetch(`${SERVER}/index`, { method: 'POST' });
    const data = await res.json();
    await loadTopics();
    addMessage('assistant', `Vault indexed. ${data.indexed || 0} chunks stored.`);
  } catch {
    addMessage('assistant', 'Re-indexing failed. Is the server running?');
  } finally {
    indexBtn.disabled = false;
    indexBtn.innerHTML = '&#8635;';
  }
});

// --- Receive highlight from content.js ---

window.addEventListener('message', event => {
  if (!event.data) return;
  if (event.data.type === 'HIGHLIGHTED_TEXT') {
    questionInput.value = event.data.text;
    questionInput.focus();
  }
  if (event.data.type === 'SET_MINIMISED') {
    if (event.data.value) {
      panel.classList.add('hidden');
      miniBtn.classList.remove('hidden');
    } else {
      miniBtn.classList.add('hidden');
      panel.classList.remove('hidden');
    }
  }
});

// --- Init ---

checkServer().then(ok => { if (ok) loadTopics(); });
setInterval(() => checkServer().then(ok => { if (ok) loadTopics(); }), 15000);
