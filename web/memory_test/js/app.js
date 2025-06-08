/**
 * Memory Testing Interface
 * Main application script
 * 
 * This script initializes the memory testing interface, handles
 * user interactions, and manages WebSocket communication with
 * the memory system server.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize WebSocket connection
    wsClient.init();
    
    // Add event listeners
    setupEventListeners();
    
    // Log initialization
    addLogEntry('system', 'Memory testing interface initialized');
});

/**
 * Set up all event listeners for the interface
 */
function setupEventListeners() {
    // WebSocket connection status
    wsClient.onConnectionChange(handleConnectionChange);
    
    // WebSocket message handlers
    wsClient.onMessage('pong', handlePongMessage);
    wsClient.onMessage('memory_added', handleMemoryAddedMessage);
    wsClient.onMessage('search_results', handleSearchResultsMessage);
    wsClient.onMessage('system_stats', handleSystemStatsMessage);
    wsClient.onMessage('error', handleErrorMessage);
    
    // Form submissions
    document.getElementById('add-memory-btn').addEventListener('click', handleAddMemory);
    document.getElementById('search-memory-btn').addEventListener('click', handleSearchMemory);
    
    // Search query Enter key
    document.getElementById('search-query').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            document.getElementById('search-memory-btn').click();
        }
    });
    
    // Quick Tests
    document.getElementById('test-quick-queries-btn').addEventListener('click', function() {
        const modal = new bootstrap.Modal(document.getElementById('quick-test-modal'));
        modal.show();
    });
    
    document.getElementById('run-quick-tests').addEventListener('click', handleRunQuickTests);
    
    // Settings
    document.getElementById('save-settings').addEventListener('click', handleSaveSettings);
    
    // Visualization tabs
    document.querySelectorAll('.viz-tab').forEach(tab => {
        tab.addEventListener('click', handleVizTabClick);
    });
    
    // UI Control buttons
    document.getElementById('clear-results').addEventListener('click', handleClearResults);
    document.getElementById('refresh-stats').addEventListener('click', handleRefreshStats);
    document.getElementById('clear-log').addEventListener('click', handleClearLog);
    document.getElementById('export-results').addEventListener('click', handleExportResults);
    
    // Custom log event
    document.addEventListener('memory-log', function(event) {
        const { timestamp, level, message } = event.detail;
        addLogEntry(level, message, timestamp);
    });
}

/**
 * Handle WebSocket connection status changes
 */
function handleConnectionChange(isConnected) {
    const statusEl = document.getElementById('connection-status');
    
    if (isConnected) {
        statusEl.className = 'badge bg-success';
        statusEl.innerHTML = '<i class="fas fa-plug"></i> Connected';
        
        // Get memory system status
        wsClient.sendMessage({ type: 'ping' });
        
        // Get system stats
        wsClient.sendMessage({ type: 'get_system_stats' });
    } else {
        statusEl.className = 'badge bg-secondary';
        statusEl.innerHTML = '<i class="fas fa-plug"></i> Disconnected';
        
        // Update memory system status
        const memoryStatusEl = document.getElementById('memory-status');
        memoryStatusEl.className = 'badge bg-secondary';
        memoryStatusEl.innerHTML = '<i class="fas fa-database"></i> Unknown';
    }
}

/**
 * Handle pong messages (server health check)
 */
function handlePongMessage(data) {
    const memoryStatusEl = document.getElementById('memory-status');
    
    if (data.memory_system_available) {
        memoryStatusEl.className = 'badge bg-success';
        memoryStatusEl.innerHTML = '<i class="fas fa-database"></i> Available';
    } else {
        memoryStatusEl.className = 'badge bg-danger';
        memoryStatusEl.innerHTML = '<i class="fas fa-database"></i> Unavailable';
    }
}

/**
 * Handle memory added response
 */
