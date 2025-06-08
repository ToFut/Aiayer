<script>
  export let plan = {};
  export let onExecute = () => {};
  export let onCancel = () => {};
  export let onModify = () => {};
  export let onSimulate = () => {};
  
  // Parse the plan content from markdown-like format to structured data
  import { onMount } from 'svelte';
  
  let taskType = '';
  let taskTitle = '';
  let estimatedDuration = '';
  let successProbability = '';
  let complexity = '';
  let stepsCount = '';
  let steps = [];
  let planId = '';
  let planningSystem = '';
  
  // Function to parse plan content
  function parsePlanContent(content) {
    try {
      if (!content) return;
      
      // Extract Task Type
      const taskTypeMatch = content.match(/\*\*🔍 Task Type:\*\* ([^\n]+)/);
      if (taskTypeMatch) taskType = taskTypeMatch[1];
      
      // Extract Task Title
      const taskTitleMatch = content.match(/\*\*📋 Task:\*\* ([^\n]+)/);
      if (taskTitleMatch) taskTitle = taskTitleMatch[1];
      
      // Extract Estimated Duration
      const durationMatch = content.match(/\*\*⏱️ Estimated Duration:\*\* ([^\n]+)/);
      if (durationMatch) estimatedDuration = durationMatch[1];
      
      // Extract Success Probability
      const probabilityMatch = content.match(/\*\*🎯 Success Probability:\*\* ([^\n]+)/);
      if (probabilityMatch) successProbability = probabilityMatch[1];
      
      // Extract Complexity
      const complexityMatch = content.match(/\*\*🔧 Complexity:\*\* ([^\n]+)/);
      if (complexityMatch) complexity = complexityMatch[1];
      
      // Extract Steps Count
      const stepsCountMatch = content.match(/\*\*📝 Steps:\*\* ([^\n]+)/);
      if (stepsCountMatch) stepsCount = stepsCountMatch[1];
      
      // Extract Steps
      const stepsSection = content.match(/\*\*🚀 Automation Steps:\*\*\n([\s\S]*?)(?=\n\n\*\*🆔|$)/);
      if (stepsSection) {
        const stepsText = stepsSection[1];
        steps = stepsText.split('\n')
          .filter(step => step.trim())
          .map(step => {
            const stepMatch = step.match(/\d+\.\s+🟢\s+(.*)/);
            return stepMatch ? stepMatch[1] : step.trim();
          });
      }
      
      // Extract Plan ID
      const planIdMatch = content.match(/\*\*🆔 Plan ID:\*\* `([^`]+)`/);
      if (planIdMatch) planId = planIdMatch[1];
      
      // Extract Planning System
      const planningMatch = content.match(/\*\*🧠 Planning:\*\* ([^\n]+)/);
      if (planningMatch) planningSystem = planningMatch[1];
    } catch (error) {
      console.error('Error parsing plan content:', error);
    }
  }
  
  onMount(() => {
    parsePlanContent(plan.content);
  });
</script>

<div class="automation-plan-card">
  <div class="plan-header">
    <div class="plan-icon">🎯</div>
    <div class="plan-title">
      <h3>AUTOMATION EXECUTION PLAN</h3>
      <div class="plan-id">ID: {planId}</div>
    </div>
  </div>
  
  <div class="plan-details">
    <div class="detail-row">
      <div class="detail-item">
        <div class="detail-icon">🔍</div>
        <div class="detail-content">
          <div class="detail-label">Task Type</div>
          <div class="detail-value">{taskType}</div>
        </div>
      </div>
      <div class="detail-item">
        <div class="detail-icon">📋</div>
        <div class="detail-content">
          <div class="detail-label">Task</div>
          <div class="detail-value">{taskTitle}</div>
        </div>
      </div>
    </div>
    
    <div class="detail-row">
      <div class="detail-item">
        <div class="detail-icon">⏱️</div>
        <div class="detail-content">
          <div class="detail-label">Duration</div>
          <div class="detail-value">{estimatedDuration}</div>
        </div>
      </div>
      <div class="detail-item">
        <div class="detail-icon">🎯</div>
        <div class="detail-content">
          <div class="detail-label">Success Rate</div>
          <div class="detail-value">{successProbability}</div>
        </div>
      </div>
      <div class="detail-item">
        <div class="detail-icon">🔧</div>
        <div class="detail-content">
          <div class="detail-label">Complexity</div>
          <div class="detail-value">{complexity}</div>
        </div>
      </div>
    </div>
  </div>
  
  <div class="plan-steps">
    <div class="steps-header">
      <div class="steps-icon">🚀</div>
      <div class="steps-title">Automation Steps</div>
    </div>
    <div class="steps-list">
      {#each steps as step, i}
        <div class="step-item">
          <div class="step-number">{i + 1}</div>
          <div class="step-content">
            <div class="step-indicator">🟢</div>
            <div class="step-text">{step}</div>
          </div>
        </div>
      {/each}
    </div>
  </div>
  
  <div class="plan-footer">
    <div class="plan-system">
      <div class="system-icon">🧠</div>
      <div class="system-text">{planningSystem}</div>
    </div>
    
    <div class="action-buttons">
      <button class="action-button execute" on:click={onExecute}>
        <div class="button-icon">▶️</div>
        <div class="button-text">EXECUTE</div>
      </button>
      <button class="action-button simulate" on:click={onSimulate}>
        <div class="button-icon">🔍</div>
        <div class="button-text">SIMULATE</div>
      </button>
      <button class="action-button modify" on:click={onModify}>
        <div class="button-icon">✏️</div>
        <div class="button-text">MODIFY</div>
      </button>
      <button class="action-button cancel" on:click={onCancel}>
        <div class="button-icon">❌</div>
        <div class="button-text">CANCEL</div>
      </button>
    </div>
  </div>
</div>

<style>
  .automation-plan-card {
    width: 100%;
    background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(20, 20, 40, 0.9));
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(100, 100, 255, 0.2);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25), 
                0 0 0 1px rgba(255, 255, 255, 0.1),
                0 0 20px rgba(100, 100, 255, 0.2);
    overflow: hidden;
    margin: 1rem 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    color: white;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: card-appear 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  @keyframes card-appear {
    from {
      opacity: 0;
      transform: translateY(20px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
  
  .automation-plan-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3), 
                0 0 0 1px rgba(255, 255, 255, 0.15),
                0 0 30px rgba(100, 100, 255, 0.3);
  }
  
  .plan-header {
    display: flex;
    align-items: center;
    padding: 1.2rem 1.5rem;
    background: linear-gradient(135deg, rgba(80, 80, 220, 0.2), rgba(40, 40, 180, 0.3));
    border-bottom: 1px solid rgba(100, 100, 255, 0.15);
  }
  
  .plan-icon {
    font-size: 2rem;
    margin-right: 1rem;
    animation: pulse 3s infinite;
  }
  
  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.1);
    }
    100% {
      transform: scale(1);
    }
  }
  
  .plan-title {
    flex: 1;
  }
  
  .plan-title h3 {
    margin: 0;
    font-size: 1.3rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    background: linear-gradient(135deg, #ffffff, #aaccff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .plan-id {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 0.3rem;
    font-family: monospace;
  }
  
  .plan-details {
    padding: 1.2rem 1.5rem;
    background: rgba(20, 20, 40, 0.5);
    border-bottom: 1px solid rgba(100, 100, 255, 0.1);
  }
  
  .detail-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .detail-row:last-child {
    margin-bottom: 0;
  }
  
  .detail-item {
    flex: 1;
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    background: rgba(30, 30, 60, 0.5);
    padding: 0.8rem;
    border-radius: 10px;
    border: 1px solid rgba(100, 100, 255, 0.1);
  }
  
  .detail-icon {
    font-size: 1.2rem;
  }
  
  .detail-content {
    flex: 1;
  }
  
  .detail-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.6);
    letter-spacing: 0.5px;
    margin-bottom: 0.3rem;
  }
  
  .detail-value {
    font-size: 0.9rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .plan-steps {
    padding: 1.2rem 1.5rem;
    background: rgba(25, 25, 50, 0.5);
  }
  
  .steps-header {
    display: flex;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .steps-icon {
    font-size: 1.2rem;
    margin-right: 0.8rem;
  }
  
  .steps-title {
    font-size: 1rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .steps-list {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
  }
  
  .step-item {
    display: flex;
    align-items: flex-start;
    padding: 0.8rem;
    background: rgba(40, 40, 80, 0.4);
    border-radius: 10px;
    border: 1px solid rgba(100, 100, 255, 0.1);
    transition: all 0.2s ease-in-out;
  }
  
  .step-item:hover {
    background: rgba(50, 50, 100, 0.5);
    transform: translateX(5px);
  }
  
  .step-number {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(80, 80, 220, 0.2);
    border-radius: 50%;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 0.8rem;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .step-content {
    flex: 1;
    display: flex;
    align-items: center;
  }
  
  .step-indicator {
    margin-right: 0.6rem;
    font-size: 0.9rem;
  }
  
  .step-text {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.9);
    line-height: 1.4;
  }
  
  .plan-footer {
    padding: 1.2rem 1.5rem;
    background: linear-gradient(135deg, rgba(30, 30, 60, 0.6), rgba(20, 20, 40, 0.6));
    border-top: 1px solid rgba(100, 100, 255, 0.1);
  }
  
  .plan-system {
    display: flex;
    align-items: center;
    margin-bottom: 1.2rem;
  }
  
  .system-icon {
    font-size: 1.1rem;
    margin-right: 0.6rem;
    opacity: 0.8;
  }
  
  .system-text {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.7);
    font-style: italic;
  }
  
  .action-buttons {
    display: flex;
    gap: 0.8rem;
    justify-content: space-between;
  }
  
  .action-button {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0.8rem 0.5rem;
    border: none;
    border-radius: 10px;
    background: rgba(50, 50, 100, 0.4);
    color: white;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    font-family: inherit;
    border: 1px solid rgba(100, 100, 255, 0.1);
  }
  
  .action-button:hover {
    transform: translateY(-3px);
  }
  
  .action-button.execute {
    background: linear-gradient(135deg, rgba(40, 180, 100, 0.4), rgba(30, 140, 80, 0.4));
  }
  
  .action-button.execute:hover {
    background: linear-gradient(135deg, rgba(40, 180, 100, 0.6), rgba(30, 140, 80, 0.6));
    box-shadow: 0 5px 15px rgba(40, 180, 100, 0.2);
  }
  
  .action-button.simulate {
    background: linear-gradient(135deg, rgba(80, 120, 220, 0.4), rgba(60, 80, 180, 0.4));
  }
  
  .action-button.simulate:hover {
    background: linear-gradient(135deg, rgba(80, 120, 220, 0.6), rgba(60, 80, 180, 0.6));
    box-shadow: 0 5px 15px rgba(80, 120, 220, 0.2);
  }
  
  .action-button.modify {
    background: linear-gradient(135deg, rgba(220, 180, 40, 0.4), rgba(180, 140, 30, 0.4));
  }
  
  .action-button.modify:hover {
    background: linear-gradient(135deg, rgba(220, 180, 40, 0.6), rgba(180, 140, 30, 0.6));
    box-shadow: 0 5px 15px rgba(220, 180, 40, 0.2);
  }
  
  .action-button.cancel {
    background: linear-gradient(135deg, rgba(180, 40, 40, 0.4), rgba(140, 30, 30, 0.4));
  }
  
  .action-button.cancel:hover {
    background: linear-gradient(135deg, rgba(180, 40, 40, 0.6), rgba(140, 30, 30, 0.6));
    box-shadow: 0 5px 15px rgba(180, 40, 40, 0.2);
  }
  
  .button-icon {
    font-size: 1.2rem;
    margin-bottom: 0.4rem;
  }
  
  .button-text {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  
  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .automation-plan-card {
      background: linear-gradient(135deg, rgba(10, 10, 20, 0.95), rgba(20, 20, 40, 0.95));
    }
  }
</style>