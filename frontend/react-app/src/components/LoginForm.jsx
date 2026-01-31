import { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, User, AlertCircle, Loader2 } from 'lucide-react';
import { useStore } from '../store/useStore';

export default function LoginForm() {
  const { login, isLoading, error } = useStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    
    if (!username.trim() || !password) {
      setLocalError('Please enter both username and password');
      return;
    }
    
    const success = await login(username, password);
    if (!success) {
      setLocalError('Login failed. Please check your credentials.');
    }
  };
  
  return (
    <motion.div 
      className="max-w-md mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="glass rounded-2xl p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex p-4 rounded-2xl bg-cyber-accent/10 border border-cyber-accent/30 mb-4">
            <Lock size={32} className="text-cyber-accent" />
          </div>
          <h2 className="text-2xl font-bold text-cyan-100">Login Required</h2>
          <p className="text-cyber-muted text-sm mt-2">
            Sign in to access Agent Manager
          </p>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
              Username
            </label>
            <div className="relative">
              <User size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-cyber-muted" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full bg-cyber-darker border border-cyber-border rounded-xl pl-12 pr-4 py-3.5 text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
                autoComplete="username"
              />
            </div>
          </div>
          
          <div>
            <label className="text-[0.65rem] uppercase tracking-widest text-cyber-muted block mb-2">
              Password
            </label>
            <div className="relative">
              <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-cyber-muted" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full bg-cyber-darker border border-cyber-border rounded-xl pl-12 pr-4 py-3.5 text-cyber-text placeholder:text-cyber-muted/50 focus:border-cyber-accent transition-all"
                autoComplete="current-password"
              />
            </div>
          </div>
          
          {/* Error Message */}
          {(localError || error) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 p-3 rounded-lg bg-cyber-danger/10 border border-cyber-danger/30 text-cyber-danger text-sm"
            >
              <AlertCircle size={16} />
              <span>{localError || error}</span>
            </motion.div>
          )}
          
          <button
            type="submit"
            disabled={isLoading}
            className="btn-cyber w-full flex items-center justify-center gap-2 px-4 py-4 rounded-xl bg-cyber-accent text-cyber-dark font-semibold text-sm hover:shadow-lg hover:shadow-cyber-accent/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <Lock size={18} />
                Sign In
              </>
            )}
          </button>
        </form>
        
        {/* Help Text */}
        <p className="text-center text-cyber-muted text-xs mt-6">
          Contact your administrator if you need access
        </p>
      </div>
    </motion.div>
  );
}