function handleMemoryAddedMessage(data) {
    if (data.success) {
        addLogEntry('success', `Memory added successfully in ${data.memory_processing.processing_time_ms}ms`);
        
        // Show memory processing details
        const memoryId = data.memory_id;
        const processingInfo = `
            <div class="memory-processing-info">
                <h5>Memory Processing Details</h5>
                <div class="mb-3">
                    <div class="row mb-2">
                        <div class="col-4"><strong>Memory ID:</strong></div>
                        <div class="col-8">${memoryId}</div>
                    </div>
                    <div class="row mb-2">
                        <div class="col-4"><strong>Source:</strong></div>
                        <div class="col-8">${data.memory_processing.source}</div>
                    </div>
                    <div class="row mb-2">
                        <div class="col-4"><strong>Tags:</strong></div>
                        <div class="col-8">${data.memory_processing.tags.join(', ') || 'None'}</div>
                    </div>
                    <div class="row mb-2">
                        <div class="col-4"><strong>Processing Time:</strong></div>
                        <div class="col-8">${data.memory_processing.processing_time_ms}ms</div>
                    </div>
                </div>
                <h6>Original Content</h6>
                <pre class="memory-content">${data.memory_processing.original_content}</pre>
            </div>
        `;
        
        showDetailModal('Memory Added Successfully', processingInfo);
        
        // Refresh system stats
        wsClient.sendMessage({ type: 'get_system_stats' });
    } else {
        addLogEntry('error', `Failed to add memory: ${data.error || 'Unknown error'}`);
    }
}

/**
 * Handle search results
 */
function handleSearchResultsMessage(data) {
    const resultsContainer = document.getElementById('search-results');
    const searchInfo = document.getElementById('search-info');
    const searchStats = document.getElementById('search-stats');
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    // Update search info
    searchInfo.classList.remove('d-none');
    searchStats.innerHTML = `
        <div><strong>Query:</strong> "${data.query}"</div>
        <div><strong>Results:</strong> ${data.result_count} items found in ${data.search_process.total_search_time_ms}ms</div>
    `;
    
    // Format results
    const formattedResults = MemoryUtils.formatSearchResults(data.results);
    
    if (formattedResults.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">No results found</div>';
    } else {
        // Create result elements
        formattedResults.forEach((result, index) => {
            const resultEl = document.createElement('div');
            resultEl.className = 'result-item';
            resultEl.innerHTML = `
                <div class="result-header">
                    <span class="result-score" style="background-color: ${result.color}">${result.formattedScore}</span>
                    <span class="result-source">${result.source}</span>
                    <span class="result-date">${result.formattedDate}</span>
                </div>
                <div class="result-content">${result.truncatedContent}</div>
                <div class="result-tags">
                    ${result.tags.map(tag => `<span class="result-tag">${tag}</span>`).join('')}
                </div>
            `;
            
            // Add click handler to show details
            resultEl.addEventListener('click', function() {
                showResultDetail(result, index, data.query);
            });
            
            resultsContainer.appendChild(resultEl);
        });
    }
    
    // Update visualizations
    updateVisualizations(data, formattedResults);
    
    addLogEntry('success', `Search completed: ${data.result_count} results for "${data.query}"`);
    
    // Refresh system stats
    wsClient.sendMessage({ type: 'get_system_stats' });
}

/**
 * Handle system stats message
 */
function handleSystemStatsMessage(data) {
    if (!data.memory_system_available) {
        addLogEntry('warning', 'Memory system is not available');
        return;
    }
    
    // Update stats display
    document.getElementById('total-memories').textContent = data.stats.total_memories;
    document.getElementById('short-term-count').textContent = data.stats.short_term_count;
    document.getElementById('long-term-count').textContent = data.stats.long_term_count;
    document.getElementById('avg-search-time').textContent = data.stats.search_stats.avg_search_time_ms + 'ms';
    document.getElementById('successful-searches').textContent = data.stats.search_stats.successful_searches;
    
    // Update search history
    updateSearchHistory(data.search_history);
}

/**
 * Handle error messages
 */
function handleErrorMessage(data) {
    addLogEntry('error', data.error || 'Unknown error');
}

/**
 * Handle add memory form submission
 */
