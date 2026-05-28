// ══════════════════════════════════════════════
//  EDUGENIE — Frontend Logic
// ══════════════════════════════════════════════

const API = '';

// ──────────────────────────────────────────────
// AUTH
// ──────────────────────────────────────────────

function showTab(tab) {
    document.getElementById('loginForm')?.classList.toggle('hidden', tab !== 'login');
    document.getElementById('registerForm')?.classList.toggle('hidden', tab !== 'register');
    document.getElementById('loginTab')?.classList.toggle('active', tab === 'login');
    document.getElementById('regTab')?.classList.toggle('active', tab === 'register');
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorEl  = document.getElementById('loginError');
    hideEl(errorEl);

    if (!username || !password) { showError(errorEl, 'Please enter your username and password.'); return; }

    try {
        const res  = await fetch(`${API}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();

        if (data.status === 'success') {
            sessionStorage.setItem('username', data.username);
            sessionStorage.setItem('role',     data.role);
            window.location.href = '/dashboard';
        } else {
            showError(errorEl, data.message || 'Login failed.');
        }
    } catch {
        showError(errorEl, 'Could not connect to server. Is the app running?');
    }
}

async function handleRegister() {
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value;
    const role     = document.getElementById('regRole').value;
    const errorEl  = document.getElementById('regError');
    hideEl(errorEl);

    if (!username || !password) { showError(errorEl, 'Please fill in all fields.'); return; }
    if (password.length < 6)    { showError(errorEl, 'Password must be at least 6 characters.'); return; }

    try {
        const res  = await fetch(`${API}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });
        const data = await res.json();

        if (data.status === 'success') {
            showTab('login');
            const loginErr = document.getElementById('loginError');
            if (loginErr) {
                loginErr.style.color      = '#86EFAC';
                loginErr.style.background = 'rgba(34,197,94,0.1)';
                loginErr.style.border     = '1px solid rgba(34,197,94,0.2)';
                loginErr.textContent      = '✅ Account created! You can now log in.';
                loginErr.classList.remove('hidden');
            }
            document.getElementById('loginUsername').value = username;
        } else {
            showError(errorEl, data.message || 'Registration failed.');
        }
    } catch {
        showError(errorEl, 'Could not connect to server.');
    }
}

async function logout() {
    try { await fetch(`${API}/api/logout`, { method: 'POST' }); } catch {}
    sessionStorage.clear();
    window.location.href = '/';
}

// ──────────────────────────────────────────────
// PAGE INIT
// ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const username = sessionStorage.getItem('username');
    const role     = sessionStorage.getItem('role');

    const sidebarUser = document.getElementById('sidebarUser');
    if (sidebarUser && username) {
        sidebarUser.textContent = `${username} (${role || 'user'})`;
    }

    const welcomeMsg = document.getElementById('welcomeMsg');
    if (welcomeMsg && username) {
        welcomeMsg.textContent = `Welcome back, ${username}! 👋`;
    }

    // Restore PDF info bar if PDF was previously loaded
    const pdfName = sessionStorage.getItem('pdfName');
    if (pdfName) {
        const bar = document.getElementById('pdfInfoBar');
        const nameEl = document.getElementById('pdfName');
        if (bar && nameEl) {
            nameEl.textContent = pdfName;
            bar.classList.remove('hidden');
        }
    }
});

// ──────────────────────────────────────────────
// PDF UPLOAD
// ──────────────────────────────────────────────

function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer?.files?.[0];
    if (file) uploadFile(file);
}

function handleUpload(event) {
    const file = event.target.files[0];
    if (file) uploadFile(file);
}

async function uploadFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showStatusMsg('❌ Please upload a PDF file.', 'error'); return;
    }

    const statusEl = document.getElementById('uploadStatus');
    showStatus(statusEl, '⏳ Uploading and extracting text…', '');
    statusEl.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res  = await fetch(`${API}/api/upload`, { method: 'POST', body: formData });
        const data = await res.json();

        if (data.status === 'success') {
            showStatus(statusEl, `✅ "${data.filename}" uploaded successfully!`, 'success');

            document.getElementById('pdfInfoBar').classList.remove('hidden');
            document.getElementById('pdfName').textContent    = data.filename;
            document.getElementById('pdfPreview').textContent = data.preview
                ? `"${data.preview.substring(0, 120)}…"` : '';

            sessionStorage.setItem('pdfLoaded', 'true');
            sessionStorage.setItem('pdfName',   data.filename);
        } else {
            showStatus(statusEl, `❌ ${data.message}`, 'error');
        }
    } catch {
        showStatus(statusEl, '❌ Upload failed. Check your connection.', 'error');
    }
}

