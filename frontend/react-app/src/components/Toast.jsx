import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';

const icons = {
  error: AlertCircle,
  success: CheckCircle,
  info: Info,
};

const colors = {
  error: {
    bg: 'bg-cyber-danger/10',
    border: 'border-cyber-danger/30',
    text: 'text-cyber-danger',
    icon: 'text-cyber-danger',
  },
  success: {
    bg: 'bg-cyber-success/10',
    border: 'border-cyber-success/30',
    text: 'text-cyber-success',
    icon: 'text-cyber-success',
  },
  info: {
    bg: 'bg-cyber-accent/10',
    border: 'border-cyber-accent/30',
    text: 'text-cyber-accent',
    icon: 'text-cyber-accent',
  },
};

export default function Toast({ message, type = 'info', onClose, duration = 5000 }) {
  const Icon = icons[type];
  const colorScheme = colors[type];
  
  useEffect(() => {
    if (duration) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 50, x: '-50%' }}
      animate={{ opacity: 1, y: 0, x: '-50%' }}
      exit={{ opacity: 0, y: 50, x: '-50%' }}
      className={`fixed bottom-6 left-1/2 z-50 flex items-center gap-3 px-5 py-4 rounded-xl ${colorScheme.bg} border ${colorScheme.border} shadow-lg backdrop-blur-sm min-w-[300px] max-w-lg`}
    >
      <Icon size={20} className={colorScheme.icon} />
      <span className={`flex-1 text-sm ${colorScheme.text}`}>{message}</span>
      <button
        onClick={onClose}
        className={`p-1 rounded-lg hover:bg-white/10 transition-colors ${colorScheme.text}`}
      >
        <X size={16} />
      </button>
      
      {/* Progress bar */}
      {duration && (
        <motion.div
          initial={{ scaleX: 1 }}
          animate={{ scaleX: 0 }}
          transition={{ duration: duration / 1000, ease: 'linear' }}
          className={`absolute bottom-0 left-0 right-0 h-1 ${colorScheme.bg} origin-left rounded-b-xl`}
          style={{ background: `linear-gradient(90deg, transparent, ${type === 'error' ? '#fb7185' : type === 'success' ? '#22c55e' : '#2dd4bf'})` }}
        />
      )}
    </motion.div>
  );
}