function handleAddMemory() {
    const form = document.getElementById('memory-form');
    
    try {
        const memoryData = MemoryUtils.createMemoryFromForm(form);
        
        wsClient.sendMessage({
            type: 'add_memory',
            ...memoryData
        });
        
        addLogEntry('system', 'Sending memory: ' + memoryData.content.substring(0, 30) + '...');
    } catch (error) {
        addLogEntry('error', error.message);
    }
}

/**
 * Handle search memory form submission
 */
function handleSearchMemory() {
    const form = document.getElementById('search-form');
    
    try {
        const searchParams = MemoryUtils.createSearchQueryFromForm(form);
        
        wsClient.sendMessage({
            type: 'search_memory',
            ...searchParams
        });
        
        addLogEntry('system', 'Searching for: ' + searchParams.query);
    } catch (error) {
        addLogEntry('error', error.message);
    }
}

/**
 * Handle run quick tests button
 */
function handleRunQuickTests() {
    const queries = [];
    
    // Gather selected predefined queries
    if (document.getElementById('query-os').checked) {
        queries.push('What operating system is running on this computer?');
    }
    if (document.getElementById('query-apps').checked) {
        queries.push('What applications are currently running?');
    }
    if (document.getElementById('query-browser').checked) {
        queries.push('What browser am I using?');
    }
    if (document.getElementById('query-dev').checked) {
        queries.push('What development environment am I using?');
    }
    if (document.getElementById('query-music').checked) {
        queries.push('Am I listening to any music?');
    }
    if (document.getElementById('query-recent').checked) {
        queries.push('What was I working on recently?');
    }
    if (document.getElementById('query-productivity').checked) {
        queries.push('What\'s my current productivity level?');
    }
    if (document.getElementById('query-languages').checked) {
        queries.push('What programming languages do I use?');
    }
    
    // Add custom queries
    const customQuery1 = document.getElementById('custom-query-1').value.trim();
    const customQuery2 = document.getElementById('custom-query-2').value.trim();
    const customQuery3 = document.getElementById('custom-query-3').value.trim();
    
    if (customQuery1) queries.push(customQuery1);
    if (customQuery2) queries.push(customQuery2);
    if (customQuery3) queries.push(customQuery3);
    
    if (queries.length === 0) {
        addLogEntry('warning', 'No queries selected for quick tests');
        return;
    }
    
    // Run the first query immediately
    const firstQuery = queries.shift();
    document.getElementById('search-query').value = firstQuery;
    
    wsClient.sendMessage({
        type: 'search_memory',
        query: firstQuery,
        top_k: parseInt(document.getElementById('search-top-k').value, 10),
        min_similarity: parseFloat(document.getElementById('search-min-similarity').value),
        source_filter: document.getElementById('source-filter').value,
        application_context: document.getElementById('app-context').value.trim()
    });
    
    addLogEntry('system', `Running quick test: "${firstQuery}" (1/${queries.length + 1})`);
    
    // Schedule the rest with delays
    if (queries.length > 0) {
        let index = 0;
        const runNextQuery = function() {
            if (index < queries.length) {
                const query = queries[index];
                document.getElementById('search-query').value = query;
                
                wsClient.sendMessage({
                    type: 'search_memory',
                    query: query,
                    top_k: parseInt(document.getElementById('search-top-k').value, 10),
                    min_similarity: parseFloat(document.getElementById('search-min-similarity').value),
                    source_filter: document.getElementById('source-filter').value,
                    application_context: document.getElementById('app-context').value.trim()
                });
                
                addLogEntry('system', `Running quick test: "${query}" (${index + 2}/${queries.length + 1})`);
                
                index++;
                setTimeout(runNextQuery, 2000);  // Run next query after 2 second delay
            }
        };
        
        // Start running queries after a delay
        setTimeout(runNextQuery, 2000);
    }
}

/**
 * Handle save settings button
 */
function handleSaveSettings() {
    const wsUrl = document.getElementById('ws-url').value;
    const apiUrl = document.getElementById('api-url').value;
    
    wsClient.updateSettings(wsUrl, apiUrl);
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('settings-modal'));
    modal.hide();
}

