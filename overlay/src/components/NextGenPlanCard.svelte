<script>
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale, blur, slide } from 'svelte/transition';
  import { cubicOut, elasticOut, expoOut, backOut } from 'svelte/easing';
  
  export let plan = {};
  export let planId = '';
  export let mode = 'Agent';
  export let onExecute = () => {};
  export let onModify = () => {};
  export let onCancel = () => {};
  
  let isExpanded = false;
  let showDetails = false;
  let currentStep = 0;
  let progress = 0;
  let isExecuting = false;
  let executionResults = [];
  let showStepDetails = false;
  let selectedStep = null;
  
  // Animation states
  let cardVisible = false;
  let stepsVisible = false;
  let buttonsVisible = false;
  
  const steps = plan.steps || [];
  const estimatedDuration = plan.estimated_duration || '15.0';
  const successProbability = plan.success_probability || '80';
  const complexity = plan.complexity || 'Medium';
  
  // Color schemes for different modes
  const modeColors = {
    'Agent': {
      primary: '#FF3B30',
      secondary: '#FF9500',
      gradient: 'linear-gradient(135deg, #FF3B30 0%, #FF9500 100%)',
      accent: '#FF6B6B'
    },
    'Ask': {
      primary: '#007AFF',
      secondary: '#5AC8FA',
      gradient: 'linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%)',
      accent: '#4A90E2'
    },
    'Suggest': {
      primary: '#30D158',
      secondary: '#32D74B',
      gradient: 'linear-gradient(135deg, #30D158 0%, #32D74B 100%)',
      accent: '#34C759'
    }
  };
  
  const colors = modeColors[mode] || modeColors['Agent'];
  
  onMount(() => {
    setTimeout(() => {
      cardVisible = true;
    }, 100);
    
    setTimeout(() => {
      stepsVisible = true;
    }, 300);
    
    setTimeout(() => {
      buttonsVisible = true;
    }, 500);
  });
  
  function toggleDetails() {
    showDetails = !showDetails;
  }
  
  function executePlan() {
    isExecuting = true;
    progress = 0;
    currentStep = 0;
    executionResults = [];
    
    // Simulate execution progress
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        isExecuting = false;
        clearInterval(interval);
      }
    }, 500);
    
    onExecute();
  }
  
  function getStepIcon(step) {
    const action = step.action?.toLowerCase() || '';
    if (action.includes('open') || action.includes('launch')) return '🚀';
    if (action.includes('click')) return '🖱️';
    if (action.includes('type') || action.includes('input')) return '⌨️';
    if (action.includes('wait') || action.includes('sleep')) return '⏱️';
    if (action.includes('navigate')) return '🧭';
    if (action.includes('search')) return '🔍';
    return '⚡';
  }
  
  function getStepColor(step, index) {
    if (isExecuting && index <= currentStep) return '#30D158';
    if (isExecuting && index === currentStep) return colors.accent;
    return '#8E8E93';
  }
</script>

