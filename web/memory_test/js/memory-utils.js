/**
 * Memory Utilities
 * Helper functions for memory operations and data handling
 */

class MemoryUtils {
    /**
     * Format date for display
     * @param {string|number|Date} timestamp - Timestamp to format
     * @returns {string} - Formatted date string
     */
    static formatDate(timestamp) {
        if (!timestamp) return 'Unknown';
        
        let date;
        if (typeof timestamp === 'string') {
            // Handle ISO strings
            date = new Date(timestamp);
        } else if (typeof timestamp === 'number') {
            // Handle unix timestamps (seconds or milliseconds)
            date = new Date(timestamp > 10000000000 ? timestamp : timestamp * 1000);
        } else {
            date = new Date(timestamp);
        }
        
        if (isNaN(date.getTime())) return 'Invalid Date';
        
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        // For recent dates, show relative time
        if (diffDays === 0) {
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            if (diffHours === 0) {
                const diffMinutes = Math.floor(diffMs / (1000 * 60));
                if (diffMinutes === 0) {
                    return 'Just now';
                }
                return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
            }
            return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        } else if (diffDays < 7) {
            return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
        }
        
        // For older dates, show full date
        return date.toLocaleString();
    }
    
    /**
     * Format similarity score as percentage
     * @param {number} score - Similarity score (0-1)
     * @returns {string} - Formatted percentage
     */
    static formatSimilarity(score) {
        if (typeof score !== 'number' || isNaN(score)) return 'N/A';
        return `${(score * 100).toFixed(1)}%`;
    }
    
    /**
     * Generate a color based on similarity score
     * @param {number} score - Similarity score (0-1)
     * @returns {string} - Color in hex format
     */
    static getSimilarityColor(score) {
        if (typeof score !== 'number' || isNaN(score)) return '#999999';
        
        // Interpolate between red and green
        const r = Math.round(255 * (1 - score));
        const g = Math.round(255 * score);
        const b = 50;
        
        return `rgb(${r}, ${g}, ${b})`;
    }
    
    /**
     * Truncate text to a maximum length
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} - Truncated text
     */
    static truncateText(text, maxLength = 100) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    /**
     * Parse JSON safely
     * @param {string} jsonString - JSON string to parse
     * @param {*} defaultValue - Default value if parsing fails
     * @returns {*} - Parsed object or default value
     */
    static safeJsonParse(jsonString, defaultValue = {}) {
        try {
            return JSON.parse(jsonString);
        } catch (error) {
            console.error('JSON parse error:', error);
            return defaultValue;
        }
    }
    
    /**
     * Format tags array for display
     * @param {Array|string} tags - Tags array or comma-separated string
     * @returns {Array} - Array of tags
     */
    static formatTags(tags) {
        if (!tags) return [];
        
        if (Array.isArray(tags)) {
            return tags.map(tag => tag.trim()).filter(tag => tag);
        }
        
        if (typeof tags === 'string') {
            return tags.split(',').map(tag => tag.trim()).filter(tag => tag);
        }
        
        return [];
    }
    
    /**
     * Check if an object is empty
     * @param {Object} obj - Object to check
     * @returns {boolean} - Whether the object is empty
     */
    static isEmptyObject(obj) {
        return obj && Object.keys(obj).length === 0 && obj.constructor === Object;
    }
    
    /**
     * Format memory search results for display
     * @param {Array} results - Search results from memory API
     * @returns {Array} - Formatted results for UI
     */
    static formatSearchResults(results) {
        if (!results || !Array.isArray(results)) return [];
        
        return results.map(result => {
            // Handle both raw API format and websocket message format
            const content = result.content || result.text || '';
            const score = result.similarity_score || result.score || 0;
            const source = result.source || 'unknown';
            const timestamp = result.timestamp || Date.now();
            const metadata = result.metadata || {};
            const context = result.context || {};
            const confidence = result.confidence || score;
            const relevanceFactors = result.relevance_factors || [];
            const tags = this.formatTags(result.tags || context.tags || []);
            
            return {
                content,
                score,
                source,
                timestamp,
                metadata,
                context,
                confidence,
                relevanceFactors,
                tags,
                // For UI
                formattedScore: this.formatSimilarity(score),
                formattedDate: this.formatDate(timestamp),
                color: this.getSimilarityColor(score),
                truncatedContent: this.truncateText(content, 150)
            };
        });
    }
    
