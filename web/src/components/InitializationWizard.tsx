import React, { useState } from 'react'
import { Settings, CheckCircle, AlertCircle, Eye, EyeOff, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { videoRAGApi, type VideoRAGConfig } from '../services/api'
import { toast } from 'sonner'
import { generateChatId } from '../lib/utils'

interface InitializationWizardProps {
  onComplete: (chatId: string) => void
}

export default function InitializationWizard({ onComplete }: InitializationWizardProps) {
  const [step, setStep] = useState(1)
  const [config, setConfig] = useState<VideoRAGConfig>({
    openai_api_key: '',
    openai_base_url: 'https://api.openai.com/v1',
    ali_dashscope_api_key: '',
    ali_dashscope_base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    analysisModel: 'gpt-4',
    processingModel: 'gpt-3.5-turbo',
    caption_model: 'qwen-vl-plus',
    asr_mode: 'local',  // 改为ASR模式选择：local 或 api
    asr_model: 'large-v3', // 本地模式：large-v3等，API模式：parformance-realtime-v2等
    image_bind_model_path: '/app/models/imagebind.pth',
    base_storage_path: '/app/storage'
  })
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({})
  const [isInitializing, setIsInitializing] = useState(false)
  const [initStatus, setInitStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleConfigChange = (field: keyof VideoRAGConfig, value: string) => {
    setConfig(prev => ({ ...prev, [field]: value }))
  }

  const toggleApiKeyVisibility = (field: string) => {
    setShowApiKeys(prev => ({ ...prev, [field]: !prev[field] }))
  }

  const validateConfig = () => {
    if (!config.openai_api_key.trim()) {
      toast.error('请输入OpenAI API密钥')
      return false
    }
    if (!config.ali_dashscope_api_key.trim()) {
      toast.error('请输入阿里云DashScope API密钥')
      return false
    }
    // API ASR模式需要验证API密钥
    if (config.asr_mode === 'api' && !config.ali_dashscope_api_key.trim()) {
      toast.error('API ASR模式需要配置阿里云DashScope API密钥')
      return false
    }
    return true
  }

  const handleInitialize = async () => {
    if (!validateConfig()) return

    setIsInitializing(true)
    setInitStatus('idle')
    setErrorMessage('')

    try {
      const response = await videoRAGApi.initializeSystem(config)

      if (response.data.success) {
        setInitStatus('success')
        toast.success('系统初始化成功！')

        // Generate new chat session
        const chatId = generateChatId()

        // Wait a moment before showing success
        setTimeout(() => {
          onComplete(chatId)
        }, 1500)
      } else {
        setInitStatus('error')
        setErrorMessage(response.data.error || '初始化失败')
        toast.error('系统初始化失败')
      }
    } catch (error) {
      setInitStatus('error')
      setErrorMessage('网络错误，请检查连接')
      toast.error('初始化失败，请重试')
      console.error('Initialization error:', error)
    } finally {
      setIsInitializing(false)
    }
  }

  const renderStep1 = () => (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader className="text-center">
        <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <Settings className="w-8 h-8 text-primary" />
        </div>
        <CardTitle className="text-2xl">欢迎使用 VideoRAG</CardTitle>
        <CardDescription>
          配置AI服务以开始与视频进行智能对话
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <h3 className="text-lg font-medium">配置说明</h3>
          <div className="space-y-3 text-sm text-muted-foreground">
            <p>• 需要配置OpenAI API用于文本分析和对话生成</p>
            <p>• 需要配置阿里云DashScope API用于视频理解</p>
            <p>• 您的API密钥将安全存储在本地环境中</p>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-medium">模型配置</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">分析模型</label>
              <Input
                value={config.analysisModel}
                onChange={(e) => handleConfigChange('analysisModel', e.target.value)}
                placeholder="e.g., gpt-4, custom-model"
                className="w-full p-2 border rounded-md"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">处理模型</label>
              <Input
                value={config.processingModel}
                onChange={(e) => handleConfigChange('processingModel', e.target.value)}
                placeholder="e.g., gpt-3.5-turbo, custom-model"
                className="w-full p-2 border rounded-md"
              />
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-sm font-medium mb-2 block">ASR语音转文本配置</label>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">ASR模式</label>
                <select
                  value={config.asr_mode}
                  onChange={(e) => {
                    const newMode = e.target.value
                    handleConfigChange('asr_mode', newMode)
                    // 根据模式自动设置默认模型
                    if (newMode === 'local') {
                      handleConfigChange('asr_model', 'large-v3')
                    } else if (newMode === 'api') {
                      handleConfigChange('asr_model', 'paraformer-realtime-v2')
                    }
                  }}
                  className="w-full p-2 border rounded-md"
                >
                  <option value="local">本地处理（Faster-Whisper）- 100%离线</option>
                  <option value="api">云端API（阿里云DashScope） - 需要网络和费用</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">ASR模型</label>
                <Input
                  value={config.asr_model}
                  onChange={(e) => handleConfigChange('asr_model', e.target.value)}
                  placeholder={
                    config.asr_mode === 'local'
                      ? "e.g., large-v3, small, medium"
                      : "e.g., paraformer-realtime-v2, paraformer-realtime-16k-v1"
                  }
                  className="w-full p-2 border rounded-md"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {config.asr_mode === 'local'
                    ? "本地Faster-Whisper模型，支持多语言，完全离线处理"
                    : "阿里云DashScope ASR模型，支持实时语音识别，速度更快但需API调用费"
                  }
                </p>
              </div>
            </div>
          </div>
        </div>

        <Button onClick={() => setStep(2)} className="w-full" size="lg">
          下一步：配置API密钥
        </Button>
      </CardContent>
    </Card>
  )

  const renderStep2 = () => (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5" />
          API密钥配置
        </CardTitle>
        <CardDescription>
          请配置必要的API密钥以启用VideoRAG功能
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* OpenAI Configuration */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">OpenAI 配置</h3>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">API 密钥</label>
              <div className="relative">
                <Input
                  type={showApiKeys.openai ? 'text' : 'password'}
                  value={config.openai_api_key}
                  onChange={(e) => handleConfigChange('openai_api_key', e.target.value)}
                  placeholder="sk-..."
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0"
                  onClick={() => toggleApiKeyVisibility('openai')}
                >
                  {showApiKeys.openai ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">API 基础URL（可选）</label>
              <Input
                value={config.openai_base_url}
                onChange={(e) => handleConfigChange('openai_base_url', e.target.value)}
                placeholder="https://api.openai.com/v1"
              />
            </div>
          </div>
        </div>

        {/* Aliyun DashScope Configuration */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">阿里云 DashScope 配置</h3>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">API 密钥</label>
              <div className="relative">
                <Input
                  type={showApiKeys.dashscope ? 'text' : 'password'}
                  value={config.ali_dashscope_api_key}
                  onChange={(e) => handleConfigChange('ali_dashscope_api_key', e.target.value)}
                  placeholder="sk-..."
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0"
                  onClick={() => toggleApiKeyVisibility('dashscope')}
                >
                  {showApiKeys.dashscope ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">API 基础URL（可选）</label>
              <Input
                value={config.ali_dashscope_base_url}
                onChange={(e) => handleConfigChange('ali_dashscope_base_url', e.target.value)}
                placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1"
              />
            </div>
          </div>
        </div>

        {/* Status Display */}
        {initStatus !== 'idle' && (
          <div className={`p-4 rounded-lg ${
            initStatus === 'success'
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center gap-2">
              {initStatus === 'success' ? (
                <>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="text-green-800">系统初始化成功！正在跳转...</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <span className="text-red-800">初始化失败: {errorMessage}</span>
                </>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button
            variant="outline"
            onClick={() => setStep(1)}
            disabled={isInitializing}
            className="flex-1"
          >
            上一步
          </Button>
          <Button
            onClick={handleInitialize}
            disabled={isInitializing}
            className="flex-1"
          >
            {isInitializing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                正在初始化...
              </>
            ) : (
              '完成配置'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
      </div>
    </div>
  )
}