/**
 * Handle visualization tab click
 */
function handleVizTabClick() {
    // Remove active class from all tabs
    document.querySelectorAll('.viz-tab').forEach(t => {
        t.classList.remove('active');
    });
    
    // Add active class to clicked tab
    this.classList.add('active');
    
    // Hide all panels
    document.querySelectorAll('.viz-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Show selected panel
    const target = this.dataset.target;
    document.getElementById(target).classList.add('active');
}

/**
 * Handle clear results button
 */
function handleClearResults() {
    document.getElementById('search-results').innerHTML = `
        <div class="placeholder-message">
            <i class="fas fa-search fa-3x mb-3"></i>
            <p>Search results will appear here</p>
        </div>
    `;
    document.getElementById('search-info').classList.add('d-none');
    
    // Reset visualizations
    resetVisualizations();
}

/**
 * Handle refresh stats button
 */
function handleRefreshStats() {
    wsClient.sendMessage({
        type: 'get_system_stats'
    });
    addLogEntry('system', 'Refreshing system stats...');
}

/**
 * Handle clear log button
 */
function handleClearLog() {
    const logContainer = document.getElementById('activity-log');
    logContainer.innerHTML = `
        <div class="log-entry system">
            <span class="timestamp">${new Date().toLocaleTimeString()}</span>
            <span class="message">Log cleared</span>
        </div>
    `;
}

/**
 * Handle export results button
 */
function handleExportResults() {
    // Get current results
    const searchInfo = document.getElementById('search-info');
    
    if (searchInfo.classList.contains('d-none')) {
        addLogEntry('warning', 'No results to export');
        return;
    }
    
    // Create export data
    const exportData = {
        query: document.getElementById('search-query').value,
        timestamp: new Date().toISOString(),
        results: lastResults || [],
        search_process: lastSearchProcess || {}
    };
    
    // Create download link
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportData, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `memory-search-${Date.now()}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    
    addLogEntry('success', 'Search results exported to JSON');
}

/**
 * Add entry to activity log
 */
function addLogEntry(level, message, timestamp = null) {
    const logContainer = document.getElementById('activity-log');
    const entry = document.createElement('div');
    entry.className = `log-entry ${level}`;
    
    const time = timestamp || new Date().toLocaleTimeString();
    
    entry.innerHTML = `
        <span class="timestamp">${time}</span>
        <span class="message">${message}</span>
    `;
    
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

/**
 * Show result detail modal
 */
function showResultDetail(result, index, query) {
    const detailContainer = document.getElementById('memory-detail-content');
    
    // Create content
    let content = `
        <div class="result-detail">
            <div class="row mb-3">
                <div class="col-md-6">
                    <h5>Memory Content</h5>
                    <pre class="memory-content">${result.content}</pre>
                </div>
                <div class="col-md-6">
                    <h5>Details</h5>
                    <div class="detail-item">
                        <div class="detail-label">Similarity Score:</div>
                        <div class="detail-value">
                            <span class="badge" style="background-color: ${result.color}">${result.formattedScore}</span>
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Source:</div>
                        <div class="detail-value">${result.source}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Created:</div>
                        <div class="detail-value">${result.formattedDate}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Tags:</div>
                        <div class="detail-value">
                            ${result.tags.length > 0 
                                ? result.tags.map(tag => `<span class="result-tag">${tag}</span>`).join('') 
                                : '<em>None</em>'}
                        </div>
                    </div>
                    
                    ${result.relevanceFactors.length > 0 ? `
                        <h6 class="mt-3">Relevance Factors</h6>
                        <ul class="relevance-factors">
                            ${result.relevanceFactors.map(factor => 
                                `<li>${MemoryUtils.formatFactorName(factor)}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
            
            ${!MemoryUtils.isEmptyObject(result.metadata) ? `
                <div class="row mb-3">
                    <div class="col-12">
                        <h5>Metadata</h5>
                        <pre class="metadata-json">${JSON.stringify(result.metadata, null, 2)}</pre>
                    </div>
                </div>
            ` : ''}
            
            <div class="row">
                <div class="col-12">
                    <h5>Memory-Query Relationship</h5>
                    <p>The memory "${result.truncatedContent}" was found for query "${query}" with ${result.formattedScore} similarity.</p>
                    
                    <div class="query-memory-match">
                        <div class="query-box">
                            <h6>Query</h6>
                            <div class="query-content">${query}</div>
                        </div>
                        <div class="match-arrow">
                            <i class="fas fa-arrow-right"></i>
                            <div class="match-score">${result.formattedScore}</div>
                        </div>
                        <div class="memory-box">
                            <h6>Memory</h6>
                            <div class="memory-snippet">${result.truncatedContent}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    detailContainer.innerHTML = content;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('result-detail-modal'));
    modal.show();
}

/**
 * Show detail modal with custom content
 */
function showDetailModal(title, content) {
    // Set title
    document.querySelector('#result-detail-modal .modal-title').innerHTML = 
        `<i class="fas fa-info-circle"></i> ${title}`;
    
    // Set content
    document.getElementById('memory-detail-content').innerHTML = content;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('result-detail-modal'));
    modal.show();
}

