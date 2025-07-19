/**
 * Risk Controller
 * Manages individual bot risk parameters and real-time P&L calculation
 */

class RiskController {
    constructor() {
        this.bots = {
            bot1: {
                name: 'Trend-Following Bot',
                allocation: 25,
                maxDrawdown: 5,
                stopLoss: 2,
                takeProfit: 6,
                positionSize: 1000,
                currentPL: 0,
                totalPL: 0,
                winRate: 0,
                active: true
            },
            bot2: {
                name: 'Mean-Reversion Bot',
                allocation: 25,
                maxDrawdown: 3,
                stopLoss: 1,
                takeProfit: 3,
                positionSize: 1000,
                currentPL: 0,
                totalPL: 0,
                winRate: 0,
                active: true
            },
            bot3: {
                name: 'News-Driven Bot',
                allocation: 25,
                maxDrawdown: 7,
                stopLoss: 3,
                takeProfit: 9,
                positionSize: 1000,
                currentPL: 0,
                totalPL: 0,
                winRate: 0,
                active: true
            },
            bot4: {
                name: 'ML-Powered Bot',
                allocation: 25,
                maxDrawdown: 4,
                stopLoss: 1.5,
                takeProfit: 4.5,
                positionSize: 1000,
                currentPL: 0,
                totalPL: 0,
                winRate: 0,
                active: true
            }
        };
        
        this.totalCapital = 10000;
        this.listeners = new Map();
    }
    
    /**
     * Update bot risk parameters
     */
    updateBotRisk(botId, params) {
        if (!this.bots[botId]) return false;
        
        const bot = this.bots[botId];
        
        // Update parameters
        if (params.maxDrawdown !== undefined) {
            bot.maxDrawdown = Math.max(1, Math.min(50, params.maxDrawdown));
        }
        if (params.stopLoss !== undefined) {
            bot.stopLoss = Math.max(0.5, Math.min(10, params.stopLoss));
        }
        if (params.takeProfit !== undefined) {
            bot.takeProfit = Math.max(1, Math.min(100, params.takeProfit));
        }
        if (params.positionSize !== undefined) {
            const maxPosition = this.totalCapital * (bot.allocation / 100);
            bot.positionSize = Math.min(params.positionSize, maxPosition);
        }
        
        this.emit('riskUpdate', { botId, bot });
        return true;
    }
    
    /**
     * Update bot allocation ensuring total equals 100%
     */
    updateBotAllocation(botId, newAllocation) {
        if (!this.bots[botId]) return false;
        
        newAllocation = Math.max(5, Math.min(90, newAllocation));
        
        const oldAllocation = this.bots[botId].allocation;
        const diff = newAllocation - oldAllocation;
        
        // Get other active bots
        const otherBots = Object.keys(this.bots).filter(id => 
            id !== botId && this.bots[id].active
        );
        
        if (otherBots.length === 0) return false;
        
        // Distribute difference among other bots
        const adjustment = -diff / otherBots.length;
        
        // Check if adjustment is possible
        let canAdjust = true;
        otherBots.forEach(id => {
            const newVal = this.bots[id].allocation + adjustment;
            if (newVal < 5 || newVal > 90) canAdjust = false;
        });
        
        if (!canAdjust) return false;
        
        // Apply changes
        this.bots[botId].allocation = newAllocation;
        otherBots.forEach(id => {
            this.bots[id].allocation += adjustment;
        });
        
        // Update position sizes
        this.updatePositionSizes();
        
        this.emit('allocationUpdate', this.getAllocations());
        return true;
    }
    
    /**
     * Update position sizes based on allocations
     */
    updatePositionSizes() {
        Object.keys(this.bots).forEach(botId => {
            const bot = this.bots[botId];
            const maxPosition = this.totalCapital * (bot.allocation / 100);
            bot.positionSize = Math.min(bot.positionSize, maxPosition);
        });
    }
    
