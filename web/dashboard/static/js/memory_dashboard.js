/**
 * Neural Memory Dashboard
 * Advanced visualization and monitoring of the AI memory system
 */

// Global variables
let brainGraph = null;
let memoryNodes = [];
let memoryLinks = [];
let memoryDistributionChart = null;
let contextTypeChart = null;
let connectionHeatmapChart = null;
let systemPerformanceChart = null;
let sensorBufferChart = null;
let memoryTypeChart = null;

// Debug flag - enable logging
const DEBUG = true;

// Debug logging function
function debugLog(message, type = 'log') {
    if (DEBUG) {
        console[type]('[Memory Dashboard] ' + message);
    }
}

// Format bytes to human readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Format timestamp to readable date
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
}

// Fetch memory data from server
async function fetchMemoryData() {
    try {
        const response = await fetch('/api/memory/metrics');
        const data = await response.json();
        updateDashboard(data);
    } catch (error) {
        debugLog('Error fetching memory data: ' + error, 'error');
    }
}

// Update memory activity timeline
function updateMemoryActivity(activities) {
    const timeline = document.getElementById('memory-activity');
    if (!timeline) return;
    
    // Clear existing items
    timeline.innerHTML = '';
    
    if (!activities || activities.length === 0) {
        timeline.innerHTML = `
            <div class="memory-item">
                <div class="memory-item-header">
                    <h6 class="memory-item-title">No recent activity</h6>
                    <span class="memory-item-time">${formatTimestamp(Date.now() / 1000)}</span>
                </div>
                <div class="memory-item-content">
                    The memory system is currently idle.
                </div>
            </div>
        `;
        return;
    }
    
    // Add activity items
    activities.forEach(activity => {
        const item = document.createElement('div');
        item.className = 'memory-item';
        item.innerHTML = `
            <div class="memory-item-header">
                <h6 class="memory-item-title">${activity.type}</h6>
                <span class="memory-item-time">${formatTimestamp(activity.timestamp)}</span>
            </div>
            <div class="memory-item-content">
                ${activity.description}
            </div>
        `;
        timeline.appendChild(item);
    });
}