/**
 * Show search process modal
 */
function showSearchProcessModal(processData) {
    const detailContainer = document.getElementById('search-process-detail');
    
    // Create content
    let content = `
        <div class="search-process-detail">
            <h5>Search Process Overview</h5>
            <div class="process-overview">
                <div class="process-step embedding">
                    <div class="step-time">${processData.embedding_time_ms}ms</div>
                    <div class="step-name">Query Embedding</div>
                    <div class="step-desc">Converting query to vector representation</div>
                </div>
                <div class="process-arrow"><i class="fas fa-arrow-right"></i></div>
                <div class="process-step retrieval">
                    <div class="step-time">${processData.retrieval_time_ms}ms</div>
                    <div class="step-name">Vector Search</div>
                    <div class="step-desc">Finding similar memories in vector space</div>
                </div>
                <div class="process-arrow"><i class="fas fa-arrow-right"></i></div>
                <div class="process-step ranking">
                    <div class="step-time">${processData.ranking_time_ms}ms</div>
                    <div class="step-name">Result Ranking</div>
                    <div class="step-desc">Sorting and filtering results</div>
                </div>
            </div>
            
            <h5 class="mt-4">Search Details</h5>
            <div class="row">
                <div class="col-md-6">
                    <h6>Query Processing</h6>
                    <div class="detail-item">
                        <div class="detail-label">Original Query:</div>
                        <div class="detail-value">"${processData.original_query}"</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Processed Query:</div>
                        <div class="detail-value">"${processData.processed_query}"</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Search Strategy:</div>
                        <div class="detail-value">${processData.search_strategy}</div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Performance Metrics</h6>
                    <div class="detail-item">
                        <div class="detail-label">Total Search Time:</div>
                        <div class="detail-value">${processData.total_search_time_ms}ms</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Embedding Time:</div>
                        <div class="detail-value">${processData.embedding_time_ms}ms</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Retrieval Time:</div>
                        <div class="detail-value">${processData.retrieval_time_ms}ms</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Ranking Time:</div>
                        <div class="detail-value">${processData.ranking_time_ms}ms</div>
                    </div>
                </div>
            </div>
            
            <h5 class="mt-4">Search Parameters</h5>
            <div class="row">
                <div class="col-md-12">
                    <div class="parameters-container">
                        <div class="detail-item">
                            <div class="detail-label">Top K Results:</div>
                            <div class="detail-value">${processData.parameters.top_k}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Min Similarity:</div>
                            <div class="detail-value">${processData.parameters.min_similarity}</div>
                        </div>
                        ${processData.parameters.source_filter ? `
                            <div class="detail-item">
                                <div class="detail-label">Source Filter:</div>
                                <div class="detail-value">${processData.parameters.source_filter}</div>
                            </div>
                        ` : ''}
                        ${processData.parameters.application_context ? `
                            <div class="detail-item">
                                <div class="detail-label">Application Context:</div>
                                <div class="detail-value">${processData.parameters.application_context}</div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    detailContainer.innerHTML = content;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('search-process-modal'));
    modal.show();
}

