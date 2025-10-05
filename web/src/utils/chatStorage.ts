import { Message } from '../types/chat';

// Chat session data structure (aligned with desktop version)
export interface ChatSession {
  id: string;
  title: string;
  createdAt: Date | string;
  lastUpdated: Date | string;
  videos: any[];
  analysisState: 'none' | 'analyzing' | 'completed' | 'error';
  messages: Message[];
  lastMessage: string;
  videoCount?: number; // Keep for backward compatibility
}

// Storage result interfaces
interface LoadResult {
  session?: ChatSession;
}

interface SaveResult {
  success: boolean;
  error?: string;
}

// LocalStorage-based storage implementation
export class ChatSessionStorage {
  private keyPrefix = 'videorag-chat-session-';

  private getStorageKey(chatId: string): string {
    return `${this.keyPrefix}${chatId}`;
  }

  /**
   * Load chat session from localStorage
   */
  async load(chatId: string): Promise<LoadResult> {
    try {
      const key = this.getStorageKey(chatId);
      const data = localStorage.getItem(key);

      if (!data) {
        return { session: this.createEmptySession(chatId) };
      }

      const session = JSON.parse(data);
      // Convert date strings back to Date objects
      if (session.createdAt && typeof session.createdAt === 'string') {
        session.createdAt = new Date(session.createdAt);
      }
      if (session.lastUpdated && typeof session.lastUpdated === 'string') {
        session.lastUpdated = new Date(session.lastUpdated);
      }

      return { session };
    } catch (error) {
      console.error('Failed to load chat session:', error);
      return { session: this.createEmptySession(chatId) };
    }
  }

  /**
   * Save chat session to localStorage
   */
  async save(chatId: string, session: ChatSession): Promise<SaveResult> {
    try {
      const key = this.getStorageKey(chatId);
      const dataToSave = {
        ...session,
        createdAt: session.createdAt instanceof Date ? session.createdAt.toISOString() : session.createdAt,
        lastUpdated: session.lastUpdated instanceof Date ? session.lastUpdated.toISOString() : session.lastUpdated
      };

      localStorage.setItem(key, JSON.stringify(dataToSave));
      return { success: true };
    } catch (error) {
      console.error('Failed to save chat session:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown storage error' };
    }
  }

  /**
   * Delete chat session from localStorage
   */
  async delete(chatId: string): Promise<SaveResult> {
    try {
      const key = this.getStorageKey(chatId);
      localStorage.removeItem(key);
      return { success: true };
    } catch (error) {
      console.error('Failed to delete chat session:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown delete error' };
    }
  }

  /**
   * Get all chat session IDs
   */
  getAllChatIds(): string[] {
    const keys = Object.keys(localStorage);
    const sessionKeys = keys.filter(key => key.startsWith(this.keyPrefix));
    return sessionKeys.map(key => key.replace(this.keyPrefix, ''));
  }

  /**
   * Create empty session data structure
   */
  private createEmptySession(chatId: string): ChatSession {
    return {
      id: chatId,
      title: 'New Chat',
      createdAt: new Date(),
      lastUpdated: new Date(),
      videos: [],
      analysisState: 'none',
      messages: [],
      lastMessage: '',
      videoCount: 0
    };
  }
}

// Singleton instance
export const chatSessionStorage = new ChatSessionStorage();

// Utility Functions (ported from desktop version)
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const generateChatId = (): string => {
  return `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

export const generateMessageId = (): string => {
  return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};