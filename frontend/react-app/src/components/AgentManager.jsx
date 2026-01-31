import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  RefreshCw, 
  Zap, 
  Bot, 
  Edit, 
  Trash2, 
  Code,
  LogOut,
  Lock,
  User,
  Settings,
  Volume2,
  Brain,
  Shield,
  X,
  Check,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useStore } from '../store/useStore';
import LoginForm from './LoginForm';
import AgentModal from './AgentModal';

export default function AgentManager() {
  const { 
    isAuthenticated, 
    currentUser,
    agents,
    agentsLoading,
    fetchAgents,
    deleteAgent,
    syncState,
    logout,
    isLoading
  } = useStore();
  
  const [showModal, setShowModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [jsonContent, setJsonContent] = useState(null);
  const [expandedAgent, setExpandedAgent] = useState(null);
  
  useEffect(() => {
    if (isAuthenticated) {
      fetchAgents();
    }
  }, [isAuthenticated, fetchAgents]);
  
  const handleEdit = (agent) => {
    setEditingAgent(agent);
    setShowModal(true);
  };
  
  const handleCreate = () => {
    setEditingAgent(null);
    setShowModal(true);
  };
  
  const handleViewJson = (agent) => {
    setJsonContent(agent);
    setShowJsonModal(true);
  };
  
  const handleDelete = async (agentId) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    await deleteAgent(agentId);
  };
  
  if (!isAuthenticated) {
    return <LoginForm />;
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div 
        className="glass rounded-2xl p-5 card-cyber"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-cyber-accent/10 border border-cyber-accent/30">
              <Settings size={24} className="text-cyber-accent" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-cyan-100">Agent Manager</h2>
              <div className="flex items-center gap-2 mt-1">
                <User size={12} className="text-cyber-muted" />
                <span className="text-sm text-cyber-accent">{currentUser?.username}</span>
                <span className="text-xs text-cyber-muted px-2 py-0.5 bg-cyber-panel rounded-full">
                  {currentUser?.role}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleCreate}
              className="btn-cyber flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyber-accent text-cyber-dark font-semibold text-sm hover:shadow-lg hover:shadow-cyber-accent/20 transition-all"
            >
              <Plus size={16} />
              Create Agent
            </button>
            <button
              onClick={fetchAgents}
              disabled={agentsLoading}
              className="btn-cyber flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 text-sm font-medium transition-all disabled:opacity-50"
            >
              <RefreshCw size={16} className={agentsLoading ? 'animate-spin' : ''} />
              Refresh
            </button>
            <button
              onClick={syncState}
              disabled={isLoading}
              className="btn-cyber flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-cyber-text hover:border-cyber-accent/50 text-sm font-medium transition-all disabled:opacity-50"
            >
              <Zap size={16} />
              Sync
            </button>
            <button
              onClick={logout}
              className="btn-cyber flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyber-danger/10 border border-cyber-danger/30 text-cyber-danger hover:bg-cyber-danger/20 text-sm font-medium transition-all"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </div>
      </motion.div>

      {/* Agent List */}
      <motion.div 
        className="glass rounded-2xl p-5"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <h3 className="text-lg font-semibold mb-4 text-cyan-100 flex items-center gap-2">
          <Bot size={18} className="text-cyber-accent" />
          Agents ({agents.length})
        </h3>
        
        {agentsLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw size={32} className="text-cyber-accent animate-spin" />
          </div>
        ) : agents.length === 0 ? (
          <div className="text-center py-12">
            <Bot size={48} className="mx-auto mb-4 text-cyber-muted opacity-30" />
            <p className="text-cyber-muted">No agents found. Create one to get started!</p>
          </div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {agents.map((agent, index) => (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: index * 0.03 }}
                  className="bg-cyber-darker/80 rounded-xl border border-cyber-border/50 overflow-hidden hover:border-cyber-accent/30 transition-colors"
                >
                  {/* Main Row */}
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`p-2.5 rounded-xl ${agent.enabled ? 'bg-cyber-success/10' : 'bg-cyber-danger/10'}`}>
                          <Bot size={20} className={agent.enabled ? 'text-cyber-success' : 'text-cyber-danger'} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-cyber-text">
                              {agent.display_name || agent.name}
                            </h4>
                            <span className={`text-[0.6rem] uppercase tracking-wider px-2 py-0.5 rounded-full ${
                              agent.enabled 
                                ? 'bg-cyber-success/10 text-cyber-success' 
                                : 'bg-cyber-danger/10 text-cyber-danger'
                            }`}>
                              {agent.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                          </div>
                          <p className="text-xs text-cyber-muted font-mono mt-1">{agent.name}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {/* Quick Stats */}
                        <div className="hidden md:flex items-center gap-4 mr-4 text-xs text-cyber-muted">
                          <span className="flex items-center gap-1">
                            <Settings size={12} />
                            {agent.provider || 'openai'}
                          </span>
                          <span className="flex items-center gap-1">
                            <Code size={12} />
                            {agent.model}
                          </span>
                        </div>
                        
                        {/* Actions */}
                        <button
                          onClick={() => setExpandedAgent(expandedAgent === agent.id ? null : agent.id)}
                          className="btn-cyber p-2 rounded-lg bg-white/5 border border-white/10 text-cyber-muted hover:text-cyber-text hover:border-cyber-accent/50 transition-all"
                        >
                          {expandedAgent === agent.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </button>
                        <button
                          onClick={() => handleEdit(agent)}
                          className="btn-cyber p-2 rounded-lg bg-white/5 border border-white/10 text-cyber-muted hover:text-cyber-accent hover:border-cyber-accent/50 transition-all"
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          onClick={() => handleViewJson(agent)}
                          className="btn-cyber p-2 rounded-lg bg-white/5 border border-white/10 text-cyber-muted hover:text-cyber-accent hover:border-cyber-accent/50 transition-all"
                        >
                          <Code size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(agent.id)}
                          className="btn-cyber p-2 rounded-lg bg-cyber-danger/10 border border-cyber-danger/30 text-cyber-danger hover:bg-cyber-danger/20 transition-all"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Expanded Details */}
                  <AnimatePresence>
                    {expandedAgent === agent.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="border-t border-cyber-border/30"
                      >
                        <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                          {/* Model Settings */}
                          <div className="bg-cyber-panel/50 rounded-lg p-4">
                            <h5 className="text-xs uppercase tracking-wider text-cyber-muted mb-3 flex items-center gap-2">
                              <Settings size={12} />
                              Model Settings
                            </h5>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-cyber-muted">Provider</span>
                                <span className="text-cyber-text font-mono">{agent.provider || 'openai'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-cyber-muted">Model</span>
                                <span className="text-cyber-text font-mono">{agent.model}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-cyber-muted">Temperature</span>
                                <span className="text-cyber-text font-mono">{agent.temperature}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-cyber-muted">Max Tokens</span>
                                <span className="text-cyber-text font-mono">{agent.max_tokens}</span>
                              </div>
                              {agent.sleep_seconds !== null && (
                                <div className="flex justify-between">
                                  <span className="text-cyber-muted">Sleep</span>
                                  <span className="text-cyber-text font-mono">{agent.sleep_seconds}s</span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Voice Settings */}
                          <div className="bg-cyber-panel/50 rounded-lg p-4">
                            <h5 className="text-xs uppercase tracking-wider text-cyber-muted mb-3 flex items-center gap-2">
                              <Volume2 size={12} />
                              Voice Settings
                            </h5>
                            {agent.voice_settings ? (
                              <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-cyber-muted">TTS</span>
                                  <span className={agent.voice_settings.tts_enabled ? 'text-cyber-success' : 'text-cyber-danger'}>
                                    {agent.voice_settings.tts_enabled ? 'Enabled' : 'Disabled'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-cyber-muted">Voice</span>
                                  <span className="text-cyber-text font-mono">{agent.voice_settings.tts_voice}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-cyber-muted">Model</span>
                                  <span className="text-cyber-text font-mono">{agent.voice_settings.tts_model}</span>
                                </div>
                              </div>
                            ) : (
                              <p className="text-cyber-muted text-sm">No voice settings</p>
                            )}
                          </div>
                          
                          {/* Memory & Permissions */}
                          <div className="bg-cyber-panel/50 rounded-lg p-4">
                            <h5 className="text-xs uppercase tracking-wider text-cyber-muted mb-3 flex items-center gap-2">
                              <Shield size={12} />
                              Memory & Filter
                            </h5>
                            <div className="space-y-2 text-sm">
                              {agent.memory_settings && (
                                <>
                                  <div className="flex justify-between">
                                    <span className="text-cyber-muted">Memory</span>
                                    <span className={agent.memory_settings.memory_enabled ? 'text-cyber-success' : 'text-cyber-danger'}>
                                      {agent.memory_settings.memory_enabled ? 'Enabled' : 'Disabled'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-cyber-muted">Top K</span>
                                    <span className="text-cyber-text font-mono">{agent.memory_settings.top_k}</span>
                                  </div>
                                </>
                              )}
                              {agent.permissions && (
                                <div className="flex justify-between">
                                  <span className="text-cyber-muted">Content Filter</span>
                                  <span className={agent.permissions.filter_enabled ? 'text-cyber-success' : 'text-cyber-danger'}>
                                    {agent.permissions.filter_enabled ? 'Enabled' : 'Disabled'}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        {/* System Prompt Preview */}
                        {agent.system_prompt && (
                          <div className="px-4 pb-4">
                            <div className="bg-cyber-panel/50 rounded-lg p-4">
                              <h5 className="text-xs uppercase tracking-wider text-cyber-muted mb-2 flex items-center gap-2">
                                <Brain size={12} />
                                System Prompt
                              </h5>
                              <p className="text-sm text-cyber-text/80 line-clamp-3 font-mono">
                                {agent.system_prompt}
                              </p>
                            </div>
                          </div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </motion.div>

      {/* Agent Modal */}
      <AnimatePresence>
        {showModal && (
          <AgentModal 
            agent={editingAgent} 
            onClose={() => {
              setShowModal(false);
              setEditingAgent(null);
            }} 
          />
        )}
      </AnimatePresence>

      {/* JSON Modal */}
      <AnimatePresence>
        {showJsonModal && jsonContent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => setShowJsonModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-5 border-b border-cyber-border">
                <h3 className="text-lg font-semibold text-cyan-100">Agent JSON</h3>
                <button
                  onClick={() => setShowJsonModal(false)}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="p-5 overflow-auto max-h-[60vh]">
                <pre className="bg-cyber-darker rounded-xl p-4 text-sm font-mono text-cyber-text overflow-x-auto">
                  {JSON.stringify(jsonContent, null, 2)}
                </pre>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