    /**
     * Update real-time P&L for a bot
     */
    updatePL(botId, currentPL) {
        if (!this.bots[botId]) return;
        
        const bot = this.bots[botId];
        bot.currentPL = currentPL;
        
        // Check drawdown
        const drawdown = (currentPL < 0) ? Math.abs(currentPL / bot.positionSize * 100) : 0;
        
        if (drawdown > bot.maxDrawdown) {
            this.emit('drawdownAlert', { botId, drawdown, maxDrawdown: bot.maxDrawdown });
        }
        
        this.emit('plUpdate', { botId, currentPL, totalPL: this.getTotalPL() });
    }
    
    /**
     * Record trade result
     */
    recordTrade(botId, profit, isWin) {
        if (!this.bots[botId]) return;
        
        const bot = this.bots[botId];
        bot.totalPL += profit;
        
        // Update win rate (simplified - in production track all trades)
        if (isWin) {
            bot.winRate = Math.min(100, bot.winRate + 1);
        } else {
            bot.winRate = Math.max(0, bot.winRate - 1);
        }
        
        this.emit('tradeComplete', { botId, profit, totalPL: bot.totalPL });
    }
    
    /**
     * Get total P&L across all bots
     */
    getTotalPL() {
        return Object.values(this.bots).reduce((sum, bot) => sum + bot.totalPL, 0);
    }
    
    /**
     * Get current allocations
     */
    getAllocations() {
        const allocations = {};
        Object.keys(this.bots).forEach(botId => {
            allocations[botId] = this.bots[botId].allocation;
        });
        return allocations;
    }
    
    /**
     * Check if take profit should scale position
     */
    checkTakeProfitScaling(botId, currentProfit) {
        if (!this.bots[botId]) return { scale: false };
        
        const bot = this.bots[botId];
        const profitPercent = (currentProfit / bot.positionSize) * 100;
        
        // Scale out strategy
        if (profitPercent >= bot.takeProfit * 0.5) {
            return {
                scale: true,
                scalePercent: 50, // Take 50% off the table
                reason: 'Reached 50% of take profit target'
            };
        }
        
        if (profitPercent >= bot.takeProfit) {
            return {
                scale: true,
                scalePercent: 100, // Close full position
                reason: 'Take profit target reached'
            };
        }
        
        return { scale: false };
    }
    
    /**
     * Check if position should be added to
     */
    checkPositionAddition(botId, currentPrice, entryPrice) {
        if (!this.bots[botId]) return { add: false };
        
        const bot = this.bots[botId];
        const priceChange = ((currentPrice - entryPrice) / entryPrice) * 100;
        
        // Add to winners (pyramiding)
        if (priceChange > 1 && priceChange < bot.takeProfit * 0.3) {
            const remainingAllocation = (bot.allocation / 100) * this.totalCapital - bot.positionSize;
            
            if (remainingAllocation > 100) {
                return {
                    add: true,
                    amount: remainingAllocation * 0.5, // Add 50% of remaining
                    reason: 'Pyramiding into winner'
                };
            }
        }
        
        return { add: false };
    }
    
    /**
     * Save allocation profile
     */
    saveProfile(name) {
        const profile = {
            name,
            allocations: this.getAllocations(),
            timestamp: new Date().toISOString()
        };
        
        // In production, save to database
        localStorage.setItem(`riskProfile_${name}`, JSON.stringify(profile));
        
        return profile;
    }
    
    /**
     * Load allocation profile
     */
    loadProfile(name) {
        const saved = localStorage.getItem(`riskProfile_${name}`);
        if (!saved) return false;
        
        const profile = JSON.parse(saved);
        
        // Apply allocations
        Object.keys(profile.allocations).forEach(botId => {
            if (this.bots[botId]) {
                this.bots[botId].allocation = profile.allocations[botId];
            }
        });
        
        this.updatePositionSizes();
        this.emit('profileLoaded', profile);
        
        return true;
    }
    
    /**
     * Event emitter methods
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    emit(event, data) {
        if (!this.listeners.has(event)) return;
        
        this.listeners.get(event).forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in event listener for ${event}:`, error);
            }
        });
    }
    
    /**
     * Get bot status
     */
    getBotStatus(botId) {
        return this.bots[botId] || null;
    }
    
    /**
     * Get all bots status
     */
    getAllBotsStatus() {
        return { ...this.bots };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RiskController;
} else {
    window.RiskController = RiskController;
} 