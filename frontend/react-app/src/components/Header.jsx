import { motion } from 'framer-motion';
import { Activity, Wifi, WifiOff, Clock } from 'lucide-react';
import { useStore } from '../store/useStore';

export default function Header() {
  const { isRunning, topic, sessionId, connectionStatus, lastUpdated } = useStore();
  
  return (
    <header className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-6 mb-8">
      {/* Brand Section */}
      <motion.section 
        className="glass rounded-2xl p-6 relative overflow-hidden"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Decorative glow */}
        <div className="absolute inset-0 bg-gradient-to-r from-cyber-accent/10 via-transparent to-transparent pointer-events-none" />
        
        <div className="relative z-10">
          <div className="text-[0.65rem] uppercase tracking-[0.25em] text-cyber-muted mb-3 font-medium">
            AI Agent Platform
          </div>
          <h1 className="text-3xl font-bold tracking-tight mb-2 bg-gradient-to-r from-cyber-text via-cyber-accent to-cyber-accent2 bg-clip-text text-transparent">
            ChatMode
          </h1>
          <p className="text-cyber-muted text-sm leading-relaxed max-w-xl">
            Multi-agent orchestration system with semantic memory, voice synthesis, and real-time conversation control.
          </p>
        </div>
        
        {/* Corner decoration */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyber-accent/5 to-transparent rounded-bl-full" />
      </motion.section>

      {/* Status Card */}
      <motion.section 
        className="glass rounded-2xl p-5 min-w-[300px] flex flex-col justify-between"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        {/* Connection & Running Status */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {/* Running Status */}
            <div className="relative">
              <motion.div
                className={`w-3 h-3 rounded-full ${isRunning ? 'bg-cyber-success' : 'bg-cyber-warning'}`}
                animate={isRunning ? {
                  boxShadow: [
                    '0 0 0 0 rgba(34, 197, 94, 0.4)',
                    '0 0 0 10px rgba(34, 197, 94, 0)',
                  ]
                } : {}}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            </div>
            <span className="text-sm uppercase tracking-wider font-semibold">
              {isRunning ? (
                <span className="text-cyber-success">Running</span>
              ) : (
                <span className="text-cyber-warning">Stopped</span>
              )}
            </span>
          </div>
          
          {/* Connection Status */}
          <div className={`flex items-center gap-2 text-xs ${
            connectionStatus === 'connected' ? 'text-cyber-success' : 'text-cyber-danger'
          }`}>
            {connectionStatus === 'connected' ? (
              <Wifi size={14} />
            ) : (
              <WifiOff size={14} />
            )}
            <span className="uppercase tracking-wider">
              {connectionStatus === 'connected' ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>

        {/* Topic */}
        <div className="mb-3">
          <div className="text-[0.65rem] uppercase tracking-wider text-cyber-muted mb-1">
            Topic
          </div>
          <div className="text-sm font-mono text-cyber-text truncate">
            {topic || 'Not set'}
          </div>
        </div>

        {/* Session ID & Last Updated */}
        <div className="flex items-center justify-between text-xs text-cyber-muted font-mono">
          <div className="flex items-center gap-2">
            <Activity size={12} />
            <span>{sessionId ? `${sessionId.substring(0, 8)}...` : 'No session'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock size={12} />
            <span>
              {lastUpdated ? lastUpdated.toLocaleTimeString() : '--:--:--'}
            </span>
          </div>
        </div>
      </motion.section>
    </header>
  );
}
