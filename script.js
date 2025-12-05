// Configuration
const API_URL = 'http://44.215.127.109:8000';
let currentSessionId = null;

// DOM Elements
const uploadView = document.getElementById('upload-view');
const chatView = document.getElementById('chat-view');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadLoader = document.getElementById('upload-loader');
const uploadText = document.getElementById('upload-text');
const filenameDisplay = document.getElementById('filename-display');
const messagesContainer = document.getElementById('messages-container');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const tableHeader = document.getElementById('table-header');
const tableBody = document.getElementById('table-body');
const dataPreviewPanel = document.getElementById('data-preview-panel');

// Event Listeners
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-blue-500', 'bg-blue-50');
});
dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-blue-500', 'bg-blue-50');
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-blue-500', 'bg-blue-50');
    if (e.dataTransfer.files.length) {
        handleFileUpload(e.dataTransfer.files[0]);
    }
});
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileUpload(e.target.files[0]);
    }
});

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSendMessage();
});
sendBtn.addEventListener('click', handleSendMessage);

window.toggleDataPreview = () => {
    dataPreviewPanel.classList.toggle('hidden');
};

// Functions

async function handleFileUpload(file) {
    if (!file.name.endsWith('.csv')) {
        alert('Please upload a valid CSV file.');
        return;
    }

    // UI Updates
    uploadLoader.classList.remove('hidden');
    uploadText.textContent = `Uploading ${file.name}...`;
    dropZone.classList.add('pointer-events-none', 'opacity-50');

    // Parse locally for preview
    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target.result;
        renderTablePreview(text);
    };
    reader.readAsText(file);

    // Upload to Backend
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();
        currentSessionId = data.session_id;
        filenameDisplay.textContent = file.name;

        // Switch to Chat View
        uploadView.classList.add('hidden');
        chatView.classList.remove('hidden');
        lucide.createIcons(); // Refresh icons for new view
        
    } catch (error) {
        console.error(error);
        alert('Error uploading file to Python backend. Ensure server is running on localhost:8000.');
        resetUploadUI();
    }
}

function resetUploadUI() {
    uploadLoader.classList.add('hidden');
    uploadText.textContent = 'Upload your CSV Data';
    dropZone.classList.remove('pointer-events-none', 'opacity-50');
    fileInput.value = '';
}

async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text || !currentSessionId) return;

    // Add User Message
    addMessage(text, 'user');
    chatInput.value = '';
    
    // Add Loading Indicator
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: text
            })
        });

        const data = await response.json();
        
        // Remove loading and add response
        removeMessage(loadingId);
        addMessage(data.response, 'model');

    } catch (error) {
        removeMessage(loadingId);
        addMessage('Error communicating with backend.', 'model', true);
    }
}

function addMessage(text, role, isError = false) {
    const div = document.createElement('div');
    div.className = `flex w-full ${role === 'user' ? 'justify-end' : 'justify-start'}`;
    
    const contentClass = role === 'user' 
        ? 'bg-blue-600 text-white rounded-br-none' 
        : `bg-slate-100 text-slate-800 rounded-bl-none ${isError ? 'bg-red-50 text-red-600 border border-red-200' : ''}`;

    div.innerHTML = `
        <div class="flex max-w-[85%] md:max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${contentClass}">
            <div class="whitespace-pre-wrap">${formatText(text)}</div>
        </div>
    `;
    
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return div;
}

function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'flex justify-start w-full';
    div.innerHTML = `
        <div class="bg-slate-100 rounded-2xl rounded-bl-none px-4 py-3 flex items-center gap-2">
            <div class="loader" style="width: 14px; height: 14px; border-width: 2px;"></div>
            <span class="text-xs text-slate-500 font-medium">Analyzing...</span>
        </div>
    `;
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function formatText(text) {
    // Simple bold formatter
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function renderTablePreview(csvText) {
    const lines = csvText.split(/\r\n|\n/).filter(line => line.trim() !== '');
    if (lines.length === 0) return;

    // Simple parser
    const headers = lines[0].split(',').map(h => h.replace(/^"|"$/g, '').trim());
    const rows = lines.slice(1, 51).map(line => { // Limit to 50 rows
        // Regex to handle quoted commas matches
        const regex = /(".*?"|[^",\s]+)(?=\s*,|\s*$)/g;
        // Fallback simple split for speed if regex fails or complex
        // For demo: simple split
        return line.split(',').map(c => c.replace(/^"|"$/g, '').trim()); 
    });

    // Render Header
    tableHeader.innerHTML = headers.map(h => `<th class="px-3 py-2 bg-slate-50 border-b border-slate-200">${h}</th>`).join('');

    // Render Body
    tableBody.innerHTML = rows.map(row => `
        <tr class="hover:bg-slate-50">
            ${row.map(cell => `<td class="px-3 py-2 border-b border-slate-100 truncate max-w-[150px]" title="${cell}">${cell}</td>`).join('')}
        </tr>
    `).join('');
}