// ──────────────────────────────────────────────
// NOTES
// ──────────────────────────────────────────────

async function generateNotes() {
    const section   = document.getElementById('notesSection');
    const loadingEl = document.getElementById('notesLoading');
    const contentEl = document.getElementById('notesContent');

    section.classList.remove('hidden');
    loadingEl.classList.remove('hidden');
    contentEl.innerHTML = '';
    section.scrollIntoView({ behavior: 'smooth' });

    try {
        const res  = await fetch(`${API}/api/generate-notes`, { method: 'POST' });
        const data = await res.json();
        loadingEl.classList.add('hidden');

        if (data.status === 'success') {
            contentEl.innerHTML = renderNotes(data.notes);
        } else {
            contentEl.innerHTML = `<p class="text-muted">${data.message}</p>`;
        }
    } catch {
        loadingEl.classList.add('hidden');
        contentEl.innerHTML = '<p class="text-muted">Failed to generate notes. Please try again.</p>';
    }
}

function renderNotes(notes) {
    const keyPoints = (notes.key_points || []).map(p => `<li>${p}</li>`).join('');
    const defs      = (notes.key_definitions || []).map(d => `
        <div class="definition-item">
            <span class="definition-term">${d.term}:</span> ${d.definition}
        </div>`).join('');

    return `
        <div class="notes-section-title">📋 Summary</div>
        <div class="notes-summary">${notes.summary || 'No summary available.'}</div>
        <div class="notes-section-title">✅ Key Points</div>
        <ul class="key-points-list">${keyPoints || '<li>No key points found.</li>'}</ul>
        <div class="notes-section-title">📖 Key Definitions</div>
        ${defs || '<p class="text-muted">No definitions found.</p>'}
    `;
}

// ──────────────────────────────────────────────
// QUIZ
// ──────────────────────────────────────────────

let correctAnswers = [];

function openQuizModal()  { document.getElementById('quizModal').classList.remove('hidden'); }
function closeQuizModal() { document.getElementById('quizModal').classList.add('hidden'); }

async function generateQuiz() {
    closeQuizModal();

    const numQuestions = parseInt(document.getElementById('numQuestions').value);
    const section      = document.getElementById('quizSection');
    const loadingEl    = document.getElementById('quizLoading');
    const contentEl    = document.getElementById('quizContent');
    const submitBtn    = document.getElementById('submitQuizBtn');
    const resultEl     = document.getElementById('quizResult');

    section.classList.remove('hidden');
    loadingEl.classList.remove('hidden');
    contentEl.innerHTML = '';
    submitBtn.style.display = 'none';
    resultEl.classList.add('hidden');
    section.scrollIntoView({ behavior: 'smooth' });

    try {
        const res  = await fetch(`${API}/api/generate-quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ num_questions: numQuestions })
        });
        const data = await res.json();
        loadingEl.classList.add('hidden');

        if (data.status === 'success' && data.quiz?.length) {
            correctAnswers          = data.quiz.map(q => q.answer);
            contentEl.innerHTML     = renderQuiz(data.quiz);
            submitBtn.style.display = 'inline-flex';
        } else {
            contentEl.innerHTML = `<p class="text-muted">${data.message || 'Could not generate quiz.'}</p>`;
        }
    } catch {
        loadingEl.classList.add('hidden');
        contentEl.innerHTML = '<p class="text-muted">Failed to generate quiz. Please try again.</p>';
    }
}

function renderQuiz(quiz) {
    return quiz.map((q, i) => {
        const opts = Object.entries(q.options || {}).map(([key, val]) => `
            <label class="quiz-option">
                <input type="radio" name="q${i}" value="${key}" />
                <span><strong>${key}.</strong> ${val}</span>
            </label>`).join('');
        return `
            <div class="quiz-question-block" data-index="${i}">
                <div class="quiz-question-text">Q${i+1}. ${q.question}</div>
                ${opts}
            </div>`;
    }).join('');
}

async function submitQuiz() {
    const blocks = document.querySelectorAll('.quiz-question-block');
    let score = 0;

    blocks.forEach((block, i) => {
        const selected = block.querySelector(`input[name="q${i}"]:checked`);
        const correct  = correctAnswers[i];

        block.querySelectorAll('.quiz-option').forEach(opt => {
            const val = opt.querySelector('input').value;
            if (val === correct) opt.classList.add('correct');
            else if (selected && val === selected.value) opt.classList.add('wrong');
            opt.querySelector('input').disabled = true;
        });

        if (selected?.value === correct) score++;
    });

    const total  = correctAnswers.length;
    const pct    = Math.round((score / total) * 100);
    const emoji  = pct >= 80 ? '🎉' : pct >= 50 ? '👍' : '📚';
    const resultEl = document.getElementById('quizResult');
    resultEl.textContent = `${emoji} You scored ${score} / ${total} (${pct}%)`;
    resultEl.classList.remove('hidden');
    document.getElementById('submitQuizBtn').style.display = 'none';
    resultEl.scrollIntoView({ behavior: 'smooth' });

    // Persist score to server if logged in
    try {
        await fetch(`${API}/api/save-score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ score, total })
        });
    } catch {}
}

