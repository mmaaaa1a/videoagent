import React, { useState, useCallback } from 'react'
import {
  Upload,
  X,
  FileVideo,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Plus,
  Folder,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { validateVideoFile, formatFileSize, getVideoThumbnail } from '../lib/utils'
import { videoRAGApi } from '../services/api'
import { toast } from 'sonner'
import VideoProcessingItem from './VideoProcessingItem'
import BatchProcessingProgress from './BatchProcessingProgress'
import FolderUpload from './FolderUpload'
import { useBatchProcessingStatus } from '../hooks/useBatchProcessingStatus'
import {
  VideoFile,
  VideoProcessingItem as VideoProcessingItemType,
  FileWithPath,
  FolderUploadResult
} from '../types/video'

interface VideoUploadProps {
  chatId: string
  onUploadComplete?: (chatId: string) => void
  disabled?: boolean
}

export default function VideoUpload({ chatId, onUploadComplete, disabled = false }: VideoUploadProps) {
  const [videos, setVideos] = useState<VideoFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadMode, setUploadMode] = useState<'files' | 'folder'>('files')
  const [showBatchProgress, setShowBatchProgress] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)

  // 批量处理状态管理
  const {
    batchState,
    isLoading,
    error,
    pauseProcessing,
    resumeProcessing,
    retryVideo,
    removeVideo,
    updateVideos,
    initializeProcessing
  } = useBatchProcessingStatus({
    chatId,
    totalVideos: videos.length,
    onVideoCompleted: (video) => {
      console.log('Video completed:', video)
    },
    onBatchCompleted: () => {
      toast.success('所有视频处理完成！')
      onUploadComplete?.(chatId)
      setVideos([])
      setShowBatchProgress(false)
    },
    onError: (error) => {
      toast.error(`处理出错: ${error}`)
    },
    enabled: showBatchProgress
  })

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()

    if (disabled || uploadMode === 'folder') return

    const files = Array.from(e.dataTransfer.files).filter(file =>
      file.type.startsWith('video/')
    )

    handleFiles(files)
  }, [disabled, uploadMode])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled || !e.target.files || uploadMode === 'folder') return

    const files = Array.from(e.target.files)
    handleFiles(files)
  }, [disabled, uploadMode])

  const retryThumbnail = useCallback(async (videoId: string) => {
    setVideos(prev => prev.map(video => {
      if (video.id === videoId) {
        return { ...video, status: 'checking' as const, retryCount: (video.retryCount || 0) + 1 }
      }
      return video
    }))

    const videoFile = videos.find(v => v.id === videoId)
    if (!videoFile) return

    try {
      const thumbnail = await getVideoThumbnail(videoFile.file)
      setVideos(prev => prev.map(video => {
        if (video.id === videoId) {
          return {
            ...video,
            thumbnail,
            status: 'valid' as const,
            error: undefined
          }
        }
        return video
      }))
      toast.success(`${videoFile.name} 的缩略图生成成功`)
    } catch (error) {
      setVideos(prev => prev.map(video => {
        if (video.id === videoId) {
          return {
            ...video,
            status: 'valid' as const,
            error: `重试失败，但视频可以正常上传`
          }
        }
        return video
      }))
      console.warn('缩略图重试失败:', error)
      toast.warning(`${videoFile.name} 的缩略图再次生成失败，但仍可正常上传`)
    }
  }, [videos])

  const handleFiles = async (files: File[]) => {
    const newVideos: VideoFile[] = []

    for (const file of files) {
      if (!validateVideoFile(file)) {
        toast.error(`文件 ${file.name} 格式不支持或超过2GB限制`)
        continue
      }

      const videoFile: VideoFile = {
        id: Math.random().toString(36).substring(7),
        file,
        name: file.name,
        size: file.size,
        status: 'checking'
      }

      try {
        // 尝试生成缩略图
        const thumbnail = await getVideoThumbnail(file)
        videoFile.thumbnail = thumbnail
        videoFile.status = 'valid'
      } catch (error) {
        console.warn('缩略图生成失败，但视频仍可上传:', error)
        videoFile.thumbnail = undefined
        videoFile.status = 'valid'
        videoFile.error = '缩略图生成失败，但视频可以正常上传'
        toast.warning(`${file.name} 的缩略图生成失败，但仍可正常上传和处理`)
      }

      newVideos.push(videoFile)
    }

    setVideos(prev => [...prev, ...newVideos])
  }

  const removeVideoFromList = useCallback((id: string) => {
    setVideos(prev => prev.filter(video => video.id !== id))
  }, [])

  // 处理文件夹上传
  const handleFolderSelect = useCallback((result: FolderUploadResult) => {
    const newVideos: VideoFile[] = []

    result.files.forEach(({ file, relativePath }) => {
      if (!validateVideoFile(file)) {
        toast.error(`文件 ${file.name} 格式不支持或超过2GB限制`)
        return
      }

      const videoFile: VideoFile = {
        id: Math.random().toString(36).substring(7),
        file,
        name: file.name,
        size: file.size,
        status: 'valid', // 文件夹上传时直接设为有效，不生成缩略图以提高性能
        relativePath
      }

      newVideos.push(videoFile)
    })

    setVideos(prev => [...prev, ...newVideos])
    toast.success(`已添加 ${result.videoCount} 个视频文件`)
  }, [])

  const handleUpload = async () => {
    if (videos.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // 转换为VideoProcessingItem格式
      const processingVideos: VideoProcessingItemType[] = videos.map(video => ({
        id: video.id,
        name: video.name,
        path: `/uploads/${chatId}/${video.name}`,
        size: video.size,
        duration: video.duration,
        thumbnail: video.thumbnail,
        status: 'pending' as const,
        progress: 0,
        file: video.file
      }))

      // 初始化批量处理状态
      updateVideos(processingVideos)

      // 创建文件路径
      const videoPaths = processingVideos.map(video => video.path)

      // 上传视频
      const response = await videoRAGApi.uploadVideosWeb(chatId, videoPaths)

      if (response.data.success) {
        toast.success(`成功提交 ${videos.length} 个视频文件进行处理`)
        setShowBatchProgress(true)
        initializeProcessing(processingVideos)
      } else {
        toast.error(response.data.error || '上传失败')
      }
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('上传失败，请重试')
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const validVideos = videos.filter(v => v.status === 'valid')
  const totalSize = validVideos.reduce((acc, video) => acc + video.size, 0)

  // 如果显示批量处理进度，直接返回进度组件
  if (showBatchProgress) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">视频处理进度</h2>
          <Button
            variant="outline"
            onClick={() => {
              setShowBatchProgress(false)
              setVideos([])
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            添加更多视频
          </Button>
        </div>

        <BatchProcessingProgress
          batchState={batchState}
          onRetryVideo={retryVideo}
          onRemoveVideo={removeVideo}
          onPause={pauseProcessing}
          onResume={resumeProcessing}
        />

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-4 h-4" />
              <span className="font-medium">错误: {error}</span>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            上传视频文件
          </CardTitle>
          <CardDescription>
            支持MP4、WebM、OGG等格式，单个文件最大2GB。可选择多个文件或整个文件夹。
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* 上传模式选择 */}
          <Tabs value={uploadMode} onValueChange={(value) => setUploadMode(value as 'files' | 'folder')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="files" className="flex items-center gap-2">
                <FileVideo className="w-4 h-4" />
                文件上传
              </TabsTrigger>
              <TabsTrigger value="folder" className="flex items-center gap-2">
                <Folder className="w-4 h-4" />
                文件夹上传
              </TabsTrigger>
            </TabsList>

            <TabsContent value="files" className="space-y-6">
              {/* 文件上传区域 */}
              <div
                className={`upload-area p-8 text-center cursor-pointer transition-all border-2 border-dashed rounded-lg ${
                  isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !disabled && document.getElementById('file-input')?.click()}
              >
                <input
                  id="file-input"
                  type="file"
                  multiple
                  accept="video/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={disabled}
                />

                <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">
                  {isDragOver ? '释放文件以上传' : '拖拽视频文件到此处'}
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  或点击选择文件
                </p>
                <Button variant="outline" disabled={disabled}>
                  选择视频文件
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="folder" className="space-y-6">
              {/* 文件夹上传组件 */}
              <FolderUpload
                onFolderSelect={handleFolderSelect}
                disabled={disabled}
              />
            </TabsContent>
          </Tabs>

          {/* 视频列表 */}
          {videos.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">
                  已选择的视频 ({validVideos.length})
                </h3>
                <div className="flex items-center gap-4">
                  <p className="text-sm text-muted-foreground">
                    总大小: {formatFileSize(totalSize)}
                  </p>
                  {videos.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setVideos([])}
                      disabled={isUploading}
                    >
                      <X className="w-4 h-4 mr-1" />
                      清空列表
                    </Button>
                  )}
                </div>
              </div>

              <div className="space-y-3 max-h-64 overflow-y-auto">
                {videos.map((video) => (
                  <div
                    key={video.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border ${
                      video.status === 'valid'
                        ? 'border-green-200 bg-green-50'
                        : video.status === 'invalid'
                        ? 'border-red-200 bg-red-50'
                        : 'border-gray-200'
                    }`}
                  >
                    {/* 缩略图 */}
                    {video.thumbnail ? (
                      <img
                        src={video.thumbnail}
                        alt={video.name}
                        className="w-16 h-12 object-cover rounded"
                      />
                    ) : (
                      <FileVideo className="w-16 h-12 text-muted-foreground" />
                    )}

                    {/* 视频信息 */}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{video.name}</p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{formatFileSize(video.size)}</span>
                        {video.relativePath && (
                          <span className="text-xs">路径: {video.relativePath}</span>
                        )}
                      </div>
                      {video.error && (
                        <p className="text-xs text-red-600">{video.error}</p>
                      )}
                    </div>

                    {/* 状态和操作 */}
                    <div className="flex items-center gap-2">
                      {video.status === 'checking' && (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      )}
                      {video.status === 'valid' && (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      )}
                      {video.status === 'invalid' && (
                        <AlertCircle className="w-4 h-4 text-red-600" />
                      )}
                      {video.error && video.error.includes('缩略图生成失败') && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => retryThumbnail(video.id)}
                          disabled={isUploading || video.status === 'checking'}
                          title={`重试生成缩略图 (已尝试 ${video.retryCount || 1} 次)`}
                        >
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeVideoFromList(video.id)}
                        disabled={isUploading}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {/* 上传按钮 */}
              <div className="flex justify-between items-center pt-4 border-t">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <BarChart3 className="w-4 h-4" />
                  批量处理模式已启用
                </div>
                <Button
                  onClick={handleUpload}
                  disabled={validVideos.length === 0 || isUploading || disabled}
                  className="min-w-32"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      上传中... ({uploadProgress}%)
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      开始处理 {validVideos.length} 个视频
                    </>
                  )}
                </Button>
              </div>

              {/* 上传进度条 */}
              {isUploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>上传进度</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}