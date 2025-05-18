let currentThreadId = null;
let deepResearch = false;

// Utility: format datetime
function formatDateTime(dtStr) {
    if (!dtStr) return '';
    const d = new Date(dtStr);
    return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
}

// Load threads into sidebar
function loadThreads(selectedId = null) {
    fetch('/chat/api/threads/')
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById('thread-list');
            list.innerHTML = '';
            data.threads.forEach(thread => {
                const li = document.createElement('li');
                li.textContent = `#${thread.thread_id.slice(0, 8)} — ${formatDateTime(thread.updated_at)}`;
                li.dataset.threadId = thread.thread_id;
                if (thread.thread_id === selectedId) li.classList.add('selected');
                li.onclick = () => selectThread(thread.thread_id);
                list.appendChild(li);
            });
        });
}

// Load messages for a thread
function loadMessages(threadId) {
    fetch(`/chat/api/thread/${threadId}/`)
        .then(res => res.json())
        .then(data => {
            const chat = document.getElementById('chat-messages');
            chat.innerHTML = '';
            data.messages.forEach(msg => {
                const div = document.createElement('div');
                div.classList.add('message-box');
                if (msg.type === 'human') {
                    div.classList.add('message-human');
                } else {
                    div.classList.add('message-ai');
                }
                div.textContent = msg.content;
                chat.appendChild(div);
            });
            chat.scrollTop = chat.scrollHeight;
        });
}

// Select a thread from sidebar
function selectThread(threadId) {
    currentThreadId = threadId;
    loadThreads(threadId);
    loadMessages(threadId);
}

// Start new chat
function startNewChat() {
    currentThreadId = null;
    document.getElementById('chat-messages').innerHTML = '';
    loadThreads(null);
}

// Send a message
function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    input.value = '';
    input.disabled = true;
    document.getElementById('send-btn').disabled = true;

    fetch('/chat/api/send/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
        body: JSON.stringify({
            thread_id: currentThreadId,
            message: message,
            deep_research: deepResearch
        })
    })
    .then(res => res.json())
    .then(data => {
        currentThreadId = data.thread_id;
        loadThreads(currentThreadId);
        // Render all messages (including the new one and AI response)
        const chat = document.getElementById('chat-messages');
        chat.innerHTML = '';
        data.messages.forEach(msg => {
            const div = document.createElement('div');
            div.classList.add('message-box');
            if (msg.type === 'human') {
                div.classList.add('message-human');
            } else {
                div.classList.add('message-ai');
            }
            div.textContent = msg.content;
            chat.appendChild(div);
        });
        chat.scrollTop = chat.scrollHeight;
    })
    .catch(() => alert('Error sending message.'))
    .finally(() => {
        input.disabled = false;
        document.getElementById('send-btn').disabled = false;
        input.focus();
    });
}

// Get CSRF token from cookie
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name + '=')) {
            return decodeURIComponent(c.substring(name.length + 1));
        }
    }
    return '';
}

// Toggle deep research
function setupDeepResearchToggle() {
    const toggle = document.getElementById('deep-research-toggle');
    toggle.checked = false;
    toggle.onchange = () => {
        deepResearch = toggle.checked;
    };
}

// Event listeners
window.onload = function() {
    loadThreads();
    setupDeepResearchToggle();

    document.getElementById('new-chat-btn').onclick = startNewChat;
    document.getElementById('send-btn').onclick = sendMessage;
    document.getElementById('chat-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') sendMessage();
    });
};
