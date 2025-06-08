<script>
  import AutomationPlanCard from './AutomationPlanCard.svelte';
  import { createEventDispatcher } from 'svelte';
  
  export let message = {};
  export let isUser = false;
  
  const dispatch = createEventDispatcher();
  
  // Check if the message content looks like an automation plan
  function isAutomationPlan(content) {
    if (!content) return false;
    
    // Look for common patterns in automation plans
    const hasAutomationTitle = content.includes('**AUTOMATION EXECUTION PLAN**') || 
                              content.includes('🎯 **AUTOMATION EXECUTION PLAN**');
    const hasTaskType = content.includes('**🔍 Task Type:**');
    const hasSteps = content.includes('**🚀 Automation Steps:**');
    
    return hasAutomationTitle && hasTaskType && hasSteps;
  }
  
  function handleExecute() {
    // Extract plan ID
    const planIdMatch = message.content.match(/\*\*🆔 Plan ID:\*\* `([^`]+)`/);
    const planId = planIdMatch ? planIdMatch[1] : null;
    
    if (planId) {
      dispatch('executeplan', { planId });
    }
  }
  
  function handleCancel() {
    // Extract plan ID
    const planIdMatch = message.content.match(/\*\*🆔 Plan ID:\*\* `([^`]+)`/);
    const planId = planIdMatch ? planIdMatch[1] : null;
    
    if (planId) {
      dispatch('cancelplan', { planId });
    }
  }
  
  function handleModify() {
    // Extract plan ID
    const planIdMatch = message.content.match(/\*\*🆔 Plan ID:\*\* `([^`]+)`/);
    const planId = planIdMatch ? planIdMatch[1] : null;
    
    if (planId) {
      dispatch('modifyplan', { planId });
    }
  }
  
  function handleSimulate() {
    // Extract plan ID
    const planIdMatch = message.content.match(/\*\*🆔 Plan ID:\*\* `([^`]+)`/);
    const planId = planIdMatch ? planIdMatch[1] : null;
    
    if (planId) {
      dispatch('simulateplan', { planId });
    }
  }
</script>

{#if isAutomationPlan(message.content)}
  <AutomationPlanCard 
    plan={message} 
    onExecute={handleExecute}
    onCancel={handleCancel}
    onModify={handleModify}
    onSimulate={handleSimulate}
  />
{:else}
  <div class="message-text">
    {message.content}
  </div>
{/if}

<style>
  .message-text {
    font-size: 0.9rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }
</style>