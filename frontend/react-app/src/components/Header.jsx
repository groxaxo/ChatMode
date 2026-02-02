import { motion } from 'framer-motion';
import { Activity, Wifi, WifiOff, Clock } from 'lucide-react';
import { useStore } from '../store/useStore';

// ASCII Art for ChatMode logo
const asciiArt = `
 ██████╗██╗  ██╗ █████╗ ████████╗
██╔════╝██║  ██║██╔══██╗╚══██╔══╝
██║     ███████║███████║   ██║   
██║     ██╔══██║██╔══██║   ██║   
╚██████╗██║  ██║██║  ██║   ██║   
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
███╗   ███╗ ██████╗ ██████╗ ███████╗
████╗ ████║██╔═══██╗██╔══██╗██╔════╝
██╔████╔██║██║   ██║██║  ██║█████╗  
██║╚██╔╝██║██║   ██║██║  ██║██╔══╝  
██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗
╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝`;

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
        
        <div className="relative z-10 flex items-center gap-6">
          {/* ASCII Art Logo */}
          <motion.pre 
            className="hidden md:block text-[0.35rem] leading-tight text-cyber-accent font-mono whitespace-pre"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            style={{
              textShadow: '0 0 20px rgba(45, 212, 191, 0.5)',
            }}
          >
            {asciiArt}
          </motion.pre>
          
          {/* Text Content */}
          <div className="flex-1">
            <div className="flex items-center gap-2 text-[0.65rem] uppercase tracking-[0.25em] text-cyber-muted mb-3 font-medium">
              <span className="text-cyber-accent animate-pulse">◆</span>
              AI Agent Platform
            </div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 bg-gradient-to-r from-cyber-text via-cyber-accent to-cyber-accent2 bg-clip-text text-transparent bg-[length:200%_200%] animate-gradient">
              ChatMode
            </h1>
            <p className="text-cyber-muted text-sm leading-relaxed max-w-xl mb-4">
              Multi-agent orchestration system with semantic memory, voice synthesis, and real-time conversation control.
            </p>
            
            {/* Feature Badges */}
            <div className="flex flex-wrap gap-2">
              <span className="text-[0.6rem] uppercase tracking-wider px-2.5 py-1 rounded-full bg-cyber-accent/10 border border-cyber-accent/30 text-cyber-accent">
                🤖 Multi-Agent
              </span>
              <span className="text-[0.6rem] uppercase tracking-wider px-2.5 py-1 rounded-full bg-cyber-accent/10 border border-cyber-accent/30 text-cyber-accent">
                🧠 Semantic Memory
              </span>
              <span className="text-[0.6rem] uppercase tracking-wider px-2.5 py-1 rounded-full bg-cyber-accent2/10 border border-cyber-accent2/30 text-cyber-accent2">
                🎙️ Voice TTS
              </span>
              <span className="text-[0.6rem] uppercase tracking-wider px-2.5 py-1 rounded-full bg-cyber-accent/10 border border-cyber-accent/30 text-cyber-accent">
                ⚡ Real-time
              </span>
            </div>
          </div>
        </div>
        
        {/* Corner decoration */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyber-accent/5 to-transparent rounded-bl-full" />
      </motion.section>

      {/* Status Card */}
      <motion.section 
        className="glass rounded-2xl p-5 min-w-[300px] flex flex-col justify-between relative overflow-hidden"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        {/* Animated top border */}
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-cyber-accent via-cyber-accent2 to-cyber-accent bg-[length:200%_100%] animate-gradient" />
        
        {/* Status Title */}
        <div className="text-[0.6rem] uppercase tracking-[0.2em] text-cyber-muted mb-3">
          System Status
        </div>
        
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
        <div className="mb-3 p-2.5 bg-cyber-dark/50 rounded-lg border border-white/5">
          <div className="text-[0.6rem] uppercase tracking-wider text-cyber-muted mb-1 flex items-center gap-1.5">
            <span>📋</span> Topic
          </div>
          <div className="text-sm font-mono text-cyber-text truncate">
            {topic || 'Not set'}
          </div>
        </div>

        {/* Session ID & Last Updated */}
        <div className="flex items-center justify-between text-xs text-cyber-muted font-mono p-2.5 bg-cyber-dark/50 rounded-lg border border-white/5">
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