/**
 * Update search history display
 */
function updateSearchHistory(history) {
    const container = document.getElementById('search-history');
    
    if (!history || history.length === 0) {
        container.innerHTML = `
            <div class="placeholder-message">
                <p>No search history available</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    // Add history items
    history.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <div class="history-query">${item.query}</div>
            <div class="history-meta">
                <span class="history-results">${item.result_count} results</span>
                <span class="history-time">${item.search_time_ms}ms</span>
            </div>
        `;
        
        // Add click handler to run this search again
        historyItem.addEventListener('click', function() {
            document.getElementById('search-query').value = item.query;
            document.getElementById('search-memory-btn').click();
        });
        
        container.appendChild(historyItem);
    });
}

// Variables to store last results for export
let lastResults = null;
let lastSearchProcess = null;

/**
 * Update visualizations
 */
function updateVisualizations(data, formattedResults) {
    // Store for export
    lastResults = formattedResults;
    lastSearchProcess = data.search_process;
    
    // Update similarity chart
    updateSimilarityChart(formattedResults);
    
    // Update relevance factors
    updateRelevanceFactors(formattedResults);
    
    // Update network visualization
    updateNetworkVisualization(data.related_concepts);
    
    // Update search process visualization
    updateSearchProcessVisualization(data.search_process);
}

/**
 * Reset visualizations
 */
function resetVisualizations() {
    // Reset similarity chart
    if (window.similarityChart) {
        window.similarityChart.destroy();
        window.similarityChart = null;
    }
    
    // Reset relevance factors
    document.getElementById('relevance-factors').innerHTML = `
        <div class="placeholder-message">
            <p>No data to display</p>
        </div>
    `;
    
    // Reset network visualization
    document.getElementById('memory-network').innerHTML = '';
    
    // Reset search process visualization
    document.getElementById('search-process').innerHTML = `
        <div class="process-step-container">
            <div class="process-timeline"></div>
        </div>
    `;
    
    // Reset stored results
    lastResults = null;
    lastSearchProcess = null;
}

/**
 * Update similarity chart
 */
