import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bot, 
  Pause, 
  Play, 
  Square, 
  CheckCircle2, 
  RefreshCw,
  Cpu,
  Brain,
  Zap,
  Clock,
  Database
} from 'lucide-react';
import { useStore } from '../store/useStore';

const stateColors = {
  active: { bg: 'bg-cyber-success/10', border: 'border-cyber-success/30', text: 'text-cyber-success', icon: Play },
  paused: { bg: 'bg-cyber-warning/10', border: 'border-cyber-warning/30', text: 'text-cyber-warning', icon: Pause },
  stopped: { bg: 'bg-cyber-danger/10', border: 'border-cyber-danger/30', text: 'text-cyber-danger', icon: Square },
  finished: { bg: 'bg-cyber-accent/10', border: 'border-cyber-accent/30', text: 'text-cyber-accent', icon: CheckCircle2 },
};

export default function AgentOverview() {
  const { 
    agentStates, 
    isRunning,
    pauseAgent,
    resumeAgent,
    stopAgent,
    finishAgent,
    restartAgent,
    refreshStatus,
    isLoading
  } = useStore();
  
  const agents = Object.entries(agentStates);
  
  if (agents.length === 0) {
    return (
      <motion.div 
        className="glass rounded-2xl p-8 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <Bot size={64} className="mx-auto mb-4 text-cyber-muted opacity-30" />
        <h3 className="text-lg font-semibold text-cyber-text mb-2">No Active Agents</h3>
        <p className="text-cyber-muted text-sm">
          Start a session to see agent states here
        </p>
      </motion.div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header Info */}
      <motion.div 
        className="glass rounded-2xl p-5 card-cyber"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-cyber-accent/10 border border-cyber-accent/30">
              <Cpu size={24} className="text-cyber-accent" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-cyan-100">Active Agents</h2>
              <p className="text-sm text-cyber-muted">
                {agents.length} agent{agents.length !== 1 ? 's' : ''} in session
              </p>
            </div>
          </div>
          
          <button
            onClick={refreshStatus}
            disabled={isLoading}
            className="btn-cyber flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 text-sm font-medium transition-all disabled:opacity-50"
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </motion.div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <AnimatePresence>
          {agents.map(([agentName, state], index) => {
            const stateConfig = stateColors[state.state] || stateColors.active;
            const StateIcon = stateConfig.icon;
            const runtime = state.runtime || {};
            
            return (
              <motion.div
                key={agentName}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ delay: index * 0.05 }}
                className={`glass rounded-2xl p-5 border ${stateConfig.border} card-cyber`}
              >
                {/* Agent Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-xl ${stateConfig.bg}`}>
                      <Bot size={20} className={stateConfig.text} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-cyber-text">{agentName}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <StateIcon size={12} className={stateConfig.text} />
                        <span className={`text-xs font-medium uppercase tracking-wider ${stateConfig.text}`}>
                          {state.state}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* State Info */}
                {state.reason && (
                  <div className="mb-4 p-3 rounded-lg bg-cyber-darker/50 border border-cyber-border/30">
                    <p className="text-xs text-cyber-muted">Reason: {state.reason}</p>
                  </div>
                )}
                
                {/* Runtime Info */}
                {runtime && (
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {runtime.sleep_seconds !== undefined && (
                      <div className="flex items-center gap-2 text-xs text-cyber-muted">
                        <Clock size={12} />
                        <span>Sleep: {runtime.sleep_seconds}s</span>
                      </div>
                    )}
                    {runtime.memory?.count !== undefined && (
                      <div className="flex items-center gap-2 text-xs text-cyber-muted">
                        <Brain size={12} />
                        <span>Memory: {runtime.memory.count}</span>
                      </div>
                    )}
                    {runtime.memory?.top_k !== undefined && (
                      <div className="flex items-center gap-2 text-xs text-cyber-muted">
                        <Database size={12} />
                        <span>Top K: {runtime.memory.top_k}</span>
                      </div>
                    )}
                    {runtime.mcp?.configured && (
                      <div className="flex items-center gap-2 text-xs text-cyber-success">
                        <Zap size={12} />
                        <span>MCP: {runtime.mcp.allowed_tools?.length || 0} tools</span>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Changed At */}
                {state.changed_at && (
                  <div className="text-[0.65rem] text-cyber-muted font-mono mb-4">
                    Last changed: {new Date(state.changed_at).toLocaleTimeString()}
                  </div>
                )}
                
                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2">
                  {state.state === 'active' && (
                    <>
                      <button
                        onClick={() => pauseAgent(agentName)}
                        className="btn-cyber flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-cyber-warning/10 border border-cyber-warning/30 text-cyber-warning hover:bg-cyber-warning/20 text-xs font-medium transition-all"
                      >
                        <Pause size={12} />
                        Pause
                      </button>
                      <button
                        onClick={() => stopAgent(agentName)}
                        className="btn-cyber flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-cyber-danger/10 border border-cyber-danger/30 text-cyber-danger hover:bg-cyber-danger/20 text-xs font-medium transition-all"
                      >
                        <Square size={12} />
                        Stop
                      </button>
                      <button
                        onClick={() => finishAgent(agentName)}
                        className="btn-cyber flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-cyber-accent/10 border border-cyber-accent/30 text-cyber-accent hover:bg-cyber-accent/20 text-xs font-medium transition-all"
                      >
                        <CheckCircle2 size={12} />
                        Finish
                      </button>
                    </>
                  )}
                  
                  {state.state === 'paused' && (
                    <>
                      <button
                        onClick={() => resumeAgent(agentName)}
                        className="btn-cyber flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-cyber-success/10 border border-cyber-success/30 text-cyber-success hover:bg-cyber-success/20 text-xs font-medium transition-all"
                      >
                        <Play size={12} />
                        Resume
                      </button>
                      <button
                        onClick={() => stopAgent(agentName)}
                        className="btn-cyber flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-cyber-danger/10 border border-cyber-danger/30 text-cyber-danger hover:bg-cyber-danger/20 text-xs font-medium transition-all"
                      >
                        <Square size={12} />
                        Stop
                      </button>
                    </>
                  )}
                  
                  {(state.state === 'stopped' || state.state === 'finished') && (
                    <button
                      onClick={() => restartAgent(agentName)}
                      className="btn-cyber flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-cyber-success/10 border border-cyber-success/30 text-cyber-success hover:bg-cyber-success/20 text-xs font-medium transition-all"
                    >
                      <RefreshCw size={12} />
                      Restart
                    </button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
