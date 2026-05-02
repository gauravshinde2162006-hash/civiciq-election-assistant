const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message');
const quickActions = document.getElementById('quick-actions');

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderAssistantMessage(data) {
  const steps = Array.isArray(data.steps) && data.steps.length
    ? `<ol>${data.steps.map((step) => `<li>${escapeHtml(step)}</li>`).join('')}</ol>`
    : '';
  const details = Array.isArray(data.details) && data.details.length
    ? `<p>${data.details.map((detail) => escapeHtml(detail)).join(' ')}</p>`
    : '';

  return `
    <div class="message assistant">
      <h3>${escapeHtml(data.title || 'Election Assistant')}</h3>
      <p>${escapeHtml(data.summary || 'No summary available.')}</p>
      ${steps}
      ${details}
    </div>
  `;
}

function appendMessage(html) {
  chatWindow.insertAdjacentHTML('beforeend', html);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addUserMessage(text) {
  appendMessage(`<div class="message user">${escapeHtml(text)}</div>`);
}

async function sendMessage(text) {
  const cleaned = text.trim();
  if (!cleaned) {
    return;
  }

  addUserMessage(cleaned);
  messageInput.value = '';

  appendMessage('<div class="message assistant">Thinking about the best guidance...</div>');
  const loadingMessage = chatWindow.lastElementChild;

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: cleaned }),
    });

    const data = await response.json();

    loadingMessage.remove();

    if (!response.ok) {
      appendMessage(`<div class="message assistant">${escapeHtml(data.error || 'Something went wrong.')}</div>`);
      return;
    }

    appendMessage(renderAssistantMessage(data));
  } catch (error) {
    loadingMessage.remove();
    appendMessage('<div class="message assistant">Unable to reach the server. Please try again.</div>');
  }
}

async function loadTopics() {
  try {
    const response = await fetch('/api/topics');
    const data = await response.json();

    quickActions.innerHTML = '';
    data.topics.forEach((topic) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = topic.label;
      button.addEventListener('click', () => sendMessage(topic.message));
      quickActions.appendChild(button);
    });
  } catch (error) {
    quickActions.innerHTML = '<button type="button" disabled>Topics unavailable</button>';
  }
}

chatForm.addEventListener('submit', (event) => {
  event.preventDefault();
  sendMessage(messageInput.value);
});

messageInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && event.shiftKey) {
    event.preventDefault();
  }
});

appendMessage(`
  <div class="message assistant">
    <h3>Welcome</h3>
    <p>Choose a quick topic or ask your own election question.</p>
    <ol>
      <li>Register to vote</li>
      <li>Learn the voting process</li>
      <li>Check the election timeline</li>
    </ol>
  </div>
`);

loadTopics();
