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
    // Try to parse error as JSON
    let errorMessage = `Request failed: ${res.status}`;
    
    // Clone response because body can only be consumed once 
    // (attempting both .json() and .text() on same response would fail)
    const clonedRes = res.clone();
    
    try {
      const error = await res.json();
      // Backend returns errors with 'reason' field
      errorMessage = error.reason || errorMessage;
    } catch (jsonError) {
      // If JSON parse fails, try to get text from cloned response
      try {
        const text = await clonedRes.text();
        if (text) errorMessage = text;
      } catch (textError) {
        // Use default error message
      }
    }
    throw new Error(errorMessage);
  }
  
  // Parse successful response as JSON
  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await res.json();
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
      eventSource: null,
      messageRate: 1.0,
      
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
      applyStatus: (data) => {
        set({
          isRunning: Boolean(data.running),
          topic: data.topic || '',
          sessionId: data.session_id || null,
          messages: data.last_messages || [],
          agentStates: data.agent_states || {},
          messageRate: Number(data.message_rate || 1.0),
          connectionStatus: 'connected',
          lastUpdated: new Date(),
        });
      },

      refreshStatus: async () => {
        try {
          const res = await fetch('/api/v1/control/status');
          if (!res.ok) throw new Error('Status unavailable');
          const data = await res.json();
          get().applyStatus(data);
        } catch (error) {
          set({ connectionStatus: 'disconnected' });
          console.error('Status refresh failed:', error);
        }
      },

      connectRealtime: () => {
        if (typeof window === 'undefined' || get().eventSource) return;
        const source = new EventSource('/api/v1/control/events');
        source.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            get().applyStatus(data);
          } catch (error) {
            console.debug('Ignored malformed realtime payload', error);
          }
        };
        source.onerror = () => {
          set({ connectionStatus: 'disconnected' });
        };
        set({ eventSource: source });
      },

      disconnectRealtime: () => {
        const source = get().eventSource;
        if (source) source.close();
        set({ eventSource: null });
      },
      
      startSession: async (topic) => {
        set({ isLoading: true, error: null });
        try {
          const response = await postForm('/api/v1/control/start', { topic });
          
          // Update with response state immediately if available
          if (response.running !== undefined) {
            set({ 
              isRunning: Boolean(response.running),
              topic: response.topic || topic,
              sessionId: response.session_id,
              isLoading: false,
            });
          }
          
          // Then refresh for complete state
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
          const response = await postForm('/api/v1/control/stop');
          
          // Update with response state immediately if available
          if (response.running !== undefined) {
            set({ 
              isRunning: Boolean(response.running),
              isLoading: false,
            });
          }
          
          // Then refresh for complete state
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
          const response = await postForm('/api/v1/control/resume');
          
          // Update with response state immediately if available
          if (response.running !== undefined) {
            set({ 
              isRunning: Boolean(response.running),
              topic: response.topic || get().topic,
              sessionId: response.session_id || get().sessionId,
              isLoading: false,
            });
          }
          
          // Then refresh for complete state
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
          await postForm('/api/v1/control/memory/clear');
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
          await postForm('/api/v1/control/messages', { content, sender });
          await get().refreshStatus();
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },

      interruptSession: async () => {
        set({ isLoading: true, error: null });
        try {
          await postForm('/api/v1/control/interrupt');
          await get().refreshStatus();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },

      switchContext: async (topic) => {
        set({ isLoading: true, error: null });
        try {
          await postForm('/api/v1/control/context/switch', { topic });
          await get().refreshStatus();
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },

      setMessageRate: async (rate) => {
        try {
          const response = await postForm('/api/v1/control/rate', { rate: String(rate) });
          if (response.message_rate !== undefined) {
            set({ messageRate: Number(response.message_rate) });
          }
          return true;
        } catch (error) {
          set({ error: error.message });
          return false;
        }
      },
      
      // Agent Control Actions
      pauseAgent: async (agentName, reason = null) => {
        // Optimistic update
        const currentStates = get().agentStates;
        set({ 
          agentStates: {
            ...currentStates,
            [agentName]: {
              ...currentStates[agentName],
              state: 'paused',
              reason: reason || null,
              changed_at: new Date().toISOString(),
            }
          }
        });
        
        try {
          const formData = reason ? { reason } : {};
          const response = await postForm(`/agents/${agentName}/pause`, formData);
          
          // Update with authoritative backend state if available
          if (response.agent_state) {
            set({ 
              agentStates: {
                ...get().agentStates,
                [agentName]: response.agent_state
              }
            });
          } else {
            // Fallback: refresh to get authoritative state from backend
            await get().refreshStatus();
          }
          return true;
        } catch (error) {
          // Revert optimistic update on error
          await get().refreshStatus();
          set({ error: error.message });
          return false;
        }
      },
      
      resumeAgent: async (agentName) => {
        // Optimistic update
        const currentStates = get().agentStates;
        set({ 
          agentStates: {
            ...currentStates,
            [agentName]: {
              ...currentStates[agentName],
              state: 'active',
              reason: null,
              changed_at: new Date().toISOString(),
            }
          }
        });
        
        try {
          const response = await postForm(`/agents/${agentName}/resume`);
          
          // Update with authoritative backend state if available
          if (response.agent_state) {
            set({ 
              agentStates: {
                ...get().agentStates,
                [agentName]: response.agent_state
              }
            });
          } else {
            // Fallback: refresh to get authoritative state from backend
            await get().refreshStatus();
          }
          return true;
        } catch (error) {
          // Revert optimistic update on error
          await get().refreshStatus();
          set({ error: error.message });
          return false;
        }
      },
      
      stopAgent: async (agentName, reason = null) => {
        // Optimistic update
        const currentStates = get().agentStates;
        set({ 
          agentStates: {
            ...currentStates,
            [agentName]: {
              ...currentStates[agentName],
              state: 'stopped',
              reason: reason || null,
              changed_at: new Date().toISOString(),
            }
          }
        });
        
        try {
          const formData = reason ? { reason } : {};
          const response = await postForm(`/agents/${agentName}/stop`, formData);
          
          // Update with authoritative backend state if available
          if (response.agent_state) {
            set({ 
              agentStates: {
                ...get().agentStates,
                [agentName]: response.agent_state
              }
            });
          } else {
            // Fallback: refresh to get authoritative state from backend
            await get().refreshStatus();
          }
          return true;
        } catch (error) {
          // Revert optimistic update on error
          await get().refreshStatus();
          set({ error: error.message });
          return false;
        }
      },
      
      finishAgent: async (agentName, reason = null) => {
        // Optimistic update
        const currentStates = get().agentStates;
        set({ 
          agentStates: {
            ...currentStates,
            [agentName]: {
              ...currentStates[agentName],
              state: 'finished',
              reason: reason || null,
              changed_at: new Date().toISOString(),
            }
          }
        });
        
        try {
          const formData = reason ? { reason } : {};
          const response = await postForm(`/agents/${agentName}/finish`, formData);
          
          // Update with authoritative backend state if available
          if (response.agent_state) {
            set({ 
              agentStates: {
                ...get().agentStates,
                [agentName]: response.agent_state
              }
            });
          } else {
            // Fallback: refresh to get authoritative state from backend
            await get().refreshStatus();
          }
          return true;
        } catch (error) {
          // Revert optimistic update on error
          await get().refreshStatus();
          set({ error: error.message });
          return false;
        }
      },
      
      restartAgent: async (agentName) => {
        // Optimistic update
        const currentStates = get().agentStates;
        set({ 
          agentStates: {
            ...currentStates,
            [agentName]: {
              ...currentStates[agentName],
              state: 'active',
              reason: 'Agent restarted',
              changed_at: new Date().toISOString(),
            }
          }
        });
        
        try {
          const response = await postForm(`/agents/${agentName}/restart`);
          
          // Update with authoritative backend state if available
          if (response.agent_state) {
            set({ 
              agentStates: {
                ...get().agentStates,
                [agentName]: response.agent_state
              }
            });
          } else {
            // Fallback: refresh to get authoritative state from backend
            await get().refreshStatus();
          }
          return true;
        } catch (error) {
          // Revert optimistic update on error
          await get().refreshStatus();
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
