// API endpoints
const API = {
    watchFolder: '/api/watch-folder',
    stopWatching: '/api/stop-watching',
    listDocuments: '/api/documents',
    getDocument: '/api/documents/',
    analyzeDocument: '/api/analyze-document',
    listFolders: '/api/folders',
    getFolderStats: '/api/folders/',
    supportedExtensions: '/api/supported-extensions'
};

// UI Elements
const elements = {
    addFolderBtn: document.getElementById('addFolderBtn'),
    addFolderModal: document.getElementById('addFolderModal'),
    folderPath: document.getElementById('folderPath'),
    confirmAddFolder: document.getElementById('confirmAddFolder'),
    cancelAddFolder: document.getElementById('cancelAddFolder'),
    folderList: document.getElementById('folderList'),
    documentList: document.getElementById('documentList'),
    analysisPanel: document.getElementById('analysisPanel'),
    closeAnalysisBtn: document.getElementById('closeAnalysisBtn'),
    analysisContent: document.getElementById('analysisContent')
};

// State
let state = {
    watchedFolders: new Set(),
    currentDocument: null,
    supportedExtensions: new Set(),
    folderStats: {}
};

// Progress tracking
let progressInterval = null;

// Event Listeners
elements.addFolderBtn.addEventListener('click', () => {
    elements.addFolderModal.classList.remove('hidden');
});

elements.cancelAddFolder.addEventListener('click', () => {
    elements.addFolderModal.classList.add('hidden');
});

elements.confirmAddFolder.addEventListener('click', async () => {
    const folderPath = elements.folderPath.value.trim();
    if (folderPath) {
        await watchFolder(folderPath);
        elements.addFolderModal.classList.add('hidden');
        elements.folderPath.value = '';
    }
});

elements.closeAnalysisBtn.addEventListener('click', () => {
    elements.analysisPanel.classList.add('hidden');
    state.currentDocument = null;
});

// API Functions
async function loadSupportedExtensions() {
    try {
        const response = await fetch(API.supportedExtensions);
        if (response.ok) {
            const extensions = await response.json();
            state.supportedExtensions = new Set(extensions);
        }
    } catch (error) {
        console.error('Error loading supported extensions:', error);
    }
}

async function watchFolder(path) {
    try {
        const response = await fetch(API.watchFolder, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path })
        });
        
        if (response.ok) {
            const data = await response.json();
            state.watchedFolders.add(path);
            state.folderStats[path] = data.stats;
            updateFolderList();
            await loadDocuments(path);
        } else {
            throw new Error('Failed to watch folder');
        }
    } catch (error) {
        console.error('Error watching folder:', error);
        alert('Failed to watch folder. Please try again.');
    }
}

async function stopWatchingFolder(path) {
    try {
        const response = await fetch(API.stopWatching, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path })
        });
        
        if (response.ok) {
            state.watchedFolders.delete(path);
            delete state.folderStats[path];
            updateFolderList();
            await loadDocuments();
        }
    } catch (error) {
        console.error('Error stopping folder watch:', error);
    }
}

