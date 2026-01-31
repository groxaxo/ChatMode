import { motion } from 'framer-motion';
import { 
  Sliders, 
  Monitor, 
  Users, 
  Settings 
} from 'lucide-react';
import { useStore } from '../store/useStore';

const tabs = [
  { id: 'control', label: 'Session Control', icon: Sliders },
  { id: 'monitor', label: 'Live Monitor', icon: Monitor },
  { id: 'agents', label: 'Agent Overview', icon: Users },
  { id: 'manager', label: 'Agent Manager', icon: Settings },
];

export default function TabBar() {
  const { activeTab, setActiveTab } = useStore();
  
  return (
    <div className="flex flex-wrap gap-2 mb-8">
      {tabs.map(({ id, label, icon: Icon }) => (
        <motion.button
          key={id}
          onClick={() => setActiveTab(id)}
          className={`
            relative flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold
            border transition-all duration-200
            ${activeTab === id 
              ? 'bg-cyber-accent text-cyber-dark border-cyber-accent' 
              : 'glass border-cyber-border text-cyber-muted hover:border-cyber-accent/40 hover:text-cyber-text'
            }
          `}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Icon size={16} />
          <span>{label}</span>
          
          {activeTab === id && (
            <motion.div
              layoutId="activeTab"
              className="absolute inset-0 bg-cyber-accent rounded-xl -z-10"
              initial={false}
              transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
            />
          )}
        </motion.button>
      ))}
    </div>
  );
}