<div class="plan-card" class:expanded={isExpanded} class:executing={isExecuting}>
  <!-- Header -->
  <div class="plan-header" style="background: {colors.gradient}">
    <div class="plan-title">
      <div class="plan-icon">🤖</div>
      <div class="plan-info">
        <h3>Automation Plan</h3>
        <p class="plan-id">#{planId}</p>
      </div>
    </div>
    
    <div class="plan-stats">
      <div class="stat">
        <span class="stat-value">{steps.length}</span>
        <span class="stat-label">Steps</span>
      </div>
      <div class="stat">
        <span class="stat-value">{estimatedDuration}s</span>
        <span class="stat-label">Duration</span>
      </div>
      <div class="stat">
        <span class="stat-value">{successProbability}%</span>
        <span class="stat-label">Success</span>
      </div>
    </div>
  </div>
  
  <!-- Progress Bar -->
  {#if isExecuting}
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%; background: {colors.gradient}"></div>
      </div>
      <div class="progress-text">Executing... {Math.round(progress)}%</div>
    </div>
  {/if}
  
  <!-- Steps -->
  <div class="steps-container">
    {#each steps as step, index}
      <div 
        class="step-item" 
        class:active={isExecuting && index === currentStep}
        class:completed={isExecuting && index < currentStep}
        style="--step-color: {getStepColor(step, index)}"
        on:click={() => { selectedStep = step; showStepDetails = true; }}
      >
        <div class="step-number">{index + 1}</div>
        <div class="step-icon">{getStepIcon(step)}</div>
        <div class="step-content">
          <div class="step-title">{step.description || step.action}</div>
          <div class="step-details">
            {#if step.app}
              <span class="step-app">📱 {step.app}</span>
            {/if}
            {#if step.action}
              <span class="step-action">⚡ {step.action}</span>
            {/if}
          </div>
        </div>
        <div class="step-status">
          {#if isExecuting && index < currentStep}
            ✅
          {:else if isExecuting && index === currentStep}
            🔄
          {:else}
            ⏳
          {/if}
        </div>
      </div>
    {/each}
  </div>
  
  <!-- Action Buttons -->
  <div class="action-buttons">
    <button 
      class="execute-btn" 
      class:executing={isExecuting}
      style="background: {colors.gradient}"
      on:click={executePlan}
      disabled={isExecuting}
    >
      {#if isExecuting}
        <span class="btn-icon">🔄</span>
        <span class="btn-text">Executing...</span>
      {:else}
        <span class="btn-icon">🚀</span>
        <span class="btn-text">Execute Plan</span>
      {/if}
    </button>
    
    <div class="secondary-actions">
      <button class="modify-btn" on:click={onModify}>
        <span class="btn-icon">✏️</span>
        <span class="btn-text">Modify</span>
      </button>
      
      <button class="cancel-btn" on:click={onCancel}>
        <span class="btn-icon">✗</span>
        <span class="btn-text">Cancel</span>
      </button>
    </div>
  </div>
</div>

<!-- Step Detail Modal -->
{#if showStepDetails && selectedStep}
  <div class="modal-overlay" on:click={() => showStepDetails = false}>
    <div class="modal-content" on:click|stopPropagation>
      <div class="modal-header">
        <h3>Step Details</h3>
        <button class="close-btn" on:click={() => showStepDetails = false}>✗</button>
      </div>
      
      <div class="step-detail-content">
        <div class="detail-item">
          <span class="detail-label">Action:</span>
          <span class="detail-value">{selectedStep.action}</span>
        </div>
        
        {#if selectedStep.app}
          <div class="detail-item">
            <span class="detail-label">App:</span>
            <span class="detail-value">{selectedStep.app}</span>
          </div>
        {/if}
        
        {#if selectedStep.description}
          <div class="detail-item">
            <span class="detail-label">Description:</span>
            <span class="detail-value">{selectedStep.description}</span>
          </div>
        {/if}
        
        {#if selectedStep.target}
          <div class="detail-item">
            <span class="detail-label">Target:</span>
            <span class="detail-value">{selectedStep.target}</span>
          </div>
        {/if}
        
        {#if selectedStep.value}
          <div class="detail-item">
            <span class="detail-label">Value:</span>
            <span class="detail-value">{selectedStep.value}</span>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .plan-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    overflow: hidden;
    margin: 16px 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .plan-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  }
  
  .plan-card.executing {
    border-color: #30D158;
    box-shadow: 0 8px 32px rgba(48, 209, 88, 0.2);
  }
  
  .plan-header {
    padding: 24px;
    color: white;
    position: relative;
    overflow: hidden;
  }
  
  .plan-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
    pointer-events: none;
  }
  
  .plan-title {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
  }
  
  .plan-icon {
    font-size: 32px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  }
  
  .plan-info h3 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }
  
  .plan-id {
    margin: 4px 0 0 0;
    font-size: 14px;
    opacity: 0.9;
    font-family: 'SF Mono', monospace;
  }
  
  .plan-stats {
    display: flex;
    gap: 24px;
  }
  
  .stat {
    text-align: center;
  }
  
  .stat-value {
    display: block;
    font-size: 20px;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }
  
  .stat-label {
    display: block;
    font-size: 12px;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .progress-container {
    padding: 16px 24px;
    background: rgba(0, 0, 0, 0.05);
  }
  
  .progress-bar {
    height: 6px;
    background: rgba(0, 0, 0, 0.1);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 8px;
  }
  
  .progress-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
  }
  
  .progress-text {
    font-size: 12px;
    color: #666;
    text-align: center;
  }
  
  .steps-container {
    padding: 24px;
  }
  
  .step-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    margin-bottom: 12px;
    background: rgba(0, 0, 0, 0.02);
    border-radius: 12px;
    border: 1px solid rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
    cursor: pointer;
    animation: fadeInUp 0.5s ease forwards;
    animation-delay: calc(var(--index, 0) * 0.1s);
  }
  
  .step-item:hover {
    background: rgba(0, 0, 0, 0.05);
    transform: translateX(4px);
  }
  
  .step-item.active {
    background: rgba(48, 209, 88, 0.1);
    border-color: #30D158;
    box-shadow: 0 0 0 2px rgba(48, 209, 88, 0.2);
  }
  
  .step-item.completed {
    background: rgba(48, 209, 88, 0.05);
    border-color: rgba(48, 209, 88, 0.3);
  }
  
  .step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--step-color);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
  }
  
  .step-icon {
    font-size: 20px;
    width: 32px;
    text-align: center;
  }
  
  .step-content {
    flex: 1;
  }
  
  .step-title {
    font-weight: 600;
    color: #1d1d1f;
    margin-bottom: 4px;
  }
  
  .step-details {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: #666;
  }
  
  .step-app, .step-action {
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 8px;
    border-radius: 4px;
  }
  
  .step-status {
    font-size: 16px;
    opacity: 0.7;
  }
  
  .action-buttons {
    padding: 24px;
    border-top: 1px solid rgba(0, 0, 0, 0.05);
  }
  
  .execute-btn {
    width: 100%;
    padding: 16px 24px;
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 16px;
  }
  
  .execute-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }
  
  .execute-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  .secondary-actions {
    display: flex;
    gap: 12px;
  }
  
  .modify-btn, .cancel-btn {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    background: white;
    color: #1d1d1f;
    font-weight: 500;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
  
  .modify-btn:hover {
    background: #f5f5f7;
    border-color: #007AFF;
  }
  
  .cancel-btn:hover {
    background: #f5f5f7;
    border-color: #FF3B30;
  }
  
  .btn-icon {
    font-size: 16px;
  }
  
  .btn-text {
    font-size: 14px;
  }
  
  /* Modal Styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.3s ease;
  }
  
  .modal-content {
    background: white;
    border-radius: 20px;
    padding: 24px;
    max-width: 400px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    animation: scaleIn 0.3s ease;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .modal-header h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #666;
    padding: 4px;
    border-radius: 4px;
    transition: background 0.2s ease;
  }
  
  .close-btn:hover {
    background: rgba(0, 0, 0, 0.05);
  }
  
  .step-detail-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: rgba(0, 0, 0, 0.02);
    border-radius: 8px;
  }
  
  .detail-label {
    font-weight: 600;
    color: #666;
    font-size: 14px;
  }
  
  .detail-value {
    color: #1d1d1f;
    font-size: 14px;
    text-align: right;
    max-width: 200px;
    word-break: break-word;
  }
  
  /* Animations */
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  
  @keyframes scaleIn {
    from {
      opacity: 0;
      transform: scale(0.9);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }
</style> 