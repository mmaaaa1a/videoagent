// Shared types for chat functionality (aligned with desktop version)

// Message interface used throughout the chat system
export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date | string; // Allow string for JSON serialization
  status?: 'sending' | 'sent' | 'error';
  // Additional desktop version fields
  messageCategory?: 'user_query' | 'assistant_response' | 'system_info' | 'analysis_status';
  videos?: string[]; // Video names attached to message
  isProgressBar?: boolean; // Special message type for progress display
  analysisSteps?: AnalysisStep[]; // Steps for video analysis progress
  isQueryAnalyzing?: boolean; // Message type for query analysis
  queryStep?: string; // Current query processing step
  queryMessage?: string; // Query processing message
  queryStatus?: 'active' | 'completed' | 'error'; // Query processing status
}

// Analysis step interface for progress tracking
export interface AnalysisStep {
  id: string;
  name: string;
  message: string;
  status: 'active' | 'completed' | 'error';
  timestamp: Date | string;
}

// Uploaded video information
export interface UploadedVideo {
  id: string;
  name: string;
  path: string;
  url: string; // Object URL for display
  size: number;
  type: string;
  duration?: number; // Video duration in seconds
  thumbnail?: string; // Thumbnail URL
}

// Video analysis state
export interface VideoAnalysisState {
  isAnalyzing: boolean;
  progress: number; // 0-100
  currentStep: string;
  selectedVideos: UploadedVideo[];
}

// Simplified chat session interface (for app navigation)
export interface SimpleChatSession {
  id: string;
  createdAt: Date;
  videoCount: number;
  status: 'ready' | 'processing' | 'completed' | 'error';
}

// Full chat session interface (for storage and detailed management)
export interface ChatSession {
  id: string;
  title: string;
  createdAt: Date | string;
  lastUpdated: Date | string;
  videos: any[]; // Video data from analysis
  analysisState: 'none' | 'analyzing' | 'completed' | 'error';
  messages: Message[];
  lastMessage: string;
  videoCount?: number; // Computed field for backward compatibility
  analysisProgress?: number; // Progress percentage
  currentStep?: string; // Current analysis step
}

// Chat session management interface
export interface ChatSessionManager {
  createSession(chatId: string, title?: string): SimpleChatSession;
  getSession(chatId: string): SimpleChatSession | null;
  updateSession(chatId: string, updates: Partial<SimpleChatSession>): void;
  deleteSession(chatId: string): void;
  completeAnalysis(chatId: string): void;
  updateSessionInfo(chatId: string, updates: any): void;
  startAnalysis(chatId: string, videos: any[]): void;
  getAllSessions(): SimpleChatSession[];
}

// Backward compatibility aliases
export type { SimpleChatSession as AppChatSession, ChatSession as StorageChatSession };