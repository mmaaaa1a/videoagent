import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader2, AlertCircle, CheckCircle, Save } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Textarea } from './ui/textarea'
import { videoRAGApi } from '../services/api'
import { toast } from 'sonner'
import { generateChatId } from '../lib/utils'
import { Message } from '../types/chat'
import { useChatHistory } from '../hooks/useChatHistory'

interface ChatInterfaceProps {
  chatId: string
  disabled?: boolean
}

export default function ChatInterface({ chatId, disabled = false }: ChatInterfaceProps) {
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [queryStatus, setQueryStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle')
  const [currentProcessingMessage, setCurrentProcessingMessage] = useState<Message | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Use chat history hook for persistent message storage
  const {
    messages,
    isLoading: isHistoryLoading,
    error: historyError,
    addMessage: addMessageToHistory,
    updateMessage: updateMessageInHistory
  } = useChatHistory(chatId)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Poll for query status
  useEffect(() => {
    if (queryStatus === 'processing' && currentProcessingMessage) {
      const interval = setInterval(async () => {
        try {
          const response = await videoRAGApi.getSessionStatus(chatId, 'query')
          if (response.data.success) {
            const status = response.data

            if (status.status === 'completed') {
              setQueryStatus('completed')
              // Update processing message with final answer (don't remove, just replace content)
              const finalAnswer = status.answer || '抱歉，我无法回答这个问题。';
              updateMessageInHistory(currentProcessingMessage.id, {
                type: 'assistant',
                content: finalAnswer,
                status: 'sent'
              }).then(() => {
                setCurrentProcessingMessage(null)
                setIsLoading(false)
              })
            } else if (status.status === 'error') {
              setQueryStatus('error')
              // Update processing message with error content
              updateMessageInHistory(currentProcessingMessage.id, {
                type: 'assistant',
                content: `错误: ${status.message}`,
                status: 'error'
              }).then(() => {
                setCurrentProcessingMessage(null)
                setIsLoading(false)
                toast.error('查询处理失败')
              })
            }
          }
        } catch (error) {
          console.error('Failed to check query status:', error)
        }
      }, 2000)

      return () => clearInterval(interval)
    }
  }, [queryStatus, chatId, currentProcessingMessage])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || disabled) return

    const userMessage: Message = {
      id: generateChatId(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
      status: 'sent'
    }

    const processingMessage: Message = {
      id: generateChatId(),
      type: 'assistant',
      content: '正在处理您的问题...',
      timestamp: new Date(),
      status: 'sending'
    }

    try {
      // Save user message to history
      await addMessageToHistory(userMessage)

      // Add processing message (temporary, will be replaced with actual response)
      await addMessageToHistory(processingMessage)

      // Store processing message ID for useEffect
      setCurrentProcessingMessage(processingMessage)

      setInputMessage('')
      setIsLoading(true)
      setQueryStatus('processing')
      const response = await videoRAGApi.queryVideo(chatId, userMessage.content)

      if (!response.data.success) {
        throw new Error(response.data.error || '查询失败')
      }
    } catch (error) {
      console.error('Query error:', error)
      setQueryStatus('error')

      // Replace processing message with error message
      if (currentProcessingMessage) {
        await updateMessageInHistory(currentProcessingMessage.id, {
          type: 'assistant',
          content: '抱歉，查询处理失败。请稍后重试。',
          status: 'error'
        })
      }

      setCurrentProcessingMessage(null)
      setIsLoading(false)
      toast.error('查询失败，请重试')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value)

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  return (
    <Card className="w-full max-w-4xl mx-auto h-[600px] flex flex-col">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <Bot className="w-5 h-5" />
          视频对话助手
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Loading/History Error State */}
        {isHistoryLoading && (
          <div className="flex justify-center items-center p-6">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-primary" />
              <p className="text-sm text-muted-foreground">正在加载对话历史...</p>
            </div>
          </div>
        )}

        {historyError && (
          <div className="m-4 p-4 bg-destructive/10 border border-destructive/20 rounded">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">对话历史加载失败: {historyError}</span>
            </div>
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && !isHistoryLoading ? (
            <div className="text-center py-12">
              <Bot className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">开始与视频对话</h3>
              <p className="text-muted-foreground">
                上传视频后，您可以询问关于视频内容的任何问题。您的对话将被自动保存。
              </p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex items-start gap-3 ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  } animate-fade-in`}
                >
                  {message.type === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-3 ${
                      message.type === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>

                    {message.status && (
                      <div className="flex items-center gap-1 mt-2">
                        {message.status === 'sending' && (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        )}
                        {message.status === 'sent' && (
                          <CheckCircle className="w-3 h-3 text-green-600" />
                        )}
                        {message.status === 'error' && (
                          <AlertCircle className="w-3 h-3 text-red-600" />
                        )}
                        <span className="text-xs opacity-70">
                          {typeof message.timestamp === 'string'
                            ? new Date(message.timestamp).toLocaleTimeString()
                            : message.timestamp.toLocaleTimeString()
                          }
                        </span>
                      </div>
                    )}
                  </div>

                  {message.type === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={handleTextareaChange}
              onKeyPress={handleKeyPress}
              placeholder="询问关于视频内容的问题..."
              className="flex-1 min-h-[40px] max-h-[120px] resize-none"
              disabled={isLoading || disabled}
              rows={1}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading || disabled}
              size="icon"
              className="flex-shrink-0"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>

          {queryStatus === 'processing' && (
            <div className="mt-2 text-sm text-muted-foreground flex items-center gap-2">
              <Loader2 className="w-3 h-3 animate-spin" />
              正在分析视频内容并生成回答...
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}