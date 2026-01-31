import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Play, 
  Square, 
  RotateCcw, 
  Trash2,
  Activity,
  Radio
} from 'lucide-react';
import { useStore } from '../store/useStore';
import MessageFeed from './MessageFeed';

export default function LiveMonitor() {
  const { 
    isRunning,
    topic,
    sessionId,
    isLoading,
    startSession,
    stopSession,
    resumeSession,
    clearMemory,
  } = useStore();
  
  const [topicInput, setTopicInput] = useState('');
  
  const handleStart = async () => {
    if (!topicInput.trim()) return;
    await startSession(topicInput.trim());
    setTopicInput('');
  };
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
      {/* Quick Actions */}
      <motion.div 
        className="glass rounded-2xl p-5 card-cyber"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <h2 className="text-lg font-semibold mb-4 text-cyan-100 flex items-center gap-2">
          <Radio size={18} className="text-cyber-accent" />
          Quick Actions
        </h2>
        
        {/* Status Indicator */}
        <div className={`p-4 rounded-xl mb-4 ${isRunning ? 'bg-cyber-success/10 border border-cyber-success/30' : 'bg-cyber-warning/10 border border-cyber-warning/30'}`}>
          <div className="flex items-center gap-3">
            <motion.div
              className={`w-3 h-3 rounded-full ${isRunning ? 'bg-cyber-success' : 'bg-cyber-warning'}`}
              animate={isRunning ? {
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1],
              } : {}}
              transition={{ duration: 1, repeat: Infinity }}
            />
            <span className={`text-sm font-semibold ${isRunning ? 'text-cyber-success' : 'text-cyber-warning'}`}>
              {isRunning ? 'Session Active' : 'Session Stopped'}
            </span>
          </div>
          {topic && (
            <p className="text-xs text-cyber-muted mt-2 font-mono truncate">
              Topic: {topic}
            </p>
          )}
          {sessionId && (
            <p className="text-[0.65rem] text-cyber-muted mt-1 font-mono">
              ID: {sessionId.substring(0, 16)}...
            </p>
          )}
        </div>
        
        {/* Action Buttons */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <button
            onClick={resumeSession}
            disabled={isLoading || isRunning}
            className="btn-cyber flex flex-col items-center justify-center gap-2 p-3 rounded-xl bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <RotateCcw size={18} />
            Resume
          </button>
          <button
            onClick={stopSession}
            disabled={isLoading || !isRunning}
            className="btn-cyber flex flex-col items-center justify-center gap-2 p-3 rounded-xl bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Square size={18} />
            Stop
          </button>
          <button
            onClick={clearMemory}
            disabled={isLoading}
            className="btn-cyber flex flex-col items-center justify-center gap-2 p-3 rounded-xl bg-cyber-danger/10 border border-cyber-danger/30 text-cyber-danger hover:bg-cyber-danger/20 text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Trash2 size={18} />
            Clear
          </button>
        </div>
        
        {/* New Topic */}
        <div className="space-y-3">
          <div>
            <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
              New Topic
            </label>
            <input
              type="text"
              value={topicInput}
              onChange={(e) => setTopicInput(e.target.value)}
              placeholder="Enter topic to start"
              className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-3 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
              onKeyDown={(e) => e.key === 'Enter' && handleStart()}
            />
          </div>
          <button
            onClick={handleStart}
            disabled={isLoading || !topicInput.trim()}
            className="btn-cyber w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-cyber-accent text-cyber-dark font-semibold text-sm hover:shadow-lg hover:shadow-cyber-accent/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Play size={16} />
            Start New Session
          </button>
        </div>
      </motion.div>

      {/* Live Feed */}
      <motion.div 
        className="glass rounded-2xl p-5 min-h-[600px] flex flex-col relative overflow-hidden"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        {/* Scan line effect */}
        {isRunning && (
          <motion.div
            className="absolute inset-0 pointer-events-none"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyber-accent/50 to-transparent"
              animate={{ y: ['0%', '100%'] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
            />
          </motion.div>
        )}
        
        <h2 className="text-lg font-semibold mb-4 text-cyan-100 flex items-center gap-2 relative z-10">
          <Activity size={18} className={isRunning ? 'text-cyber-success animate-pulse' : 'text-cyber-muted'} />
          Live Feed
          {isRunning && (
            <span className="text-[0.6rem] uppercase tracking-widest text-cyber-success bg-cyber-success/10 px-2 py-1 rounded-full">
              Live
            </span>
          )}
        </h2>
        
        <MessageFeed />
      </motion.div>
    </div>
  );
}