function updateSimilarityChart(results) {
    const chartContainer = document.getElementById('similarity-viz');
    
    if (results.length === 0) {
        chartContainer.innerHTML = `
            <div class="placeholder-message">
                <p>No data to display</p>
            </div>
        `;
        return;
    }
    
    // Create canvas for chart if not exists
    if (!document.getElementById('similarity-chart')) {
        chartContainer.innerHTML = '<canvas id="similarity-chart"></canvas>';
    }
    
    const ctx = document.getElementById('similarity-chart').getContext('2d');
    
    // Destroy previous chart if it exists
    if (window.similarityChart) {
        window.similarityChart.destroy();
    }
    
    // Prepare data
    const labels = results.map((r, i) => `Result ${i+1}`);
    const scores = results.map(r => r.score);
    const colors = results.map(r => r.color);
    
    // Create chart
    window.similarityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Similarity Score',
                data: scores,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    title: {
                        display: true,
                        text: 'Similarity Score'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const result = results[context.dataIndex];
                            return `Score: ${result.formattedScore}`;
                        },
                        afterLabel: function(context) {
                            const result = results[context.dataIndex];
                            return `"${result.truncatedContent}"`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Update relevance factors visualization
 */
function updateRelevanceFactors(results) {
    const container = document.getElementById('relevance-factors');
    
    if (results.length === 0) {
        container.innerHTML = `
            <div class="placeholder-message">
                <p>No data to display</p>
            </div>
        `;
        return;
    }
    
    // Extract relevance factors
    const groupedFactors = MemoryUtils.extractRelevanceFactors(results);
    
    if (Object.keys(groupedFactors).length === 0) {
        container.innerHTML = `
            <div class="placeholder-message">
                <p>No relevance factors available</p>
            </div>
        `;
        return;
    }
    
    // Build visualization
    container.innerHTML = '';
    
    for (const [group, factors] of Object.entries(groupedFactors)) {
        const groupEl = document.createElement('div');
        groupEl.className = 'relevance-group';
        
        groupEl.innerHTML = `
            <h6>${group}</h6>
            <div class="factors-container"></div>
        `;
        
        const factorsContainer = groupEl.querySelector('.factors-container');
        
        factors.forEach(factor => {
            const factorEl = document.createElement('div');
            factorEl.className = 'factor-item';
            
            const percentage = Math.round(factor.percentage * 100);
            
            factorEl.innerHTML = `
                <div class="factor-name">${factor.name}</div>
                <div class="factor-bar-container">
                    <div class="factor-bar" style="width: ${percentage}%"></div>
                    <span class="factor-percentage">${percentage}%</span>
                </div>
            `;
            
            factorsContainer.appendChild(factorEl);
        });
        
        container.appendChild(groupEl);
    }
}

/**
 * Update network visualization
 */
function updateNetworkVisualization(concepts) {
    const container = document.getElementById('memory-network');
    
    if (!concepts || concepts.length === 0) {
        container.innerHTML = `
            <div class="placeholder-message">
                <p>No network data available</p>
            </div>
        `;
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Set up SVG
    const width = container.clientWidth;
    const height = 300;
    
    const svg = d3.select('#memory-network')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Create nodes and links
    const nodes = concepts.map(c => ({ 
        id: c.name,
        type: c.type,
        weight: c.weight
    }));
    
    const links = [];
    concepts.forEach(concept => {
        if (concept.connections) {
            concept.connections.forEach(target => {
                links.push({
                    source: concept.name,
                    target: target
                });
            });
        }
    });
    
    // Create a force simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2));
    
    // Draw links
    const link = svg.append('g')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 1.5);
    
    // Draw nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(nodes)
        .enter()
        .append('circle')
        .attr('r', d => 5 + (d.weight * 15))
        .attr('fill', d => d.type === 'query' ? '#ff6b6b' : '#4ecdc4')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add node labels
    const text = svg.append('g')
        .selectAll('text')
        .data(nodes)
        .enter()
        .append('text')
        .text(d => d.id)
        .attr('font-size', 12)
        .attr('dx', 12)
        .attr('dy', 4);
    
    // Update positions on each tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        text
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

/**
 * Update search process visualization
 */
function updateSearchProcessVisualization(process) {
    const container = document.getElementById('search-process');
    
    if (!process) {
        container.innerHTML = `
            <div class="placeholder-message">
                <p>No search process data available</p>
            </div>
        `;
        return;
    }
    
    // Calculate percentages for visualization
    const totalTime = process.total_search_time_ms;
    const embedPct = (process.embedding_time_ms / totalTime * 100).toFixed(1);
    const retrievalPct = (process.retrieval_time_ms / totalTime * 100).toFixed(1);
    const rankingPct = (process.ranking_time_ms / totalTime * 100).toFixed(1);
    
    // Create content
    container.innerHTML = `
        <div class="process-timeline-container">
            <div class="process-timeline">
                <div class="process-step embedding" style="width: ${embedPct}%">
                    <div class="step-label">Query Embedding</div>
                    <div class="step-time">${process.embedding_time_ms}ms</div>
                </div>
                <div class="process-step retrieval" style="width: ${retrievalPct}%">
                    <div class="step-label">Vector Search</div>
                    <div class="step-time">${process.retrieval_time_ms}ms</div>
                </div>
                <div class="process-step ranking" style="width: ${rankingPct}%">
                    <div class="step-label">Ranking</div>
                    <div class="step-time">${process.ranking_time_ms}ms</div>
                </div>
            </div>
            <div class="total-time">Total: ${totalTime}ms</div>
        </div>
        
        <button id="view-process-details" class="btn btn-sm btn-outline-primary mt-3">
            <i class="fas fa-microscope"></i> View Detailed Search Process
        </button>
    `;
    
    // Add click handler for detailed view
    document.getElementById('view-process-details').addEventListener('click', function() {
        showSearchProcessModal(process);
    });
}