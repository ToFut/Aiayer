<script>
    import { onMount, onDestroy } from 'svelte';
    
    // Props
    export let active = false;
    export let intensity = 0.5; // 0-1 controls animation intensity
    
    // Canvas element and animation state
    let canvas;
    let ctx;
    let width;
    let height;
    let particles = [];
    let animationFrame;
    let isInitialized = false;
    
    // Configuration
    const config = {
        particleCount: 80,
        particleBaseSize: 4,
        particleAddedSize: 3,
        particleBaseSpeed: 0.1,
        particleVariance: 1,
        baseHue: 210, // Blue hue
        hueVariance: 20,
        baseOpacity: 0.6,
        opacityVariance: 0.3
    };
    
    onMount(() => {
        initializeCanvas();
        window.addEventListener('resize', handleResize);
        
        return () => {
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrame);
        };
    });
    
    onDestroy(() => {
        cancelAnimationFrame(animationFrame);
    });
    
    // Initialize the canvas and particles
    function initializeCanvas() {
        if (!canvas) return;
        
        // Set canvas size to match window
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
        
        // Get context
        ctx = canvas.getContext('2d');
        
        // Create initial particles
        createParticles();
        
        // Start animation loop
        startAnimation();
        
        isInitialized = true;
    }
    
    // Handle window resize
    function handleResize() {
        // Update canvas dimensions
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
        
        // Re-create particles for new dimensions
        createParticles();
    }
    
    // Create particles
    function createParticles() {
        particles = [];
        
        for (let i = 0; i < config.particleCount; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                size: config.particleBaseSize + Math.random() * config.particleAddedSize,
                speedX: (Math.random() - 0.5) * config.particleVariance * 2,
                speedY: (Math.random() - 0.5) * config.particleVariance * 2,
                hue: config.baseHue + (Math.random() * config.hueVariance * 2 - config.hueVariance),
                opacity: config.baseOpacity + (Math.random() * config.opacityVariance * 2 - config.opacityVariance)
            });
        }
    }
    
    // Animation loop
    function startAnimation() {
        function animate() {
            if (!ctx) return;
            
            // Create gradient background
            const gradient = ctx.createLinearGradient(0, 0, width, height);
            gradient.addColorStop(0, 'rgba(25, 60, 100, 0.5)');
            gradient.addColorStop(1, 'rgba(40, 80, 140, 0.5)');
            
            // Clear and fill background
            ctx.globalCompositeOperation = 'source-over';
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, width, height);
            
            // Draw particles with additive blending
            ctx.globalCompositeOperation = 'lighter';
            
            // Update and draw each particle
            particles.forEach(particle => {
                // Skip if not active
                if (!active) {
                    return;
                }
                
                // Apply intensity to movement
                const adjustedSpeedX = particle.speedX * intensity;
                const adjustedSpeedY = particle.speedY * intensity;
                
                // Move particle
                particle.x += adjustedSpeedX;
                particle.y += adjustedSpeedY;
                
                // Wrap around edges
                if (particle.x < 0) particle.x = width;
                if (particle.x > width) particle.x = 0;
                if (particle.y < 0) particle.y = height;
                if (particle.y > height) particle.y = 0;
                
                // Create glow effect
                const glow = ctx.createRadialGradient(
                    particle.x, particle.y, 0,
                    particle.x, particle.y, particle.size * 2
                );
                
                // Adjust opacity based on intensity
                const adjustedOpacity = particle.opacity * intensity;
                
                glow.addColorStop(0, `hsla(${particle.hue}, 80%, 70%, ${adjustedOpacity})`);
                glow.addColorStop(1, `hsla(${particle.hue}, 80%, 70%, 0)`);
                
                ctx.beginPath();
                ctx.fillStyle = glow;
                ctx.arc(particle.x, particle.y, particle.size * 2, 0, Math.PI * 2);
                ctx.fill();
            });
            
            animationFrame = requestAnimationFrame(animate);
        }
        
        animate();
    }
    
    // Watch for changes to the active prop
    $: if (isInitialized && active) {
        if (!animationFrame) {
            startAnimation();
        }
    } else if (isInitialized && !active) {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
            
            // Clear canvas when inactive
            if (ctx) {
                ctx.clearRect(0, 0, width, height);
            }
        }
    }
</script>

<canvas 
    bind:this={canvas} 
    class="animated-background"
    class:active={active}
></canvas>

<style>
    .animated-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1;
        opacity: 0;
        transition: opacity 1s ease-in-out;
    }
    
    .animated-background.active {
        opacity: 1;
    }
</style>