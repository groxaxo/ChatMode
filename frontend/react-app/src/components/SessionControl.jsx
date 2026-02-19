import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Play, 
  Square, 
  RotateCcw, 
  Trash2, 
  Send, 
  MessageSquare,
  Info,
  Filter,
  Volume2,
  VolumeX
} from 'lucide-react';
import { useStore } from '../store/useStore';
import MessageFeed from './MessageFeed';

export default function SessionControl() {
  const { 
    isRunning,
    topic,
    isLoading,
    autoScroll,
    setAutoScroll,
    filterEnabled,
    setFilterEnabled,
    reloadFilter,
    startSession,
    stopSession,
    resumeSession,
    clearMemory,
    sendMessage,
    interruptSession,
    switchContext,
    messageRate,
    setMessageRate,
  } = useStore();
  
  const [topicInput, setTopicInput] = useState('');
  const [contextTopic, setContextTopic] = useState('');
  const [sender, setSender] = useState('Admin');
  const [content, setContent] = useState('');
  
  const handleStart = async () => {
    if (!topicInput.trim()) return;
    await startSession(topicInput.trim());
    setTopicInput('');
  };
  
  const handleSend = async () => {
    if (!content.trim()) return;
    await sendMessage(content.trim(), sender);
    setContent('');
  };

  const handleContextSwitch = async () => {
    if (!contextTopic.trim()) return;
    const switched = await switchContext(contextTopic.trim());
    if (switched) setContextTopic('');
  };

  const handleRateChange = async (event) => {
    await setMessageRate(parseFloat(event.target.value));
  };
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6">
      {/* Left Column - Controls */}
      <div className="space-y-5">
        {/* Session Control Card */}
        <motion.div 
          className="glass rounded-2xl p-5 card-cyber"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <h2 className="text-lg font-semibold mb-4 text-cyan-100 flex items-center gap-2">
            <Play size={18} className="text-cyber-accent" />
            Session Control
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                Topic
              </label>
              <input
                type="text"
                value={topicInput}
                onChange={(e) => setTopicInput(e.target.value)}
                placeholder="Enter a conversation topic"
                className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-3 text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
                onKeyDown={(e) => e.key === 'Enter' && handleStart()}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={handleStart}
                disabled={isLoading || !topicInput.trim()}
                className="btn-cyber flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-cyber-accent/20 border border-cyber-accent/50 text-cyber-accent hover:bg-cyber-accent hover:text-cyber-dark font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <Play size={16} />
                Start
              </button>
              <button
                onClick={resumeSession}
                disabled={isLoading || isRunning}
                className="btn-cyber flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <RotateCcw size={16} />
                Resume
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={stopSession}
                disabled={isLoading || !isRunning}
                className="btn-cyber flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <Square size={16} />
                Stop
              </button>
              <button
                onClick={interruptSession}
                disabled={isLoading || !isRunning}
                className="btn-cyber flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-cyber-warning/10 border border-cyber-warning/40 text-cyber-warning hover:bg-cyber-warning/20 font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <Square size={16} />
                Interrupt
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={clearMemory}
                disabled={isLoading}
                className="btn-cyber flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-cyber-danger/10 border border-cyber-danger/30 text-cyber-danger hover:bg-cyber-danger/20 font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <Trash2 size={16} />
                Clear
              </button>
              <div className="flex items-center justify-center rounded-xl border border-cyber-border bg-cyber-darker/40 text-cyber-muted text-xs">
                Live controls
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block">
                Context Switch
              </label>
              <div className="grid grid-cols-[1fr_auto] gap-2">
                <input
                  type="text"
                  value={contextTopic}
                  onChange={(e) => setContextTopic(e.target.value)}
                  placeholder="Switch conversation topic"
                  className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-3 py-2 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
                />
                <button
                  onClick={handleContextSwitch}
                  disabled={isLoading || !isRunning || !contextTopic.trim()}
                  className="btn-cyber px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  Apply
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block">
                Message Rate ({messageRate.toFixed(1)}x)
              </label>
              <input
                type="range"
                min="0.1"
                max="5"
                step="0.1"
                value={messageRate}
                onChange={handleRateChange}
                className="w-full accent-cyber-accent"
              />
            </div>
          </div>
          
          <p className="text-xs text-cyber-muted mt-4 leading-relaxed">
            <Info size={12} className="inline mr-1" />
            Start creates a fresh session. Resume continues without clearing memory.
          </p>
        </motion.div>

        {/* Message Inject Card */}
        <motion.div 
          className="glass rounded-2xl p-5 card-cyber"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h2 className="text-lg font-semibold mb-4 text-cyan-100 flex items-center gap-2">
            <MessageSquare size={18} className="text-cyber-accent" />
            Inject Message
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                Sender
              </label>
              <input
                type="text"
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-3 text-cyber-text focus:border-cyber-accent transition-all"
              />
            </div>
            
            <div>
              <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                Message
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Type a message to inject..."
                rows={4}
                className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-3 text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all resize-none"
                onKeyDown={(e) => e.key === 'Enter' && e.metaKey && handleSend()}
              />
            </div>
            
            <button
              onClick={handleSend}
              disabled={!content.trim()}
              className="btn-cyber w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-cyber-accent text-cyber-dark font-semibold text-sm hover:shadow-lg hover:shadow-cyber-accent/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <Send size={16} />
              Send Message
            </button>
          </div>
        </motion.div>

        {/* Settings Card */}
        <motion.div 
          className="glass rounded-2xl p-5 card-cyber"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-lg font-semibold mb-4 text-cyan-100 flex items-center gap-2">
            <Filter size={18} className="text-cyber-accent" />
            Settings
          </h2>
          
          <div className="space-y-4">
            {/* Auto Scroll Toggle */}
            <label className="flex items-center justify-between cursor-pointer group">
              <div className="flex items-center gap-3">
                <Volume2 size={16} className="text-cyber-muted group-hover:text-cyber-accent transition-colors" />
                <span className="text-sm text-cyber-text">Auto-scroll messages</span>
              </div>
              <div 
                className={`w-11 h-6 rounded-full p-1 transition-colors ${autoScroll ? 'bg-cyber-accent' : 'bg-cyber-border'}`}
                onClick={() => setAutoScroll(!autoScroll)}
              >
                <motion.div 
                  className="w-4 h-4 bg-white rounded-full shadow-md"
                  animate={{ x: autoScroll ? 20 : 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              </div>
            </label>
            
            {/* Content Filter Toggle */}
            <label className="flex items-center justify-between cursor-pointer group">
              <div className="flex items-center gap-3">
                <Filter size={16} className="text-cyber-muted group-hover:text-cyber-accent transition-colors" />
                <span className="text-sm text-cyber-text">Content filter</span>
              </div>
              <div 
                className={`w-11 h-6 rounded-full p-1 transition-colors ${filterEnabled ? 'bg-cyber-success' : 'bg-cyber-border'}`}
                onClick={() => setFilterEnabled(!filterEnabled)}
              >
                <motion.div 
                  className="w-4 h-4 bg-white rounded-full shadow-md"
                  animate={{ x: filterEnabled ? 20 : 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              </div>
            </label>
            
            <p className={`text-xs ${filterEnabled ? 'text-cyber-success' : 'text-cyber-danger'}`}>
              Filter is {filterEnabled ? 'active' : 'disabled'}
            </p>

            <button
              onClick={reloadFilter}
              className="btn-cyber w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-cyber-darker border border-cyber-border text-cyber-text text-xs hover:border-cyber-accent transition-all"
            >
              <RotateCcw size={14} />
              Reload filter settings
            </button>
          </div>
        </motion.div>
      </div>

      {/* Right Column - Message Feed */}
      <motion.div 
        className="glass rounded-2xl p-5 min-h-[600px] flex flex-col"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <h2 className="text-lg font-semibold mb-4 text-cyan-100 flex items-center gap-2">
          <MessageSquare size={18} className="text-cyber-accent" />
          Recent Messages
        </h2>
        
        <MessageFeed />
      </motion.div>
    </div>
  );
}
