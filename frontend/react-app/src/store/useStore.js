import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// API helper with auth token
const apiCall = async (endpoint, options = {}) => {
  const token = useStore.getState().authToken;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(endpoint, { ...options, headers });
  
  if (response.status === 401) {
    useStore.getState().logout();
    throw new Error('Session expired');
  }
  
  return response;
};

// Form data helper
const postForm = async (url, data = {}) => {
  const body = new URLSearchParams(data);
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res;
};

export const useStore = create(
  persist(
    (set, get) => ({
      // Auth State
      authToken: null,
      currentUser: null,
      isAuthenticated: false,
      
      // Session State
      isRunning: false,
      topic: '',
      sessionId: null,
      messages: [],
      agentStates: {},
      
      // UI State
      activeTab: 'control',
      autoScroll: true,
      isLoading: false,
      error: null,
      
      // Connection State
      connectionStatus: 'connected',
      lastUpdated: null,
      
      // Agent Management
      agents: [],
      selectedAgent: null,
      agentsLoading: false,
      
      // Content Filter
      filterEnabled: false,
      filterStatus: null,
      
      // Actions
      setActiveTab: (tab) => set({ activeTab: tab }),
      setAutoScroll: (enabled) => set({ autoScroll: enabled }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),
      
      // Filter Actions
      fetchFilterStatus: async () => {
        try {
          const res = await fetch('/api/v1/filter/status');
          if (res.ok) {
            const data = await res.json();
            set({ filterEnabled: data.enabled, filterStatus: data });
          }
        } catch (error) {
          console.error('Failed to fetch filter status:', error);
        }
      },
      
      setFilterEnabled: async (enabled) => {
        try {
          const res = await fetch('/api/v1/filter/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled }),
          });
          if (res.ok) {
            set({ filterEnabled: enabled });
          }
        } catch (error) {
          console.error('Failed to toggle filter:', error);
        }
      },
      
      reloadFilter: async () => {
        try {
          const res = await fetch('/api/v1/filter/reload', { method: 'POST' });
          if (res.ok) {
            await get().fetchFilterStatus();
          }
        } catch (error) {
          console.error('Failed to reload filter:', error);
        }
      },
      
      // Auth Actions
      login: async (username, password) => {
        set({ isLoading: true, error: null });
        try {
          const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
          });
          
          if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail?.message || 'Login failed');
          }
          
          const data = await res.json();
          set({ 
            authToken: data.access_token, 
            isAuthenticated: true,
            isLoading: false 
          });
          
          // Fetch user info
          await get().fetchCurrentUser();
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      logout: async () => {
        const token = get().authToken;
        if (token) {
          try {
            await fetch('/api/v1/auth/logout', {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
            });
          } catch (e) {
            // Ignore logout errors
          }
        }
        set({ 
          authToken: null, 
          currentUser: null, 
          isAuthenticated: false 
        });
      },
      
      fetchCurrentUser: async () => {
        try {
          const res = await apiCall('/api/v1/auth/me');
          if (res.ok) {
            const user = await res.json();
            set({ currentUser: user });
          }
        } catch (error) {
          console.error('Failed to fetch user:', error);
        }
      },
      
      // Session Actions
      refreshStatus: async () => {
        try {
          const res = await fetch('/status');
          if (!res.ok) throw new Error('Status unavailable');
          const data = await res.json();
          
          set({
            isRunning: Boolean(data.running),
            topic: data.topic || '',
            sessionId: data.session_id,
            messages: data.last_messages || [],
            agentStates: data.agent_states || {},
            connectionStatus: 'connected',
            lastUpdated: new Date(),
          });
        } catch (error) {
          set({ connectionStatus: 'disconnected' });
          console.error('Status refresh failed:', error);
        }
      },
      
      startSession: async (topic) => {
        set({ isLoading: true, error: null });
        try {
          await postForm('/start', { topic });
          await get().refreshStatus();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      stopSession: async () => {
        set({ isLoading: true, error: null });
        try {
          await postForm('/stop');
          await get().refreshStatus();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      resumeSession: async () => {
        set({ isLoading: true, error: null });
        try {
          await postForm('/resume');
          await get().refreshStatus();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      clearMemory: async () => {
        set({ isLoading: true, error: null });
        try {
          await postForm('/memory/clear');
          await get().refreshStatus();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      sendMessage: async (content, sender = 'Admin') => {
        try {
          await postForm('/messages', { content, sender });
          await get().refreshStatus();
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      // Agent Control Actions
      pauseAgent: async (agentName, reason = null) => {
        try {
          const formData = reason ? { reason } : {};
          await postForm(`/agents/${agentName}/pause`, formData);
          await get().refreshStatus();
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      resumeAgent: async (agentName) => {
        try {
          await postForm(`/agents/${agentName}/resume`);
          await get().refreshStatus();
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      stopAgent: async (agentName, reason = null) => {
        try {
          const formData = reason ? { reason } : {};
          await postForm(`/agents/${agentName}/stop`, formData);
          await get().refreshStatus();
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      finishAgent: async (agentName, reason = null) => {
        try {
          const formData = reason ? { reason } : {};
          await postForm(`/agents/${agentName}/finish`, formData);
          await get().refreshStatus();
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      restartAgent: async (agentName) => {
        try {
          await postForm(`/agents/${agentName}/restart`);
          await get().refreshStatus();
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      // Agent Management Actions
      fetchAgents: async () => {
        set({ agentsLoading: true });
        try {
          const res = await apiCall('/api/v1/agents/?page=1&per_page=100');
          if (res.ok) {
            const data = await res.json();
            set({ agents: data.items || [], agentsLoading: false });
          } else {
            set({ agentsLoading: false });
          }
        } catch (error) {
          set({ agentsLoading: false, error: error.message });
        }
      },
      
      createAgent: async (agentData) => {
        set({ isLoading: true, error: null });
        try {
          const res = await apiCall('/api/v1/agents/', {
            method: 'POST',
            body: JSON.stringify(agentData),
          });
          
          if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail?.message || 'Failed to create agent');
          }
          
          await get().fetchAgents();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      updateAgent: async (agentId, agentData) => {
        set({ isLoading: true, error: null });
        try {
          const res = await apiCall(`/api/v1/agents/${agentId}`, {
            method: 'PUT',
            body: JSON.stringify(agentData),
          });
          
          if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail?.message || 'Failed to update agent');
          }
          
          await get().fetchAgents();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      deleteAgent: async (agentId) => {
        set({ isLoading: true, error: null });
        try {
          const res = await apiCall(`/api/v1/agents/${agentId}`, {
            method: 'DELETE',
          });
          
          if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail?.message || 'Failed to delete agent');
          }
          
          await get().fetchAgents();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      updateAgentPermissions: async (agentId, permissions) => {
        try {
          const res = await apiCall(`/api/v1/agents/${agentId}/permissions`, {
            method: 'PUT',
            body: JSON.stringify(permissions),
          });
          
          if (!res.ok) {
            throw new Error('Failed to update permissions');
          }
          
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      updateAgentVoice: async (agentId, voiceSettings) => {
        try {
          const res = await apiCall(`/api/v1/agents/${agentId}/voice`, {
            method: 'PUT',
            body: JSON.stringify(voiceSettings),
          });
          
          if (!res.ok) {
            throw new Error('Failed to update voice settings');
          }
          
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      updateAgentMemory: async (agentId, memorySettings) => {
        try {
          const res = await apiCall(`/api/v1/agents/${agentId}/memory`, {
            method: 'PUT',
            body: JSON.stringify(memorySettings),
          });
          
          if (!res.ok) {
            throw new Error('Failed to update memory settings');
          }
          
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      clearAgentMemory: async (agentId, sessionId = null) => {
        try {
          const url = sessionId 
            ? `/api/v1/agents/${agentId}/memory?session_id=${sessionId}`
            : `/api/v1/agents/${agentId}/memory`;
          
          const res = await apiCall(url, { method: 'DELETE' });
          
          if (!res.ok) {
            throw new Error('Failed to clear agent memory');
          }
          
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      // Sync State
      syncState: async () => {
        try {
          const res = await apiCall('/api/v1/state/sync', { method: 'POST' });
          if (res.ok) {
            await get().fetchAgents();
            await get().refreshStatus();
          }
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      // Get single agent
      getAgent: async (agentId) => {
        try {
          const res = await apiCall(`/api/v1/agents/${agentId}`);
          if (res.ok) {
            return await res.json();
          }
          return null;
        } catch (error) {
          return null;
        }
      },
    }),
    {
      name: 'chatmode-storage',
      partialize: (state) => ({
        authToken: state.authToken,
        autoScroll: state.autoScroll,
        filterEnabled: state.filterEnabled,
      }),
    }
  )
);

export default useStore;