// Update memory tables
function updateMemoryTables(data) {
    // Update short-term memory table
    const shortTermTable = document.getElementById('short-term-memory-table');
    if (shortTermTable) {
        const tbody = shortTermTable.querySelector('tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td>${data.counts.short_term}</td>
                    <td>${formatBytes(data.memory_size.short_term)}</td>
                    <td>${data.performance.avg_retrieval_time}ms</td>
                </tr>
            `;
        }
    }
    
    // Update long-term memory table
    const longTermTable = document.getElementById('long-term-memory-table');
    if (longTermTable) {
        const tbody = longTermTable.querySelector('tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td>${data.counts.long_term}</td>
                    <td>${formatBytes(data.memory_size.long_term)}</td>
                    <td>${data.performance.retrieval_accuracy}%</td>
                </tr>
            `;
        }
    }
    
    // Update context memory table
    const contextTable = document.getElementById('context-memory-table');
    if (contextTable) {
        const tbody = contextTable.querySelector('tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td>${data.counts.context}</td>
                    <td>${formatBytes(data.memory_size.context)}</td>
                    <td>${data.performance.context_relevance}%</td>
                </tr>
            `;
        }
    }
}

// Update brain visualization data
function updateBrainVisualizationData(data) {
    if (!brainGraph) return;
    
    // Update nodes based on memory counts
    memoryNodes = [
        { id: 'short_term', group: 1, value: data.counts.short_term },
        { id: 'context', group: 2, value: data.counts.context },
        { id: 'long_term', group: 3, value: data.counts.long_term },
        { id: 'conscious', group: 4, value: data.counts.conscious }
    ];
    
    // Update links based on memory relationships
    memoryLinks = [
        { source: 'short_term', target: 'context', value: data.health.memory_coherence },
        { source: 'context', target: 'long_term', value: data.performance.retrieval_accuracy },
        { source: 'conscious', target: 'short_term', value: data.performance.insight_quality }
    ];
    
    // Update the graph
    brainGraph.data({ nodes: memoryNodes, links: memoryLinks });
    brainGraph.refresh();
}

// Update dashboard with new data
function updateDashboard(data) {
    debugLog('Updating dashboard with data:', data);
    
    // Update memory utilization
    const memUtil = data.health.memory_utilization;
    document.getElementById('memory-utilization').textContent = memUtil + '%';
    document.getElementById('memory-utilization-bar').style.width = memUtil + '%';
    
    // Update processing load
    const procLoad = data.health.processing_load;
    document.getElementById('processing-load').textContent = procLoad + '%';
    document.getElementById('processing-load-bar').style.width = procLoad + '%';
    
    // Update memory coherence
    const memCoher = data.health.memory_coherence;
    document.getElementById('memory-coherence').textContent = memCoher + '%';
    document.getElementById('memory-coherence-bar').style.width = memCoher + '%';
    
    // Update memory usage in sidebar
    document.getElementById('memory-usage-percent').textContent = memUtil + '%';
    document.getElementById('memory-usage-bar').style.width = memUtil + '%';
    
    // Update memory health badge
    const healthBadge = document.getElementById('memory-health-badge');
    if (memUtil < 60) {
        healthBadge.className = 'badge bg-success';
        healthBadge.textContent = 'Healthy';
    } else if (memUtil < 80) {
        healthBadge.className = 'badge bg-warning';
        healthBadge.textContent = 'Moderate';
    } else {
        healthBadge.className = 'badge bg-danger';
        healthBadge.textContent = 'Critical';
    }
    
    // Update memory activity timeline
    updateMemoryActivity(data.recent_activity);
    
    // Update memory tables
    updateMemoryTables(data);
    
    // Update brain visualization
    updateBrainVisualizationData(data);
    
    // Update short-term memory stats
    document.getElementById('short-term-items').textContent = data.counts.short_term;
    document.getElementById('short-term-size').textContent = formatBytes(data.memory_size.short_term);
    
    // Update long-term memory stats
    document.getElementById('long-term-items').textContent = data.counts.long_term;
    document.getElementById('long-term-size').textContent = formatBytes(data.memory_size.long_term);
    document.getElementById('avg-retrieval-time').textContent = data.performance.avg_retrieval_time + 'ms';
    document.getElementById('retrieval-accuracy').textContent = data.performance.retrieval_accuracy + '%';
    
    // Update context memory stats
    document.getElementById('context-items').textContent = data.counts.context;
    document.getElementById('context-size').textContent = formatBytes(data.memory_size.context);
    document.getElementById('context-relevance').textContent = data.performance.context_relevance + '%';
    
    // Update conscious memory stats
    document.getElementById('sensor-buffer-size').textContent = data.counts.sensor_buffer;
    document.getElementById('insights-generated').textContent = data.counts.insights_generated;
    document.getElementById('processing-cycles').textContent = data.counts.processing_cycles;
    document.getElementById('insight-quality').textContent = data.performance.insight_quality + '%';
    
    // Update analytics metrics
    document.getElementById('metric-memory-utilization').textContent = memUtil + '%';
    document.getElementById('metric-retrieval-speed').textContent = data.performance.avg_retrieval_time + 'ms';
    document.getElementById('metric-memory-coherence').textContent = memCoher + '%';
    document.getElementById('metric-system-reliability').textContent = data.health.system_reliability + '%';
    document.getElementById('metric-memory-fragmentation').textContent = data.health.memory_fragmentation + '%';
}

// Initialize dashboard
function initializeDashboard() {
    debugLog('Initializing dashboard');
    
    // Fetch initial data
    fetchMemoryData();
    
    // Set up periodic updates
    setInterval(fetchMemoryData, 5000);  // Update every 5 seconds
    
    // Initialize charts
    initializeCharts();
}

// Initialize charts
function initializeCharts() {
    // Memory distribution chart
    const distCtx = document.getElementById('memory-distribution-chart');
    if (distCtx) {
        memoryDistributionChart = new Chart(distCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Short-Term', 'Context', 'Long-Term', 'Conscious'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
    
    // System performance chart
    const perfCtx = document.getElementById('system-performance-chart');
    if (perfCtx) {
        systemPerformanceChart = new Chart(perfCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Memory Utilization',
                    data: [],
                    borderColor: '#4e73df',
                    fill: false
                }, {
                    label: 'Processing Load',
                    data: [],
                    borderColor: '#1cc88a',
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

// Generate memory report
async function generateMemoryReport() {
    try {
        const response = await fetch('/api/memory/report', {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            alert('Memory report generated successfully!');
        } else {
            alert('Error generating memory report: ' + result.message);
        }
    } catch (error) {
        debugLog('Error generating memory report: ' + error, 'error');
        alert('Error generating memory report. Please try again.');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeDashboard);