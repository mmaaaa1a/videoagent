import React, { useState, useCallback } from 'react'
import { Upload, X, FileVideo, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { validateVideoFile, formatFileSize, getVideoThumbnail } from '../lib/utils'
import { videoRAGApi } from '../services/api'
import { toast } from 'sonner'

interface VideoFile {
  id: string
  file: File
  name: string
  size: number
  duration?: number
  thumbnail?: string
  status: 'pending' | 'checking' | 'valid' | 'invalid'
  error?: string
}

interface VideoUploadProps {
  chatId: string
  onUploadComplete?: (chatId: string) => void
  disabled?: boolean
}

export default function VideoUpload({ chatId, onUploadComplete, disabled = false }: VideoUploadProps) {
  const [videos, setVideos] = useState<VideoFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    if (disabled) return

    const files = Array.from(e.dataTransfer.files).filter(file =>
      file.type.startsWith('video/')
    )

    handleFiles(files)
  }, [disabled])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled || !e.target.files) return

    const files = Array.from(e.target.files)
    handleFiles(files)
  }, [disabled])

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
        // Generate thumbnail
        const thumbnail = await getVideoThumbnail(file)
        videoFile.thumbnail = thumbnail

        // Get video duration (this would need backend API call in real implementation)
        videoFile.status = 'valid'
      } catch (error) {
        videoFile.status = 'invalid'
        videoFile.error = '无法读取视频文件'
        console.error('Failed to process video:', error)
      }

      newVideos.push(videoFile)
    }

    setVideos(prev => [...prev, ...newVideos])
  }

  const removeVideo = useCallback((id: string) => {
    setVideos(prev => prev.filter(video => video.id !== id))
  }, [])

  const handleUpload = async () => {
    if (videos.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Create file paths (in real implementation, these would be uploaded to server)
      const videoPaths = videos.map(video => `/uploads/${chatId}/${video.name}`)

      // Upload videos via API
      const response = await videoRAGApi.uploadVideos(chatId, videoPaths)

      if (response.data.success) {
        toast.success(`成功上传 ${videos.length} 个视频文件`)
        setVideos([])
        onUploadComplete?.(chatId)
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

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="w-5 h-5" />
          上传视频文件
        </CardTitle>
        <CardDescription>
          支持MP4、WebM、OGG等格式，单个文件最大2GB。可同时上传多个视频。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Upload Area */}
        <div
          className={`upload-area p-8 text-center cursor-pointer transition-all ${
            isDragOver ? 'drag-over' : ''
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

        {/* Video List */}
        {videos.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">已选择的视频 ({validVideos.length})</h3>
              <p className="text-sm text-muted-foreground">
                总大小: {formatFileSize(totalSize)}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  {/* Thumbnail */}
                  {video.thumbnail ? (
                    <img
                      src={video.thumbnail}
                      alt={video.name}
                      className="w-16 h-12 object-cover rounded"
                    />
                  ) : (
                    <FileVideo className="w-16 h-12 text-muted-foreground" />
                  )}

                  {/* Video Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{video.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatFileSize(video.size)}
                    </p>
                    {video.error && (
                      <p className="text-xs text-red-600">{video.error}</p>
                    )}
                  </div>

                  {/* Status & Actions */}
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
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeVideo(video.id)}
                      disabled={isUploading}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {/* Upload Button */}
            <div className="flex justify-end">
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
                    开始上传
                  </>
                )}
              </Button>
            </div>

            {/* Progress Bar */}
            {isUploading && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}