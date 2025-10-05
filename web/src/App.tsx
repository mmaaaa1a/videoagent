import React, { useState, useEffect } from 'react'
import { HashRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import VideoSelector from './components/VideoSelector'
import ChatInterface from './components/ChatInterface'
import SettingsPage from './pages/settings'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './components/ui/card'
import { Button } from './components/ui/button'
import { Settings, Upload, MessageSquare, Loader2, CheckCircle, Plus } from 'lucide-react'
import { videoRAGApi } from './services/api'
import { toast } from 'sonner'
import { generateChatId } from './lib/utils'
import './styles/globals.css'

interface ChatSession {
  id: string
  createdAt: Date
  videoCount: number
  status: 'ready' | 'processing' | 'completed'
}

// Main Chat Page Component
function MainPage() {
  const navigate = useNavigate()
  const [isInitialized, setIsInitialized] = useState<boolean | null>(null)
  const [currentChatId, setCurrentChatId] = useState<string>('')
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentView, setCurrentView] = useState<'upload' | 'chat'>('upload')
  const [systemStatus, setSystemStatus] = useState<any>(null)

  const handleSettingsClick = () => {
    navigate('/settings')
  }

  // Reuse the existing logic... (keeping the same implementation)

  // Check configuration and initialization status on mount
  useEffect(() => {
    checkInitialization()
  }, [])

  // Poll system status periodically
  useEffect(() => {
    if (isInitialized) {
      fetchSystemStatus()
      const interval = setInterval(fetchSystemStatus, 10000) // Every 10 seconds
      return () => clearInterval(interval)
    }
  }, [isInitialized])

  const checkInitialization = async () => {
    try {
      // First check if we have localStorage configuration
      const savedSettings = localStorage.getItem('videorag-settings')

      // Check system status
      const response = await videoRAGApi.getSystemStatus()

      if (response.data.success && response.data.global_config_set) {
        // System is properly initialized
        setIsInitialized(true)
        const newChatId = generateChatId()
        setCurrentChatId(newChatId)
        setChatSessions([{
          id: newChatId,
          createdAt: new Date(),
          videoCount: 0,
          status: 'ready'
        }])
      } else if (savedSettings) {
        // Have localStorage settings but system not initialized - redirect to settings
        navigate('/settings')
      } else {
        // Completely fresh installation - show simple welcome
        setIsInitialized(null) // Null means show welcome guide
      }
    } catch (error) {
      console.error('Failed to check initialization:', error)
      // Fall back to localStorage check
      const savedSettings = localStorage.getItem('videorag-settings')
      if (savedSettings) {
        setIsInitialized(true) // Assume initialized if we have settings
        const newChatId = generateChatId()
        setCurrentChatId(newChatId)
        setChatSessions([{
          id: newChatId,
          createdAt: new Date(),
          videoCount: 0,
          status: 'ready'
        }])
      } else {
        setIsInitialized(null) // Show welcome guide
      }
    } finally {
      setIsLoading(false)
    }
  }

  const fetchSystemStatus = async () => {
    try {
      const response = await videoRAGApi.getSystemStatus()
      if (response.data.success) {
        setSystemStatus(response.data)
      }
    } catch (error) {
      console.error('Failed to fetch system status:', error)
    }
  }

  const handleInitializationComplete = (chatId: string) => {
    setIsInitialized(true)
    setCurrentChatId(chatId)
    setChatSessions([{
      id: chatId,
      createdAt: new Date(),
      videoCount: 0,
      status: 'ready'
    }])
    setCurrentView('upload')
  }

  const handleUploadComplete = async (chatId: string) => {
    setChatSessions(prev => prev.map(session =>
      session.id === chatId
        ? { ...session, status: 'processing' as const }
        : session
    ))

    // Poll for indexing completion
    const checkIndexingStatus = async () => {
      try {
        const response = await videoRAGApi.getSessionStatus(chatId)
        if (response.data.success) {
          const status = response.data
          if (status.status === 'completed') {
            setChatSessions(prev => prev.map(session =>
              session.id === chatId
                ? { ...session, status: 'completed' as const }
                : session
            ))
            setCurrentView('chat')
            toast.success('视频处理完成，开始对话吧！')
          } else if (status.status === 'error') {
            toast.error('视频处理失败，请重试')
          } else {
            // Still processing, check again in 2 seconds
            setTimeout(checkIndexingStatus, 2000)
          }
        }
      } catch (error) {
        console.error('Failed to check indexing status:', error)
      }
    }

    setTimeout(checkIndexingStatus, 2000) // Start checking after 2 seconds
  }

  const createNewChat = () => {
    const newChatId = generateChatId()
    setCurrentChatId(newChatId)
    setChatSessions(prev => [...prev, {
      id: newChatId,
      createdAt: new Date(),
      videoCount: 0,
      status: 'ready'
    }])
    setCurrentView('upload')
  }

  const switchToChat = (chatId: string) => {
    setCurrentChatId(chatId)
    setCurrentView('chat')
  }

  const switchToUpload = (chatId: string) => {
    setCurrentChatId(chatId)
    setCurrentView('upload')
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-96">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
              <h3 className="text-lg font-medium">正在检查VideoRAG环境...</h3>
              <p className="text-sm text-muted-foreground">
                请稍候，正在初始化系统...
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Show welcome guide for fresh installations
  if (isInitialized === null) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-lg">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Settings className="w-8 h-8 text-primary" />
            </div>
            <CardTitle className="text-2xl">欢迎使用 VideoRAG</CardTitle>
            <CardDescription>
              开始您的第一个 AI 视频对话体验
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-muted-foreground">
              请先到设置页面配置您的API密钥和存储路径，然后就可以开始使用VideoRAG了。
            </p>
            <Button onClick={() => navigate('/settings')} size="lg" className="w-full">
              开始配置
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Main application content
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <MessageSquare className="w-4 h-4 text-primary-foreground" />
              </div>
              <h1 className="text-xl font-semibold">VideoRAG</h1>
              {systemStatus && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>{systemStatus.total_sessions} 个会话</span>
                  <span>•</span>
                  <span>{systemStatus.total_indexed_videos} 个视频</span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={createNewChat}>
                新建对话
              </Button>
              <Button variant="ghost" size="sm" onClick={handleSettingsClick}>
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {currentChatId && (
            <div className="space-y-6">
              {/* Chat Session Tabs */}
              {chatSessions.length > 1 && (
                <div className="flex gap-2 p-1 bg-muted rounded-lg">
                  {chatSessions.map((session) => (
                    <Button
                      key={session.id}
                      variant={currentChatId === session.id ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => setCurrentChatId(session.id)}
                      className="flex items-center gap-2"
                    >
                      <span>对话 {chatSessions.indexOf(session) + 1}</span>
                      {session.videoCount > 0 && (
                        <span className="text-xs bg-primary-foreground/20 px-1.5 rounded">
                          {session.videoCount}
                        </span>
                      )}
                    </Button>
                  ))}
                </div>
              )}

              {/* View Toggle */}
              <div className="flex gap-2 p-1 bg-muted rounded-lg w-fit">
                <Button
                  variant={currentView === 'upload' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => switchToUpload(currentChatId)}
                  className="flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  选择视频
                </Button>
                <Button
                  variant={currentView === 'chat' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => switchToChat(currentChatId)}
                  className="flex items-center gap-2"
                  // Removed video count requirement - allow chat even without videos
                  // Users can view history and get helpful messages about uploading videos
                >
                  <MessageSquare className="w-4 h-4" />
                  对话
                </Button>
              </div>

              {/* Current View */}
              {currentView === 'upload' ? (
                <VideoSelector
                  chatId={currentChatId}
                  onSubmitComplete={handleUploadComplete}
                />
              ) : (
                <ChatInterface chatId={currentChatId} />
              )}
            </div>
          )}
        </main>

        {/* Toast Notifications */}
        <Toaster
          position="top-right"
          offset={{ top: '48px' }}
          mobileOffset={{ top: '48px' }}
        />
      </div>
  )
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="/chat" element={<MainPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Router>
  )
}

export default App