<script>
    import { onMount } from 'svelte';
    import { Renderer } from '../services/render';
    
    let canvas;
    let renderer;
    let isInteractive = false;
    let currentLayout = null;
    let interactionMap = new Map();
    
    onMount(() => {
        renderer = new Renderer(canvas);
        
        // Handle window resize
        window.addEventListener('resize', handleResize);
        
        // Handle mouse events
        canvas.addEventListener('mousemove', handleMouseMove);
        canvas.addEventListener('click', handleClick);
        
        return () => {
            window.removeEventListener('resize', handleResize);
            canvas.removeEventListener('mousemove', handleMouseMove);
            canvas.removeEventListener('click', handleClick);
        };
    });
    
    function handleResize() {
        renderer.resizeCanvas();
        if (currentLayout) {
            renderer.render(currentLayout);
        }
    }
    
    function handleMouseMove(event) {
        if (!isInteractive) return;
        
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Check for hover effects
        if (currentLayout) {
            const element = findElementAt(x, y);
            if (element) {
                renderer.highlightElement(element.id);
            }
        }
    }
    
    function handleClick(event) {
        if (!isInteractive) return;
        
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Find and trigger element action
        const element = findElementAt(x, y);
        if (element && interactionMap.has(element.id)) {
            const action = interactionMap.get(element.id);
            triggerAction(action);
        }
    }
    
    function findElementAt(x, y) {
        if (!currentLayout) return null;
        
        return currentLayout.elements.find(element => {
            const { bounds } = element;
            return x >= bounds.x && x <= bounds.x + bounds.width &&
                   y >= bounds.y && y <= bounds.y + bounds.height;
        });
    }
    
    function triggerAction(action) {
        // Send action to Python backend
        window.bridge.send('user_interaction', {
            type: 'action',
            action: action
        });
    }
    
    export function updateLayout(layout, map) {
        currentLayout = layout;
        interactionMap = new Map(Object.entries(map));
        renderer.render(layout);
    }
    
    export function setInteractive(value) {
        isInteractive = value;
    }
</script>

<canvas
    bind:this={canvas}
    class="transformed-interface"
    class:interactive={isInteractive}
/>

<style>
    .transformed-interface {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 100;
    }
    
    .transformed-interface.interactive {
        pointer-events: auto;
    }
</style>