    /**
     * Create a memory object from form data
     * @param {HTMLFormElement} form - Memory form
     * @returns {Object} - Memory object
     */
    static createMemoryFromForm(form) {
        const content = form.querySelector('#message-content').value.trim();
        const source = form.querySelector('#message-source').value;
        const tagsInput = form.querySelector('#message-tags').value;
        const metadataInput = form.querySelector('#message-metadata').value;
        
        if (!content) {
            throw new Error('Content is required');
        }
        
        const tags = this.formatTags(tagsInput);
        let metadata = {};
        
        if (metadataInput) {
            try {
                metadata = JSON.parse(metadataInput);
                if (typeof metadata !== 'object' || metadata === null) {
                    throw new Error('Metadata must be a valid JSON object');
                }
            } catch (error) {
                throw new Error(`Invalid metadata JSON: ${error.message}`);
            }
        }
        
        return {
            content,
            source,
            tags,
            metadata
        };
    }
    
    /**
     * Create a search query object from form data
     * @param {HTMLFormElement} form - Search form
     * @returns {Object} - Search query object
     */
    static createSearchQueryFromForm(form) {
        const query = form.querySelector('#search-query').value.trim();
        const topK = parseInt(form.querySelector('#search-top-k').value, 10);
        const minSimilarity = parseFloat(form.querySelector('#search-min-similarity').value);
        const sourceFilter = form.querySelector('#source-filter').value;
        const appContext = form.querySelector('#app-context').value.trim();
        
        if (!query) {
            throw new Error('Search query is required');
        }
        
        const searchParams = {
            query,
            top_k: isNaN(topK) ? 5 : topK,
            min_similarity: isNaN(minSimilarity) ? 0.1 : minSimilarity
        };
        
        if (sourceFilter) {
            searchParams.source_filter = sourceFilter;
        }
        
        if (appContext) {
            searchParams.application_context = appContext;
        }
        
        return searchParams;
    }
    
    /**
     * Extract unique relevance factors from search results
     * @param {Array} results - Formatted search results
     * @returns {Object} - Grouped relevance factors
     */
    static extractRelevanceFactors(results) {
        if (!results || !Array.isArray(results)) return {};
        
        const factorGroups = {
            'Semantic Relevance': ['high_semantic_similarity', 'moderate_semantic_similarity', 'keyword_match'],
            'Content Characteristics': ['user_generated', 'system_generated', 'application_context_match'],
            'Usage Patterns': ['frequently_accessed', 'recently_accessed', 'high_importance']
        };
        
        const factorCounts = {};
        
        // Count occurrences of each factor
        results.forEach(result => {
            if (result.relevanceFactors && Array.isArray(result.relevanceFactors)) {
                result.relevanceFactors.forEach(factor => {
                    factorCounts[factor] = (factorCounts[factor] || 0) + 1;
                });
            }
        });
        
        // Group factors by category
        const groupedFactors = {};
        
        for (const [group, factors] of Object.entries(factorGroups)) {
            const relevantFactors = factors.filter(factor => factorCounts[factor]);
            
            if (relevantFactors.length > 0) {
                groupedFactors[group] = relevantFactors.map(factor => ({
                    name: this.formatFactorName(factor),
                    count: factorCounts[factor],
                    percentage: factorCounts[factor] / results.length
                }));
            }
        }
        
        // Add any uncategorized factors
        const uncategorizedFactors = Object.keys(factorCounts).filter(factor => {
            return !Object.values(factorGroups).flat().includes(factor);
        });
        
        if (uncategorizedFactors.length > 0) {
            groupedFactors['Other Factors'] = uncategorizedFactors.map(factor => ({
                name: this.formatFactorName(factor),
                count: factorCounts[factor],
                percentage: factorCounts[factor] / results.length
            }));
        }
        
        return groupedFactors;
    }
    
    /**
     * Format a relevance factor name for display
     * @param {string} factor - Relevance factor
     * @returns {string} - Formatted factor name
     */
    static formatFactorName(factor) {
        if (!factor) return '';
        
        // Split by underscore and capitalize each word
        return factor
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
}

// Export for module usage
window.MemoryUtils = MemoryUtils;