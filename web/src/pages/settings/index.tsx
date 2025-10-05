import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/ui/card';
import { videoRAGApi } from '../../services/api';
import { toast } from 'sonner';
import { Button } from '../../components/ui/button';
import { ArrowLeft, Key, CheckCircle, XCircle, RefreshCw, AlertCircle, ExternalLink, Cpu, Download, FolderOpen, MessageSquare, Settings as SettingsIcon } from 'lucide-react';

interface SettingsState {
  // OpenAI Configuration
  openaiBaseUrl: string;
  openaiApiKey: string;
  processingModel: string;
  analysisModel: string;

  // DashScope Configuration
  dashscopeApiKey: string;
  captionModel: string;
  asrModel: string;

  // System Configuration
  storeDirectory: string;

  // ImageBind Model Configuration
  imagebindModelDirectory: string;
  selectedImagebindModel: string;

  // Initialization tracking
  imagebindInstalled: boolean;
}

// Model Status Section Component
const ModelStatusSection = ({
  storeDirectory,
  imagebindModelDirectory
}: {
  storeDirectory: string;
  imagebindModelDirectory: string;
}) => {
  const [modelStatus, setModelStatus] = React.useState<{
    exists: boolean;
    isComplete: boolean;
    isDownloading: boolean;
    size: string;
    checking: boolean;
    downloading: boolean;
  }>({
    exists: false,
    isComplete: false,
    isDownloading: false,
    size: '',
    checking: false,
    downloading: false,
  });

  const checkModelStatus = async () => {
    const modelDir = imagebindModelDirectory || '/app/models';
    setModelStatus(prev => ({ ...prev, checking: true }));

    try {
      const response = await fetch('/api/imagebind/check-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_directory: modelDir }),
      });

      const result = await response.json();
      if (result.success) {
        setModelStatus({
          exists: result.exists,
          isComplete: result.is_complete || false,
          isDownloading: result.is_downloading || false,
          size: result.size_mb ? `${result.size_mb}MB` : '',
          checking: false,
          downloading: false,
        });
      } else {
        setModelStatus(prev => ({
          ...prev,
          checking: false,
          exists: false,
          isComplete: false,
          isDownloading: false,
          size: '',
        }));
      }
    } catch (error) {
      console.error('Failed to check model status:', error);
      setModelStatus({
        exists: false,
        isComplete: false,
        isDownloading: false,
        size: '',
        checking: false,
        downloading: false,
      });
    }
  };

  React.useEffect(() => {
    checkModelStatus();
  }, [storeDirectory, imagebindModelDirectory]);

  const downloadModel = async () => {
    const modelDir = imagebindModelDirectory || '/app/models';
    setModelStatus(prev => ({ ...prev, downloading: true }));

    try {
      const response = await fetch('/api/imagebind/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_type: 'huge',
          model_directory: modelDir
        }),
      });

      const result = await response.json();
      if (result.success) {
        // 开始监控下载状态
        const checkDownloadStatus = async () => {
          const statusResponse = await fetch('/api/imagebind/check-status', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ model_directory: modelDir }),
          });
          const statusResult = await statusResponse.json();

          if (statusResult.success && statusResult.exists) {
            if (statusResult.is_complete) {
              setModelStatus({
                exists: true,
                isComplete: true,
                isDownloading: false,
                size: statusResult.size_mb ? `${statusResult.size_mb}MB` : '4.5GB',
                checking: false,
                downloading: false,
              });
            } else {
              // 继续检查下载状态
              setTimeout(checkDownloadStatus, 2000);
            }
          } else {
            // 检查是否还在下载
            setTimeout(checkDownloadStatus, 2000);
          }
        };

        setTimeout(checkDownloadStatus, 2000);
      } else {
        console.error('Download failed:', result.error);
        setModelStatus(prev => ({ ...prev, downloading: false }));
        alert(`下载失败: ${result.error}`);
      }
    } catch (error) {
      console.error('Download error:', error);
      setModelStatus(prev => ({ ...prev, downloading: false }));
      alert('下载过程中发生错误');
    }
  };

  const getStatusMessage = () => {
    if (modelStatus.checking) return '正在检查模型状态...';
    if (modelStatus.downloading) return '正在下载模型...';
    if (modelStatus.isDownloading) return '下载进行中...';
    if (modelStatus.exists && modelStatus.isComplete) return '模型已准备就绪';
    if (modelStatus.exists && !modelStatus.isComplete) return '模型文件不完整';
    return '模型未找到 - 请下载模型文件';
  };

  const getStatusColor = () => {
    if (modelStatus.checking || modelStatus.downloading || modelStatus.isDownloading) return 'text-blue-600';
    if (modelStatus.exists && modelStatus.isComplete) return 'text-green-600';
    return 'text-gray-500';
  };

  return (
    <div className="p-4 border rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <Cpu className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-medium">ImageBind Model</h4>
              {modelStatus.checking ? (
                <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
              ) : modelStatus.downloading || modelStatus.isDownloading ? (
                <Download className="w-4 h-4 animate-pulse text-blue-600" />
              ) : modelStatus.exists && modelStatus.isComplete ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <XCircle className="w-4 h-4 text-gray-500" />
              )}
            </div>
            <p className="text-xs text-gray-500">{modelStatus.size || '~4.5GB'} • Image Understanding</p>
            <p className={`text-sm ${getStatusColor()}`}>
              {getStatusMessage()}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={checkModelStatus}
            disabled={modelStatus.checking || modelStatus.downloading}
          >
            {modelStatus.checking ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            检查状态
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={downloadModel}
            disabled={modelStatus.downloading || (modelStatus.exists && modelStatus.isComplete)}
          >
            {modelStatus.downloading ? (
              <Download className="w-4 h-4 mr-2 animate-pulse" />
            ) : (
              <Download className="w-4 h-4 mr-2" />
            )}
            {modelStatus.exists && modelStatus.isComplete ? '已下载' : '下载模型'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default function Settings() {
  const [settings, setSettings] = useState<SettingsState>({
    openaiBaseUrl: '',
    openaiApiKey: '',
    processingModel: 'gpt-4o-mini',
    analysisModel: 'gpt-4o-mini',
    dashscopeApiKey: '',
    captionModel: 'qwen-vl-plus-latest',
    asrModel: 'paraformer-realtime-v2',
    storeDirectory: '',
    // ImageBind Model Configuration
    imagebindModelDirectory: '/app/models',
    selectedImagebindModel: 'huge',
    imagebindInstalled: false,
  });

  const [apiConfigStatus, setApiConfigStatus] = useState<
    'idle' | 'saving' | 'saved' | 'error'
  >('idle');

  // System initialization status
  const [systemInitialized, setSystemInitialized] = useState<boolean | null>(null);

  // Load settings and system status
  useEffect(() => {
    loadSettings();
    checkSystemStatus();
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await videoRAGApi.getSystemStatus();
      if (response.data.success) {
        setSystemInitialized(response.data.global_config_set || false);
      } else {
        setSystemInitialized(false);
      }
    } catch (error) {
      console.error('Failed to check system status:', error);
      setSystemInitialized(false);
    }
  };

  const loadSettings = async () => {
    try {
      // First, load default configuration from backend environment variables
      let defaultSettings: Partial<SettingsState> = {};
      try {
        const { videoRAGApi } = await import('../../services/api');
        const response = await videoRAGApi.getDefaultConfig();
        if (response.data.success && response.data.defaults) {
          defaultSettings = {
            openaiBaseUrl: response.data.defaults.openai_base_url,
            processingModel: response.data.defaults.processing_model,
            analysisModel: response.data.defaults.analysis_model,
            dashscopeApiKey: response.data.defaults.dashscope_api_key,
            captionModel: response.data.defaults.caption_model,
            asrModel: response.data.defaults.asr_model,
            storeDirectory: response.data.defaults.store_directory,
            imagebindModelDirectory: response.data.defaults.imagebind_model_directory,
            selectedImagebindModel: response.data.defaults.selected_imagebind_model,
          };
          console.log('✅ Loaded default settings from backend:', defaultSettings);
        } else {
          console.warn('⚠️ Failed to load default settings from backend:', response.data.error);
        }
      } catch (error) {
        console.warn('⚠️ Could not fetch default settings from backend:', error);
      }

      // Then, load user settings from localStorage
      const savedSettings = localStorage.getItem('videorag-settings');
      if (savedSettings) {
        const parsedSettings = JSON.parse(savedSettings);
        // Merge saved settings with defaults, with saved settings taking precedence
        setSettings(prevSettings => ({
          // Start with initial defaults
          ...prevSettings,
          // Apply backend defaults (don't override API keys)
          ...defaultSettings,
          // Apply user saved settings (this takes highest precedence)
          ...parsedSettings,
        }));
        console.log('✅ Loaded user settings from localStorage:', parsedSettings);
      } else {
        // No saved settings, use defaults
        setSettings(prevSettings => ({
          ...prevSettings,
          ...defaultSettings,
        }));
        console.log('✅ Using default settings from backend');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      // Fall back to default hardcoded values
      setSettings(prev => prev);
    }
  };

  const handleOpenaiChange = (field: string, value: string) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
  };

  const handleDashscopeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSettings((prev) => ({ ...prev, dashscopeApiKey: e.target.value }));
  };

  const handleModelChange = (field: string, value: string) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
  };

  const handleApiConfigSave = async () => {
    setApiConfigStatus('saving');
    try {
      // 准备配置数据
      const config = {
        openai_api_key: settings.openaiApiKey,
        openai_base_url: settings.openaiBaseUrl,
        ali_dashscope_api_key: settings.dashscopeApiKey,
        ali_dashscope_base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', // Fixed base URL
        analysisModel: settings.analysisModel,
        processingModel: settings.processingModel,
        caption_model: settings.captionModel,
        asr_model: settings.asrModel,
        image_bind_model_path: `${settings.imagebindModelDirectory}/imagebind.pth`,
        base_storage_path: settings.storeDirectory
      };

      // Step 1: Update system configuration (works for both initialized and non-initialized systems)
      try {
        let response;
        if (systemInitialized === false) {
          // System not initialized - use initialize API
          response = await videoRAGApi.initializeSystem(config);
          if (response.data.success) {
            console.log('✅ Global configuration initialized successfully');
            setSystemInitialized(true);
          } else {
            console.warn('⚠️ Global configuration initialization failed:', response.data.error);
          }
        } else {
          // System already initialized - use update API
          response = await videoRAGApi.updateSystemConfig(config);
          if (response.data.success) {
            console.log('✅ Global configuration updated successfully');
          } else {
            console.warn('⚠️ Global configuration update failed:', response.data.error);
          }
        }
      } catch (configError) {
        console.warn('⚠️ System configuration update failed:', configError);
        // Continue with localStorage save anyway
      }

      // Step 2: Save settings to localStorage
      localStorage.setItem('videorag-settings', JSON.stringify(settings));

      // Step 3: Trigger configuration update event (for any other components listening)
      if (settings.storeDirectory) {
        const event = new CustomEvent('storage-config-updated', {
          detail: { storeDirectory: settings.storeDirectory }
        });
        window.dispatchEvent(event);
      }

      setTimeout(() => setApiConfigStatus('idle'), 2000);
    } catch (error) {
      console.error('Failed to save API configuration:', error);
      setApiConfigStatus('error');
      setTimeout(() => setApiConfigStatus('idle'), 2000);
    }
  };

  const getApiConfigButtonText = () => {
    switch (apiConfigStatus) {
      case 'saving':
        return 'Saving...';
      case 'saved':
        return 'Saved!';
      case 'error':
        return 'Save Configuration';
      default:
        return 'Save Configuration';
    }
  };

  const getApiConfigButtonIcon = () => {
    switch (apiConfigStatus) {
      case 'saving':
        return <RefreshCw className="animate-spin" size={16} />;
      case 'saved':
        return <CheckCircle className="text-green-600" size={16} />;
      case 'error':
        return <XCircle className="text-red-600" size={16} />;
      default:
        return <Key size={16} />;
    }
  };

  // Reset system configuration
  const resetSystemConfiguration = async () => {
    const confirmed = window.confirm(
      '这将重置所有系统配置并清除localStorage中的设置。您需要重新配置API密钥和存储路径。确定要继续吗？'
    );

    if (!confirmed) return;

    try {
      // Clear local settings
      localStorage.removeItem('videorag-settings');
      setSystemInitialized(false);
      // Redirect to the root path for initialization wizard
      window.location.href = '/';
    } catch (error) {
      console.error('Failed to restart initialization wizard:', error);
      alert('Failed to restart setup wizard. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16">
            <Link to="/" className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
              <ArrowLeft className="w-4 h-4" />
              返回
            </Link>
            <div className="ml-4 flex items-center">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Key className="w-4 h-4 text-primary-foreground" />
              </div>
              <h1 className="text-xl font-semibold ml-3">设置</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-2">
            <h2 className="text-3xl font-bold tracking-tight">VideoRAG 设置</h2>
            <p className="text-muted-foreground">
              配置你的 AI 模型和视频处理偏好设置。
            </p>
          </div>

          {/* API Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                  <Key size={20} />
                </div>
                <div>
                  <CardTitle>API 配置</CardTitle>
                  <CardDescription>
                    配置外部服务的 API 密钥
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* OpenAI Configuration */}
              <div className="space-y-4 p-4 border rounded-lg bg-gray-50/50">
                <h3 className="text-lg font-semibold text-gray-800">OpenAI 配置</h3>
                <p className="text-sm text-gray-600">配置 OpenAI API 用于语言模型服务</p>

                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium block mb-2">
                      基础 URL
                    </label>
                    <input
                      type="text"
                      placeholder="https://api.openai.com/v1"
                      value={settings.openaiBaseUrl}
                      onChange={(e) => handleOpenaiChange('openaiBaseUrl', e.target.value)}
                      className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium block mb-2">
                      API 密钥
                    </label>
                    <input
                      type="password"
                      placeholder="sk-..."
                      value={settings.openaiApiKey}
                      onChange={(e) => handleOpenaiChange('openaiApiKey', e.target.value)}
                      className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium block mb-2">
                        处理模型
                      </label>
                      <input
                        type="text"
                        value={settings.processingModel}
                        onChange={(e) => handleOpenaiChange('processingModel', e.target.value)}
                        className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., gpt-4o-mini, gpt-4o"
                      />
                      <p className="text-xs text-gray-500 mt-1">用于高容量预处理任务的模型</p>
                    </div>

                    <div>
                      <label className="text-sm font-medium block mb-2">
                        分析模型
                      </label>
                      <input
                        type="text"
                        value={settings.analysisModel}
                        onChange={(e) => handleOpenaiChange('analysisModel', e.target.value)}
                        className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., gpt-4o-mini, gpt-4o"
                      />
                      <p className="text-xs text-gray-500 mt-1">用于详细分析任务的模型</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* DashScope Configuration */}
              <div className="space-y-4 p-4 border rounded-lg bg-orange-50/50">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">DashScope 配置</h3>
                    <p className="text-sm text-gray-600">配置阿里云 DashScope API 用于视频描述</p>
                  </div>
                  <a
                    href="https://www.alibabacloud.com/help/en/model-studio/get-api-key?spm=a2c63.p38356.0.i1"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                  >
                    <ExternalLink size={14} />
                    获取 API 密钥
                  </a>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium block mb-2">
                      DashScope API 密钥
                    </label>
                    <input
                      type="password"
                      placeholder="sk-..."
                      value={settings.dashscopeApiKey}
                      onChange={handleDashscopeChange}
                      className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium block mb-2">
                        描述模型
                      </label>
                      <input
                        type="text"
                        value={settings.captionModel}
                        onChange={(e) => handleModelChange('captionModel', e.target.value)}
                        className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="e.g., qwen-vl-plus-latest, qwen-vl-plus"
                      />
                      <p className="text-xs text-gray-500 mt-1">用于视频描述的 AI 模型</p>
                    </div>

                    <div>
                      <label className="text-sm font-medium block mb-2">
                        ASR 模型 (本地离线)
                      </label>
                      <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-md border">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-gray-600 font-medium">
                          faster-whisper-large-v3
                        </span>
                        <span className="text-xs text-gray-400 ml-auto">
                          CPU 离线推理
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        使用本地 Whiper 模型，支持中英文等多语言语音识别，完全离线无需网络
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <p className="text-xs text-muted-foreground">
                所有 API 密钥均存储在本地，不会共享给第三方
              </p>
            </CardContent>
          </Card>

          {/* AI Model Status */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                  <Download size={20} />
                </div>
                <div>
                  <CardTitle>AI 模型状态</CardTitle>
                  <CardDescription>
                    检查 ImageBind 模型状态
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <ModelStatusSection
                storeDirectory={settings.storeDirectory}
                imagebindModelDirectory={settings.imagebindModelDirectory}
              />
            </CardContent>
          </Card>

          {/* File System Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
                  <FolderOpen size={20} />
                </div>
                <div>
                  <CardTitle>文件系统</CardTitle>
                  <CardDescription>
                    配置文件存储和临时目录
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-2">
                  数据存储目录
                </label>
                <input
                  type="text"
                  placeholder="模型和缓存数据存储路径"
                  value={settings.storeDirectory}
                  onChange={(e) => setSettings(prev => ({ ...prev, storeDirectory: e.target.value }))}
                  className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  用于存储视频文件和处理结果
                </p>
              </div>

              <div>
                <label className="text-sm font-medium block mb-2">
                  ImageBind 模型目录
                </label>
                <input
                  type="text"
                  placeholder="/app/models (Docker挂载目录)"
                  value={settings.imagebindModelDirectory}
                  onChange={(e) => setSettings(prev => ({ ...prev, imagebindModelDirectory: e.target.value }))}
                  className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  指定 ImageBind 模型的下载和存储目录，建议使用 Docker 挂载目录以实现持久化
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Chat History Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-green-100 text-green-600">
                  <MessageSquare size={20} />
                </div>
                <div>
                  <CardTitle>对话历史</CardTitle>
                  <CardDescription>
                    配置对话消息的保存和恢复设置
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle className="text-green-600 mt-0.5" size={16} />
                <div className="text-sm">
                  <p className="font-medium text-green-800">
                    对话历史已启用
                  </p>
                  <p className="text-green-700 mt-1">
                    您的对话消息会被自动保存到浏览器本地存储中，即使刷新页面也不会丢失。
                    每个对话会话的消息都是独立的，可以自由切换和查看。
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4">
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <div className="font-medium">自动保存</div>
                    <div className="text-sm text-muted-foreground">
                      发送消息后自动保存对话历史
                    </div>
                  </div>
                  <div className="text-green-600">
                    <CheckCircle size={20} />
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <div className="font-medium">本地存储</div>
                    <div className="text-sm text-muted-foreground">
                      使用浏览器 localStorage 保存数据
                    </div>
                  </div>
                  <div className="text-green-600">
                    <CheckCircle size={20} />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Setup Wizard */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600">
                  <SettingsIcon size={20} />
                </div>
                <div>
                  <CardTitle>重置配置</CardTitle>
                  <CardDescription>
                    重置所有系统配置和本地设置（API密钥、存储路径等）
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <AlertCircle className="text-blue-600 mt-0.5" size={16} />
                <div className="text-sm">
                  <p className="font-medium text-blue-800">
                    设置向导
                  </p>
                  <p className="text-blue-700 mt-1">
                    清除所有配置并返回初始状态，需要重新设置。
                  </p>
                </div>
              </div>

              <div className="flex justify-start">
                <Button
                  onClick={resetSystemConfiguration}
                  variant="outline"
                  className="px-6 py-2"
                >
                  <SettingsIcon className="w-4 h-4 mr-2" />
                  重置系统配置
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Global Save Button */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  保存所有配置更改到系统和本地存储
                </div>
                <Button
                  onClick={handleApiConfigSave}
                  disabled={apiConfigStatus === 'saving'}
                  className="px-6"
                >
                  {getApiConfigButtonIcon()}
                  <span className="ml-2">{getApiConfigButtonText()}</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}