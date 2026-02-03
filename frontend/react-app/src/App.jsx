import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useStore } from './store/useStore';
import Header from './components/Header';
import TabBar from './components/TabBar';
import SessionControl from './components/SessionControl';
import LiveMonitor from './components/LiveMonitor';
import AgentOverview from './components/AgentOverview';
import AgentManager from './components/AgentManager';
import Toast from './components/Toast';

function App() {
  const {
    activeTab,
    refreshStatus,
    fetchCurrentUser,
    fetchFilterStatus,
    fetchAgents,
    authToken,
    error,
    clearError
  } = useStore();

  // Status polling
  useEffect(() => {
    refreshStatus();
    fetchFilterStatus();
    fetchAgents();
    const interval = setInterval(() => {
      refreshStatus();
      fetchAgents();
    }, 1000);
    return () => clearInterval(interval);
  }, [refreshStatus, fetchFilterStatus, fetchAgents]);

  // Check auth on mount
  useEffect(() => {
    if (authToken) {
      fetchCurrentUser();
    }
  }, [authToken, fetchCurrentUser]);

  // Background grid pattern
  const gridPattern = {
    backgroundImage: `
      radial-gradient(800px 400px at 20% 10%, rgba(45, 212, 191, 0.12), transparent 60%),
      radial-gradient(600px 300px at 80% 5%, rgba(245, 158, 11, 0.12), transparent 60%),
      linear-gradient(rgba(45, 212, 191, 0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(45, 212, 191, 0.02) 1px, transparent 1px)
    `,
    backgroundSize: '100% 100%, 100% 100%, 40px 40px, 40px 40px',
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'control':
        return <SessionControl />;
      case 'monitor':
        return <LiveMonitor />;
      case 'agents':
        return <AgentOverview />;
      case 'manager':
        return <AgentManager />;
      default:
        return <SessionControl />;
    }
  };

  return (
    <div
      className="min-h-screen bg-cyber-dark relative overflow-hidden"
      style={gridPattern}
    >
      {/* Animated background glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <motion.div
          className="absolute w-[800px] h-[400px] rounded-full opacity-30"
          style={{
            background: 'radial-gradient(circle, rgba(45, 212, 191, 0.3) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
          animate={{
            x: ['-20%', '10%', '-20%'],
            y: ['-10%', '20%', '-10%'],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <motion.div
          className="absolute right-0 w-[600px] h-[300px] rounded-full opacity-20"
          style={{
            background: 'radial-gradient(circle, rgba(245, 158, 11, 0.4) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
          animate={{
            x: ['10%', '-10%', '10%'],
            y: ['10%', '-20%', '10%'],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        <Header />
        <TabBar />

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Error Toast */}
      <AnimatePresence>
        {error && (
          <Toast
            message={error}
            type="error"
            onClose={clearError}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