// ──────────────────────────────────────────────
// SCORES / ANALYTICS
// ──────────────────────────────────────────────

async function loadScores() {
    const section   = document.getElementById('scoresSection');
    const contentEl = document.getElementById('scoresContent');

    section.classList.remove('hidden');
    contentEl.innerHTML = '<p class="text-muted">Loading…</p>';
    section.scrollIntoView({ behavior: 'smooth' });

    try {
        const res  = await fetch(`${API}/api/get-scores`);
        const data = await res.json();

        if (data.status === 'success' && data.scores?.length) {
            contentEl.innerHTML = renderScores(data.scores);
        } else if (data.scores?.length === 0) {
            contentEl.innerHTML = '<p class="text-muted">No quiz history yet. Take a quiz first!</p>';
        } else {
            contentEl.innerHTML = `<p class="text-muted">${data.message || 'Could not load scores.'}</p>`;
        }
    } catch {
        contentEl.innerHTML = '<p class="text-muted">Failed to load scores.</p>';
    }
}

function renderScores(scores) {
    const rows = scores.map(s => {
        const pct   = s.percentage;
        const cls   = pct >= 80 ? 'score-good' : pct >= 50 ? 'score-mid' : 'score-low';
        const emoji = pct >= 80 ? '🎉' : pct >= 50 ? '👍' : '📚';
        return `
            <tr>
                <td>${s.pdf_name || '—'}</td>
                <td>${s.score} / ${s.total}</td>
                <td><span class="score-pill ${cls}">${emoji} ${pct}%</span></td>
                <td>${s.taken_at}</td>
            </tr>`;
    }).join('');

    return `
        <table class="scores-table">
            <thead>
                <tr>
                    <th>PDF</th><th>Score</th><th>Result</th><th>Date</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>`;
}

// ──────────────────────────────────────────────
// CHAT
// ──────────────────────────────────────────────

async function sendMessage() {
    const inputEl  = document.getElementById('chatInput');
    const question = inputEl.value.trim();
    if (!question) return;

    inputEl.value = '';
    appendMessage(question, 'user');
    const typingEl = appendTyping();

    try {
        const res  = await fetch(`${API}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await res.json();
        typingEl.remove();
        appendMessage(data.answer || 'Sorry, I could not answer that.', 'bot');
    } catch {
        typingEl.remove();
        appendMessage('Connection error. Please check the server.', 'bot');
    }
}

function appendMessage(text, sender) {
    const chatWindow = document.getElementById('chatWindow');
    const div = document.createElement('div');
    div.className = `chat-message ${sender === 'bot' ? 'bot-message' : 'user-message'}`;
    div.innerHTML  = `<div class="message-bubble">${text}</div>`;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return div;
}

function appendTyping() {
    const chatWindow = document.getElementById('chatWindow');
    const div = document.createElement('div');
    div.className = 'chat-message bot-message';
    div.innerHTML = `<div class="message-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return div;
}

function clearChat() {
    const chatWindow = document.getElementById('chatWindow');
    chatWindow.innerHTML = `
        <div class="chat-message bot-message">
            <div class="message-bubble">
                👋 Chat cleared! Ask me anything about your uploaded PDF.
            </div>
        </div>`;
}

// ──────────────────────────────────────────────
// UTILITIES
// ──────────────────────────────────────────────

function showError(el, msg) {
    if (!el) return;
    el.textContent      = msg;
    el.style.color      = '';
    el.style.background = '';
    el.style.border     = '';
    el.classList.remove('hidden');
}

function hideEl(el) {
    el?.classList.add('hidden');
}

function showStatus(el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className   = `status-msg ${type}`;
}

function showStatusMsg(msg, type) {
    const el = document.getElementById('uploadStatus');
    if (el) { showStatus(el, msg, type); el.classList.remove('hidden'); }
}