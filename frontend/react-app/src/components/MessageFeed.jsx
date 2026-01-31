import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Volume2, User, Bot, AlertTriangle } from 'lucide-react';
import { useStore } from '../store/useStore';

export default function MessageFeed({ compact = false }) {
  const { messages, autoScroll } = useStore();
  const feedRef = useRef(null);
  
  // Auto scroll to bottom
  useEffect(() => {
    if (autoScroll && feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [messages, autoScroll]);
  
  const getSenderColor = (sender) => {
    if (sender === 'System') return 'text-cyber-warning';
    if (sender === 'Admin') return 'text-cyber-accent2';
    return 'text-cyber-accent';
  };
  
  const getSenderIcon = (sender) => {
    if (sender === 'System') return AlertTriangle;
    if (sender === 'Admin') return User;
    return Bot;
  };
  
  if (!messages || messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-cyber-muted">
          <Bot size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-sm">No messages yet</p>
          <p className="text-xs mt-1">Start a session to begin</p>
        </div>
      </div>
    );
  }
  
  return (
    <div 
      ref={feedRef}
      className={`flex-1 overflow-y-auto space-y-3 pr-2 ${compact ? 'max-h-[400px]' : ''}`}
    >
      <AnimatePresence initial={false}>
        {messages.map((msg, index) => {
          const Icon = getSenderIcon(msg.sender);
          const audioUrl = msg.audio_url || msg.audio;
          
          return (
            <motion.div
              key={`${msg.sender}-${index}-${msg.content?.substring(0, 20)}`}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="bg-cyber-darker/80 rounded-xl p-4 border border-cyber-border/50 hover:border-cyber-accent/30 transition-colors message-animate"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={`p-1.5 rounded-lg bg-cyber-panel ${getSenderColor(msg.sender)}`}>
                    <Icon size={14} />
                  </div>
                  <span className={`font-semibold text-sm ${getSenderColor(msg.sender)}`}>
                    {msg.sender || 'Agent'}
                  </span>
                </div>
                
                {msg.timestamp && (
                  <span className="text-[0.65rem] text-cyber-muted font-mono">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                )}
              </div>
              
              {/* Content */}
              <div className="text-sm text-cyber-text leading-relaxed whitespace-pre-wrap pl-8">
                {msg.content || ''}
              </div>
              
              {/* Audio Player */}
              {audioUrl && (
                <div className="mt-3 pl-8">
                  <div className="flex items-center gap-3 bg-cyber-panel rounded-lg p-3">
                    <Volume2 size={16} className="text-cyber-accent" />
                    <audio 
                      controls 
                      src={audioUrl}
                      className="flex-1 h-8"
                      style={{
                        filter: 'hue-rotate(150deg) saturate(1.5)',
                      }}
                    />
                    {msg.audio_cached && (
                      <span className="text-[0.6rem] uppercase tracking-wider text-cyber-muted bg-cyber-darker px-2 py-1 rounded">
                        Cached
                      </span>
                    )}
                  </div>
                </div>
              )}
              
              {/* Audio Error */}
              {msg.audio_error && (
                <div className="mt-3 pl-8 text-xs text-cyber-danger font-mono">
                  TTS Error: {msg.audio_error}
                </div>
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