async function loadDocuments(folderPath = null) {
    try {
        const url = folderPath ? `${API.listDocuments}?folder_path=${encodeURIComponent(folderPath)}` : API.listDocuments;
        const response = await fetch(url);
        if (response.ok) {
            const documents = await response.json();
            renderDocuments(documents);
        }
    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

async function loadDocumentAnalysis(docHash) {
    try {
        const response = await fetch(API.getDocument + docHash);
        if (response.ok) {
            const document = await response.json();
            state.currentDocument = document;
            renderAnalysis(document);
        }
    } catch (error) {
        console.error('Error loading document analysis:', error);
    }
}

async function updateFolderStats(folderPath) {
    try {
        const response = await fetch(API.getFolderStats + encodeURIComponent(folderPath));
        if (response.ok) {
            const stats = await response.json();
            state.folderStats[folderPath] = stats;
            updateFolderList();
        }
    } catch (error) {
        console.error('Error updating folder stats:', error);
    }
}

// Render Functions
function updateFolderList() {
    elements.folderList.innerHTML = Array.from(state.watchedFolders)
        .map(folder => {
            const stats = state.folderStats[folder] || {};
            return `
                <div class="folder-item p-2 rounded cursor-pointer">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center">
                            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                            </svg>
                            <span class="truncate">${folder}</span>
                        </div>
                        <button onclick="stopWatchingFolder('${folder}')" class="text-red-500 hover:text-red-700">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    ${stats.scanning ? `
                        <div class="mt-2">
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div class="bg-blue-500 h-2 rounded-full" style="width: ${stats.scan_progress}%"></div>
                            </div>
                            <p class="text-xs text-gray-500 mt-1">Scanning... ${Math.round(stats.scan_progress)}%</p>
                        </div>
                    ` : `
                        <div class="mt-2 text-xs text-gray-500">
                            <p>Files: ${stats.total_files || 0}</p>
                            <p>Size: ${formatFileSize(stats.total_size || 0)}</p>
                            <p>Last scan: ${stats.last_scan ? new Date(stats.last_scan).toLocaleString() : 'Never'}</p>
                        </div>
                    `}
                </div>
            `;
        }).join('');
}

function renderDocuments(documents) {
    elements.documentList.innerHTML = documents.map(doc => `
        <div class="document-card bg-white rounded-lg shadow p-4 cursor-pointer" onclick="loadDocumentAnalysis('${doc.doc_hash}')">
            <div class="flex items-center justify-between">
                <h3 class="font-semibold truncate">${doc.doc_path.split('/').pop()}</h3>
                <span class="text-xs text-gray-500">${doc.analysis.metadata.extension}</span>
            </div>
            <p class="text-sm text-gray-500 mt-1">${doc.analysis.summary}</p>
            <div class="mt-2 flex items-center justify-between text-sm text-gray-400">
                <span>${new Date(doc.timestamp).toLocaleDateString()}</span>
                <span>${formatFileSize(doc.analysis.metadata.size)}</span>
            </div>
        </div>
    `).join('');
}

function renderAnalysis(document) {
    elements.analysisContent.innerHTML = `
        <div class="space-y-4">
            <div>
                <h3 class="font-semibold">Summary</h3>
                <p class="mt-1">${document.analysis.summary}</p>
            </div>
            
            <div>
                <h3 class="font-semibold">Risks</h3>
                <ul class="mt-1 list-disc list-inside">
                    ${document.analysis.risks.map(risk => `<li>${risk}</li>`).join('')}
                </ul>
            </div>
            
            <div>
                <h3 class="font-semibold">Recommendations</h3>
                <ul class="mt-1 list-disc list-inside">
                    ${document.analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
            
            <div>
                <h3 class="font-semibold">Metadata</h3>
                <dl class="mt-1">
                    <dt class="text-sm text-gray-500">File Type</dt>
                    <dd>${document.analysis.metadata.file_type}</dd>
                    <dt class="text-sm text-gray-500 mt-2">Size</dt>
                    <dd>${formatFileSize(document.analysis.metadata.size)}</dd>
                    <dt class="text-sm text-gray-500 mt-2">Last Modified</dt>
                    <dd>${new Date(document.analysis.metadata.last_modified).toLocaleString()}</dd>
                </dl>
            </div>
        </div>
    `;
    
    elements.analysisPanel.classList.remove('hidden');
}

// Utility Functions
function formatFileSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// Initialize
async function initialize() {
    await loadSupportedExtensions();
    await loadDocuments();
    
    // Set up periodic updates for folder stats
    setInterval(() => {
        state.watchedFolders.forEach(folder => {
            updateFolderStats(folder);
        });
    }, 5000);  // Update every 5 seconds
}

function startProgressTracking() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/analysis-progress');
            if (response.ok) {
                const progress = await response.json();
                updateProgressUI(progress);
            }
        } catch (error) {
            console.error('Error fetching analysis progress:', error);
        }
    }, 1000); // Poll every second
}

function stopProgressTracking() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    hideProgressUI();
}

function updateProgressUI(progress) {
    const progressContainer = document.getElementById('analysisProgress');
    const progressBar = document.getElementById('progressBar');
    const progressPercentage = document.getElementById('progressPercentage');
    const currentFile = document.getElementById('currentFile');
    const chunkProgress = document.getElementById('chunkProgress');
    
    if (progress.current_file) {
        progressContainer.classList.remove('hidden');
        progressBar.style.width = `${progress.progress_percentage}%`;
        progressPercentage.textContent = `${Math.round(progress.progress_percentage)}%`;
        currentFile.textContent = `Analyzing: ${progress.current_file.split('/').pop()}`;
        chunkProgress.textContent = `Processing chunk ${progress.current_chunk} of ${progress.total_chunks}`;
    } else {
        hideProgressUI();
    }
}

function hideProgressUI() {
    const progressContainer = document.getElementById('analysisProgress');
    progressContainer.classList.add('hidden');
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressPercentage').textContent = '0%';
    document.getElementById('currentFile').textContent = 'No file being analyzed';
    document.getElementById('chunkProgress').textContent = 'Processing chunk 0 of 0';
}

async function addFolderFiles(filePaths) {
    try {
        startProgressTracking();
        const response = await fetch(API.FOLDERS + '/files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ files: filePaths })
        });
        
        if (response.ok) {
            await loadWatchedFolders();
        }
    } catch (error) {
        console.error('Error adding folder files:', error);
    } finally {
        // Stop progress tracking after 5 minutes if no progress is reported
        setTimeout(() => {
            stopProgressTracking();
        }, 300000);
    }
}

initialize(); 