import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  X, 
  Bot, 
  Save, 
  Loader2,
  Settings,
  Volume2,
  Brain,
  Shield,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useStore } from '../store/useStore';

export default function AgentModal({ agent, onClose }) {
  const { createAgent, updateAgent, updateAgentPermissions, getAgent, isLoading } = useStore();
  const isEditing = Boolean(agent);
  
  // Basic settings
  const [name, setName] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [model, setModel] = useState('');
  const [provider, setProvider] = useState('openai');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [sleepSeconds, setSleepSeconds] = useState('');
  const [enabled, setEnabled] = useState(true);
  
  // Content filter settings
  const [filterEnabled, setFilterEnabled] = useState(false);
  const [blockedWords, setBlockedWords] = useState('');
  const [filterAction, setFilterAction] = useState('block');
  const [filterMessage, setFilterMessage] = useState('');
  
  // Voice settings
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [ttsVoice, setTtsVoice] = useState('alloy');
  const [ttsModel, setTtsModel] = useState('tts-1');
  
  // Memory settings
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [topK, setTopK] = useState(5);
  
  // Expandable sections
  const [expandedSection, setExpandedSection] = useState('basic');
  
  // Load agent data when editing
  useEffect(() => {
    if (agent) {
      setName(agent.name || '');
      setDisplayName(agent.display_name || '');
      setModel(agent.model || '');
      setProvider(agent.provider || 'openai');
      setSystemPrompt(agent.system_prompt || '');
      setTemperature(agent.temperature ?? 0.7);
      setMaxTokens(agent.max_tokens ?? 4096);
      setSleepSeconds(agent.sleep_seconds ?? '');
      setEnabled(agent.enabled !== false);
      
      // Permissions
      if (agent.permissions) {
        setFilterEnabled(agent.permissions.filter_enabled === true);
        setBlockedWords((agent.permissions.blocked_words || []).join(', '));
        setFilterAction(agent.permissions.filter_action || 'block');
        setFilterMessage(agent.permissions.filter_message || '');
      }
      
      // Voice
      if (agent.voice_settings) {
        setTtsEnabled(agent.voice_settings.tts_enabled !== false);
        setTtsVoice(agent.voice_settings.tts_voice || 'alloy');
        setTtsModel(agent.voice_settings.tts_model || 'tts-1');
      }
      
      // Memory
      if (agent.memory_settings) {
        setMemoryEnabled(agent.memory_settings.memory_enabled !== false);
        setTopK(agent.memory_settings.top_k ?? 5);
      }
    }
  }, [agent]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const agentData = {
      name,
      display_name: displayName || null,
      model,
      provider,
      system_prompt: systemPrompt || null,
      temperature: parseFloat(temperature) || 0.7,
      max_tokens: parseInt(maxTokens) || 4096,
      sleep_seconds: sleepSeconds !== '' ? parseFloat(sleepSeconds) : null,
      enabled,
      voice_settings: {
        tts_enabled: ttsEnabled,
        tts_voice: ttsVoice,
        tts_model: ttsModel,
      },
      memory_settings: {
        memory_enabled: memoryEnabled,
        top_k: parseInt(topK) || 5,
      },
    };
    
    let success;
    if (isEditing) {
      success = await updateAgent(agent.id, agentData);
    } else {
      success = await createAgent(agentData);
    }
    
    if (success) {
      // Update permissions separately if editing
      if (isEditing || success) {
        const agentId = isEditing ? agent.id : success.id;
        const permissionsData = {
          filter_enabled: filterEnabled,
          blocked_words: blockedWords.split(',').map(w => w.trim()).filter(w => w),
          filter_action: filterAction,
          filter_message: filterMessage || null,
        };
        await updateAgentPermissions(agentId, permissionsData);
      }
      onClose();
    }
  };
  
  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="glass rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-cyber-border">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyber-accent/10">
              <Bot size={20} className="text-cyber-accent" />
            </div>
            <h3 className="text-lg font-semibold text-cyan-100">
              {isEditing ? 'Edit Agent' : 'Create Agent'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X size={18} />
          </button>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="p-5 overflow-y-auto max-h-[calc(90vh-140px)] space-y-4">
            
            {/* Basic Settings Section */}
            <div className="bg-cyber-darker/50 rounded-xl border border-cyber-border/50 overflow-hidden">
              <button
                type="button"
                onClick={() => toggleSection('basic')}
                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Settings size={18} className="text-cyber-accent" />
                  <span className="font-semibold">Basic Settings</span>
                </div>
                {expandedSection === 'basic' ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
              
              {expandedSection === 'basic' && (
                <div className="p-4 pt-0 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Name *
                      </label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="agent_name"
                        required
                        disabled={isEditing}
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all disabled:opacity-50"
                      />
                    </div>
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Display Name
                      </label>
                      <input
                        type="text"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        placeholder="Friendly Name"
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Model *
                      </label>
                      <input
                        type="text"
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        placeholder="gpt-4o"
                        required
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
                      />
                    </div>
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Provider
                      </label>
                      <select
                        value={provider}
                        onChange={(e) => setProvider(e.target.value)}
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text focus:border-cyber-accent transition-all"
                      >
                        <option value="openai">OpenAI</option>
                        <option value="ollama">Ollama</option>
                        <option value="azure">Azure</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="fireworks">Fireworks</option>
                        <option value="deepseek">DeepSeek</option>
                      </select>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                      System Prompt
                    </label>
                    <textarea
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      placeholder="You are a helpful assistant..."
                      rows={4}
                      className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all resize-none"
                    />
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Temperature
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="2"
                        value={temperature}
                        onChange={(e) => setTemperature(e.target.value)}
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text focus:border-cyber-accent transition-all"
                      />
                    </div>
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Max Tokens
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={maxTokens}
                        onChange={(e) => setMaxTokens(e.target.value)}
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text focus:border-cyber-accent transition-all"
                      />
                    </div>
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Sleep (s)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={sleepSeconds}
                        onChange={(e) => setSleepSeconds(e.target.value)}
                        placeholder="Global"
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
                      />
                    </div>
                  </div>
                  
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enabled}
                      onChange={(e) => setEnabled(e.target.checked)}
                      className="w-5 h-5 rounded border-cyber-border bg-cyber-darker checked:bg-cyber-accent"
                    />
                    <span className="text-sm text-cyber-text">Enabled</span>
                  </label>
                </div>
              )}
            </div>
            
            {/* Voice Settings Section */}
            <div className="bg-cyber-darker/50 rounded-xl border border-cyber-border/50 overflow-hidden">
              <button
                type="button"
                onClick={() => toggleSection('voice')}
                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Volume2 size={18} className="text-cyber-accent" />
                  <span className="font-semibold">Voice Settings</span>
                </div>
                {expandedSection === 'voice' ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
              
              {expandedSection === 'voice' && (
                <div className="p-4 pt-0 space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={ttsEnabled}
                      onChange={(e) => setTtsEnabled(e.target.checked)}
                      className="w-5 h-5 rounded border-cyber-border bg-cyber-darker checked:bg-cyber-accent"
                    />
                    <span className="text-sm text-cyber-text">Enable TTS</span>
                  </label>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Voice
                      </label>
                      <select
                        value={ttsVoice}
                        onChange={(e) => setTtsVoice(e.target.value)}
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text focus:border-cyber-accent transition-all"
                      >
                        <option value="alloy">Alloy</option>
                        <option value="echo">Echo</option>
                        <option value="fable">Fable</option>
                        <option value="onyx">Onyx</option>
                        <option value="nova">Nova</option>
                        <option value="shimmer">Shimmer</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        TTS Model
                      </label>
                      <select
                        value={ttsModel}
                        onChange={(e) => setTtsModel(e.target.value)}
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text focus:border-cyber-accent transition-all"
                      >
                        <option value="tts-1">TTS-1 (Fast)</option>
                        <option value="tts-1-hd">TTS-1-HD (Quality)</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Memory Settings Section */}
            <div className="bg-cyber-darker/50 rounded-xl border border-cyber-border/50 overflow-hidden">
              <button
                type="button"
                onClick={() => toggleSection('memory')}
                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Brain size={18} className="text-cyber-accent" />
                  <span className="font-semibold">Memory Settings</span>
                </div>
                {expandedSection === 'memory' ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
              
              {expandedSection === 'memory' && (
                <div className="p-4 pt-0 space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={memoryEnabled}
                      onChange={(e) => setMemoryEnabled(e.target.checked)}
                      className="w-5 h-5 rounded border-cyber-border bg-cyber-darker checked:bg-cyber-accent"
                    />
                    <span className="text-sm text-cyber-text">Enable Memory</span>
                  </label>
                  
                  <div>
                    <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                      Top K Results
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={topK}
                      onChange={(e) => setTopK(e.target.value)}
                      className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text focus:border-cyber-accent transition-all"
                    />
                  </div>
                </div>
              )}
            </div>
            
            {/* Content Filter Section */}
            <div className="bg-cyber-darker/50 rounded-xl border border-cyber-border/50 overflow-hidden">
              <button
                type="button"
                onClick={() => toggleSection('filter')}
                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Shield size={18} className="text-cyber-accent" />
                  <span className="font-semibold">Content Filter</span>
                </div>
                {expandedSection === 'filter' ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
              
              {expandedSection === 'filter' && (
                <div className="p-4 pt-0 space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filterEnabled}
                      onChange={(e) => setFilterEnabled(e.target.checked)}
                      className="w-5 h-5 rounded border-cyber-border bg-cyber-darker checked:bg-cyber-accent"
                    />
                    <span className="text-sm text-cyber-text">Enable Content Filter</span>
                  </label>
                  
                  <div>
                    <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                      Blocked Words (comma-separated)
                    </label>
                    <textarea
                      value={blockedWords}
                      onChange={(e) => setBlockedWords(e.target.value)}
                      placeholder="word1, word2, phrase"
                      rows={2}
                      className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all resize-none"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                        Filter Action
                      </label>
                      <select
                        value={filterAction}
                        onChange={(e) => setFilterAction(e.target.value)}
                        className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text focus:border-cyber-accent transition-all"
                      >
                        <option value="block">Block</option>
                        <option value="censor">Censor</option>
                        <option value="warn">Warn</option>
                      </select>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
                      Filter Message
                    </label>
                    <input
                      type="text"
                      value={filterMessage}
                      onChange={(e) => setFilterMessage(e.target.value)}
                      placeholder="Message shown when content is blocked"
                      className="w-full bg-cyber-darker border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-5 border-t border-cyber-border">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 text-sm font-medium transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-cyber flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyber-accent text-cyber-dark font-semibold text-sm hover:shadow-lg hover:shadow-cyber-accent/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={16} />
                  {isEditing ? 'Update Agent' : 'Create Agent'}
                </>
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}
