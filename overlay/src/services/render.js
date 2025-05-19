export class Renderer {
    constructor(canvas) {
        this.ctx = canvas.getContext('2d');
        this.elements = new Map();
        this.animations = new Map();
        this.isRendering = false;
    }

    setCanvas(canvas) {
        this.ctx = canvas.getContext('2d');
        this.resizeCanvas();
    }

    resizeCanvas() {
        this.ctx.canvas.width = window.innerWidth;
        this.ctx.canvas.height = window.innerHeight;
    }

    clear() {
        this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
    }

    render(layout) {
        if (this.isRendering) return;
        this.isRendering = true;

        requestAnimationFrame(() => {
            this.clear();
            this.renderElements(layout?.elements || []);
            this.isRendering = false;
        });
    }

    renderElements(elements) {
        elements.forEach(element => {
            const cached = this.elements.get(element.id);
            
            if (!cached || this.hasElementChanged(element, cached)) {
                this.renderElement(element);
                this.elements.set(element.id, element);
            }
        });
    }

    renderElement(element) {
        const { type, bounds, style, content } = element;
        
        this.ctx.save();
        
        // Apply styles
        if (style) {
            if (style.backgroundColor) {
                this.ctx.fillStyle = style.backgroundColor;
            }
            if (style.borderColor) {
                this.ctx.strokeStyle = style.borderColor;
            }
            if (style.borderWidth) {
                this.ctx.lineWidth = style.borderWidth;
            }
        }

        // Draw element based on type
        switch (type) {
            case 'rectangle':
                this.drawRectangle(bounds);
                break;
            case 'text':
                this.drawText(content, bounds, style);
                break;
            case 'button':
                this.drawButton(content, bounds, style);
                break;
            // Add more element types as needed
        }

        this.ctx.restore();
    }

    drawRectangle(bounds) {
        const { x, y, width, height } = bounds;
        this.ctx.fillRect(x, y, width, height);
        this.ctx.strokeRect(x, y, width, height);
    }

    drawText(text, bounds, style) {
        const { x, y } = bounds;
        
        if (style) {
            if (style.font) {
                this.ctx.font = style.font;
            }
            if (style.color) {
                this.ctx.fillStyle = style.color;
            }
        }

        this.ctx.fillText(text, x, y);
    }

    drawButton(text, bounds, style) {
        this.drawRectangle(bounds);
        this.drawText(text, {
            x: bounds.x + bounds.width / 2,
            y: bounds.y + bounds.height / 2
        }, style);
    }

    hasElementChanged(newElement, oldElement) {
        return JSON.stringify(newElement) !== JSON.stringify(oldElement);
    }

    animateElement(elementId, animation) {
        if (this.animations.has(elementId)) {
            cancelAnimationFrame(this.animations.get(elementId));
        }

        const animate = () => {
            const element = this.elements.get(elementId);
            if (!element) return;

            const progress = animation.update();
            if (progress < 1) {
                this.animations.set(elementId, requestAnimationFrame(animate));
            } else {
                this.animations.delete(elementId);
            }

            this.renderElement(animation.apply(element, progress));
        };

        animate();
    }

    highlightElement(elementId, duration = 1000) {
        const element = this.elements.get(elementId);
        if (!element) return;

        const animation = {
            startTime: performance.now(),
            duration,
            update: function() {
                const elapsed = performance.now() - this.startTime;
                return Math.min(elapsed / this.duration, 1);
            },
            apply: function(element, progress) {
                const highlighted = { ...element };
                highlighted.style = {
                    ...highlighted.style,
                    backgroundColor: `rgba(255, 255, 0, ${0.3 * (1 - progress)})`
                };
                return highlighted;
            }
        };

        this.animateElement(elementId, animation);
    }
}
