import { useState, useEffect, useCallback } from 'react';
import { ChatSession, Message } from '../types/chat';
import { chatSessionStorage } from '../utils/chatStorage';

export interface UseChatHistoryReturn {
  // Data
  messages: Message[];
  sessionInfo: ChatSession | null;
  isLoading: boolean;
  error: string | null;

  // Methods
  addMessage: (message: Message) => Promise<boolean>;
  updateMessage: (messageId: string, updates: Partial<Message>) => Promise<boolean>;
  loadHistory: (chatId: string) => Promise<void>;
  saveSession: () => Promise<boolean>;
  clearMessages: () => Promise<boolean>;
  refreshHistory: () => Promise<void>;
}

/**
 * Hook for managing chat message history
 * Provides persistent storage and retrieval of chat messages using localStorage
 */
export const useChatHistory = (chatId: string): UseChatHistoryReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionInfo, setSessionInfo] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load chat history from storage
   */
  const loadHistory = useCallback(async (targetChatId: string = chatId) => {
    if (!targetChatId || targetChatId === 'new') {
      setMessages([]);
      setSessionInfo(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await chatSessionStorage.load(targetChatId);

      if (result.session) {
        setSessionInfo(result.session);

        // Filter out progress bar messages for display, keep regular messages
        const displayMessages = result.session.messages.filter(msg =>
          !msg.isProgressBar && !msg.isQueryAnalyzing
        );

        // Convert timestamp strings to Date objects and ensure consistent format
        const processedMessages = displayMessages.map(msg => ({
          ...msg,
          timestamp: typeof msg.timestamp === 'string' ? new Date(msg.timestamp) : msg.timestamp
        }));

        setMessages(processedMessages);
      } else {
        setMessages([]);
        setSessionInfo(null);
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
      setError(err instanceof Error ? err.message : 'Failed to load chat history');
      setMessages([]);
      setSessionInfo(null);
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);

  /**
   * Refresh current chat history
   */
  const refreshHistory = useCallback(async () => {
    await loadHistory(chatId);
  }, [chatId, loadHistory]);

  /**
   * Add a new message to chat history
   */
  const addMessage = useCallback(async (message: Message): Promise<boolean> => {
    if (!chatId || chatId === 'new') return false;

    try {
      // Get current session
      let currentSession = sessionInfo;
      if (!currentSession) {
        const result = await chatSessionStorage.load(chatId);
        currentSession = result.session || chatSessionStorage['createEmptySession'](chatId);
      }

      // Auto-categorize message if not already categorized
      const categorizedMessage = { ...message };
      if (!categorizedMessage.messageCategory) {
        categorizedMessage.messageCategory = message.type === 'user' ? 'user_query' : 'assistant_response';
      }

      // Add message to session
      const updatedMessages = [...currentSession.messages, categorizedMessage];
      const updatedSession: ChatSession = {
        ...currentSession,
        messages: updatedMessages,
        lastMessage: message.content.length > 50 ? message.content.substring(0, 50) + '...' : message.content,
        lastUpdated: new Date(),
        // Update video count if videos attached to message
        videoCount: message.videos ? message.videos.length : (currentSession.videoCount || 0)
      };

      // Save session
      const saveResult = await chatSessionStorage.save(chatId, updatedSession);
      if (saveResult.success) {
        setSessionInfo(updatedSession);

        // Only add to display messages if it's not a system/progress message
        if (!message.isProgressBar && !message.isQueryAnalyzing) {
          setMessages(prevMessages => [...prevMessages, message]);
        }

        return true;
      } else {
        setError(saveResult.error || 'Failed to save message');
        return false;
      }
    } catch (err) {
      console.error('Failed to add message:', err);
      setError(err instanceof Error ? err.message : 'Failed to add message');
      return false;
    }
  }, [chatId, sessionInfo]);

  /**
   * Update an existing message
   */
  const updateMessage = useCallback(async (messageId: string, updates: Partial<Message>): Promise<boolean> => {
    if (!chatId || chatId === 'new') return false;

    try {
      let currentSession = sessionInfo;
      if (!currentSession) {
        const result = await chatSessionStorage.load(chatId);
        currentSession = result.session || chatSessionStorage['createEmptySession'](chatId);
      }

      // Update message in session
      const updatedMessages = currentSession.messages.map(msg =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      );

      const updatedSession: ChatSession = {
        ...currentSession,
        messages: updatedMessages,
        lastUpdated: new Date(),
      };

      // Save session
      const saveResult = await chatSessionStorage.save(chatId, updatedSession);
      if (saveResult.success) {
        setSessionInfo(updatedSession);

        // Update display messages (only for regular messages, not system messages)
        setMessages(prevMessages =>
          prevMessages.map(msg =>
            msg.id === messageId ? { ...msg, ...updates } : msg
          )
        );

        return true;
      } else {
        setError(saveResult.error || 'Failed to update message');
        return false;
      }
    } catch (err) {
      console.error('Failed to update message:', err);
      setError(err instanceof Error ? err.message : 'Failed to update message');
      return false;
    }
  }, [chatId, sessionInfo]);

  /**
   * Save current session state
   */
  const saveSession = useCallback(async (): Promise<boolean> => {
    if (!chatId || chatId === 'new' || !sessionInfo) return false;

    try {
      const saveResult = await chatSessionStorage.save(chatId, sessionInfo);
      if (saveResult.success) {
        return true;
      } else {
        setError(saveResult.error || 'Failed to save session');
        return false;
      }
    } catch (err) {
      console.error('Failed to save session:', err);
      setError(err instanceof Error ? err.message : 'Failed to save session');
      return false;
    }
  }, [chatId, sessionInfo]);

  /**
   * Clear all messages for this chat
   */
  const clearMessages = useCallback(async (): Promise<boolean> => {
    if (!chatId || chatId === 'new') return false;

    try {
      const clearResult = await chatSessionStorage.delete(chatId);
      if (clearResult.success) {
        setMessages([]);
        setSessionInfo(null);
        return true;
      } else {
        setError(clearResult.error || 'Failed to clear messages');
        return false;
      }
    } catch (err) {
      console.error('Failed to clear messages:', err);
      setError(err instanceof Error ? err.message : 'Failed to clear messages');
      return false;
    }
  }, [chatId]);

  // Load history when chatId changes
  useEffect(() => {
    loadHistory();
  }, [chatId, loadHistory]);

  // Custom event listener for external updates (can be used by other components)
  useEffect(() => {
    const handleReloadHistory = () => {
      refreshHistory();
    };

    // Listen for custom events
    window.addEventListener('reload-chat-history', handleReloadHistory);

    return () => {
      window.removeEventListener('reload-chat-history', handleReloadHistory);
    };
  }, [refreshHistory]);

  return {
    messages,
    sessionInfo,
    isLoading,
    error,
    addMessage,
    updateMessage,
    loadHistory,
    saveSession,
    clearMessages,
    refreshHistory
  };
};