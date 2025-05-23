/**
 * Enhanced Interactions Service
 * Provides Apple-inspired interaction patterns, gestures, and accessibility features
 */

export class EnhancedInteractions {
    constructor() {
        this.gestureThreshold = 50;
        this.longPressThreshold = 500;
        this.doubleTapThreshold = 300;
        this.vibrationEnabled = true;
        this.soundEnabled = true;
        this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        this.setupEventListeners();
        this.setupAccessibility();
    }
    
    setupEventListeners() {
        // Listen for preference changes
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.reducedMotion = e.matches;
        });
    }
    
    setupAccessibility() {
        // Enhanced focus management
        document.addEventListener('keydown', this.handleKeyboardNavigation.bind(this));
        
        // Screen reader announcements
        this.createAriaLiveRegion();
    }
    
    createAriaLiveRegion() {
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.style.position = 'absolute';
        liveRegion.style.left = '-10000px';
        liveRegion.style.width = '1px';
        liveRegion.style.height = '1px';
        liveRegion.style.overflow = 'hidden';
        liveRegion.id = 'sr-announcements';
        document.body.appendChild(liveRegion);
    }
    
    announceToScreenReader(message) {
        const liveRegion = document.getElementById('sr-announcements');
        if (liveRegion) {
            liveRegion.textContent = message;
        }
    }
    
    handleKeyboardNavigation(event) {
        // Enhanced keyboard shortcuts
        switch (event.key) {
            case 'ArrowUp':
                if (event.altKey) {
                    event.preventDefault();
                    this.scrollToPreviousMessage();
                }
                break;
            case 'ArrowDown':
                if (event.altKey) {
                    event.preventDefault();
                    this.scrollToNextMessage();
                }
                break;
            case '/':
                if (!event.target.matches('input, textarea')) {
                    event.preventDefault();
                    this.focusSearchOrInput();
                }
                break;
        }
    }
    
    // Gesture Recognition System
    createGestureHandler(element, callbacks = {}) {
        let touchStart = null;
        let touchCurrent = null;
        let longPressTimer = null;
        let lastTap = 0;
        
        const handleTouchStart = (event) => {
            touchStart = {
                x: event.touches[0].clientX,
                y: event.touches[0].clientY,
                time: Date.now()
            };
            
            // Start long press detection
            longPressTimer = setTimeout(() => {
                if (callbacks.onLongPress) {
                    this.hapticFeedback('medium');
                    callbacks.onLongPress(touchStart);
                }
            }, this.longPressThreshold);
        };
        
        const handleTouchMove = (event) => {
            if (!touchStart) return;
            
            touchCurrent = {
                x: event.touches[0].clientX,
                y: event.touches[0].clientY,
                time: Date.now()
            };
            
            const deltaX = touchCurrent.x - touchStart.x;
            const deltaY = touchCurrent.y - touchStart.y;
            const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            
            // Cancel long press if moved too much
            if (distance > 10 && longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
            
            // Swipe detection
            if (distance > this.gestureThreshold) {
                const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
                const direction = this.getSwipeDirection(angle);
                
                if (callbacks.onSwipe) {
                    callbacks.onSwipe(direction, { deltaX, deltaY, distance });
                }
            }
            
            // Pan/drag detection
            if (callbacks.onPan) {
                callbacks.onPan({ deltaX, deltaY, distance });
            }
        };
        
        const handleTouchEnd = (event) => {
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
            
            if (!touchStart) return;
            
            const touchEnd = {
                x: event.changedTouches[0].clientX,
                y: event.changedTouches[0].clientY,
                time: Date.now()
            };
            
            const deltaTime = touchEnd.time - touchStart.time;
            const deltaX = touchEnd.x - touchStart.x;
            const deltaY = touchEnd.y - touchStart.y;
            const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            
            // Tap detection
            if (distance < 10 && deltaTime < 300) {
                const now = Date.now();
                
                // Double tap detection
                if (now - lastTap < this.doubleTapThreshold) {
                    if (callbacks.onDoubleTap) {
                        this.hapticFeedback('light');
                        callbacks.onDoubleTap(touchStart);
                    }
                } else {
                    if (callbacks.onTap) {
                        this.hapticFeedback('light');
                        callbacks.onTap(touchStart);
                    }
                }
                
                lastTap = now;
            }
            
            // Swipe completion
            if (distance > this.gestureThreshold && callbacks.onSwipeEnd) {
                const velocity = distance / deltaTime;
                const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
                const direction = this.getSwipeDirection(angle);
                
                callbacks.onSwipeEnd(direction, { deltaX, deltaY, distance, velocity });
            }
            
            touchStart = null;
            touchCurrent = null;
        };
        
        element.addEventListener('touchstart', handleTouchStart, { passive: false });
        element.addEventListener('touchmove', handleTouchMove, { passive: false });
        element.addEventListener('touchend', handleTouchEnd, { passive: false });
        
        // Return cleanup function
        return () => {
            element.removeEventListener('touchstart', handleTouchStart);
            element.removeEventListener('touchmove', handleTouchMove);
            element.removeEventListener('touchend', handleTouchEnd);
            if (longPressTimer) clearTimeout(longPressTimer);
        };
    }
    
    getSwipeDirection(angle) {
        if (angle >= -45 && angle <= 45) return 'right';
        if (angle >= 45 && angle <= 135) return 'down';
        if (angle >= 135 || angle <= -135) return 'left';
        if (angle >= -135 && angle <= -45) return 'up';
        return 'unknown';
    }
    
    // Haptic Feedback System
    hapticFeedback(type = 'light') {
        if (!this.vibrationEnabled || !navigator.vibrate) return;
        
        const patterns = {
            light: [10],
            medium: [10, 5, 10],
            heavy: [20, 10, 20],
            success: [10, 5, 10, 5, 10],
            error: [20, 10, 20, 10, 20, 10, 20],
            notification: [10, 5, 10, 5, 30]
        };
        
        navigator.vibrate(patterns[type] || patterns.light);
    }
    
    // Sound System
    playSound(type) {
        if (!this.soundEnabled) return;
        
        try {
            const audioContext = this.getAudioContext();
            this.synthesizeSound(audioContext, type);
        } catch (error) {
            console.warn('Could not play sound:', error);
        }
    }
    
    getAudioContext() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        return this.audioContext;
    }
    
    synthesizeSound(audioContext, type) {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        const soundConfig = {
            click: { frequency: 800, duration: 0.1, volume: 0.02 },
            success: { frequency: 600, duration: 0.2, volume: 0.025 },
            error: { frequency: 300, duration: 0.3, volume: 0.03 },
            notification: { frequency: 440, duration: 0.15, volume: 0.02 },
            send: { frequency: 1000, duration: 0.08, volume: 0.015 },
            receive: { frequency: 700, duration: 0.12, volume: 0.02 },
            'interface-open': { frequency: 600, duration: 0.15, volume: 0.02 },
            'interface-close': { frequency: 400, duration: 0.15, volume: 0.02 },
            'interface-click': { frequency: 800, duration: 0.08, volume: 0.015 },
            'interface-toggle': { frequency: 700, duration: 0.1, volume: 0.02 },
            'interface-clear': { frequency: 500, duration: 0.12, volume: 0.02 }
        };
        
        const config = soundConfig[type] || soundConfig.click;
        
        oscillator.frequency.setValueAtTime(config.frequency, audioContext.currentTime);
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0, audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(config.volume, audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + config.duration);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + config.duration);
    }
    
    // Animation Utilities
    createSpringAnimation(element, property, targetValue, options = {}) {
        if (this.reducedMotion) {
            element.style[property] = targetValue;
            return Promise.resolve();
        }
        
        const {
            stiffness = 200,
            damping = 20,
            mass = 1,
            duration = 800
        } = options;
        
        return new Promise((resolve) => {
            const startValue = parseFloat(getComputedStyle(element)[property]) || 0;
            const startTime = performance.now();
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Spring physics calculation
                const omega = Math.sqrt(stiffness / mass);
                const zeta = damping / (2 * Math.sqrt(stiffness * mass));
                
                let value;
                if (zeta < 1) {
                    // Underdamped
                    const omegaD = omega * Math.sqrt(1 - zeta * zeta);
                    value = targetValue - (targetValue - startValue) * 
                           Math.exp(-zeta * omega * elapsed / 1000) * 
                           Math.cos(omegaD * elapsed / 1000);
                } else {
                    // Critically damped or overdamped
                    value = targetValue - (targetValue - startValue) * 
                           Math.exp(-omega * elapsed / 1000) * 
                           (1 + omega * elapsed / 1000);
                }
                
                element.style[property] = value + (property.includes('translate') ? 'px' : '');
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.style[property] = targetValue;
                    resolve();
                }
            };
            
            requestAnimationFrame(animate);
        });
    }
    
    // Accessibility Helpers
    scrollToPreviousMessage() {
        const messages = document.querySelectorAll('.message');
        const chatContainer = document.querySelector('.chat-messages');
        
        if (messages.length === 0 || !chatContainer) return;
        
        const scrollTop = chatContainer.scrollTop;
        let targetMessage = null;
        
        for (let i = messages.length - 1; i >= 0; i--) {
            const messageTop = messages[i].offsetTop;
            if (messageTop < scrollTop - 10) {
                targetMessage = messages[i];
                break;
            }
        }
        
        if (targetMessage) {
            targetMessage.scrollIntoView({ behavior: 'smooth', block: 'start' });
            this.announceToScreenReader(`Scrolled to previous message: ${targetMessage.textContent.slice(0, 100)}...`);
        }
    }
    
    scrollToNextMessage() {
        const messages = document.querySelectorAll('.message');
        const chatContainer = document.querySelector('.chat-messages');
        
        if (messages.length === 0 || !chatContainer) return;
        
        const scrollTop = chatContainer.scrollTop;
        const containerHeight = chatContainer.clientHeight;
        let targetMessage = null;
        
        for (let i = 0; i < messages.length; i++) {
            const messageTop = messages[i].offsetTop;
            if (messageTop > scrollTop + containerHeight + 10) {
                targetMessage = messages[i];
                break;
            }
        }
        
        if (targetMessage) {
            targetMessage.scrollIntoView({ behavior: 'smooth', block: 'start' });
            this.announceToScreenReader(`Scrolled to next message: ${targetMessage.textContent.slice(0, 100)}...`);
        }
    }
    
    focusSearchOrInput() {
        const input = document.querySelector('.message-input');
        if (input) {
            input.focus();
            this.announceToScreenReader('Message input focused');
        }
    }
    
    // Settings Management
    toggleVibration() {
        this.vibrationEnabled = !this.vibrationEnabled;
        localStorage.setItem('enhancedInteractions.vibration', this.vibrationEnabled);
        this.hapticFeedback('medium');
        return this.vibrationEnabled;
    }
    
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        localStorage.setItem('enhancedInteractions.sound', this.soundEnabled);
        if (this.soundEnabled) {
            this.playSound('success');
        }
        return this.soundEnabled;
    }
    
    loadSettings() {
        const vibration = localStorage.getItem('enhancedInteractions.vibration');
        const sound = localStorage.getItem('enhancedInteractions.sound');
        
        if (vibration !== null) {
            this.vibrationEnabled = JSON.parse(vibration);
        }
        
        if (sound !== null) {
            this.soundEnabled = JSON.parse(sound);
        }
    }
    
    // Cleanup
    destroy() {
        if (this.audioContext) {
            this.audioContext.close();
        }
    }
}

// Export convenience functions
export const enhancedInteractions = new EnhancedInteractions();

export const haptic = (type) => enhancedInteractions.hapticFeedback(type);
export const sound = (type) => enhancedInteractions.playSound(type);
export const gesture = (element, callbacks) => enhancedInteractions.createGestureHandler(element, callbacks);
export const spring = (element, property, value, options) => 
    enhancedInteractions.createSpringAnimation(element, property, value, options);
export const announce = (message) => enhancedInteractions.announceToScreenReader(message);