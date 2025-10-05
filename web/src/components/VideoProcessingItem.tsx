import React, { useState } from 'react'
import {
  FileVideo,
  CheckCircle,
  AlertCircle,
  Clock,
  Loader2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  X
} from 'lucide-react'
import { Card, CardContent } from './ui/card'
import { Button } from './ui/button'
import { Progress } from './ui/progress'
import {
  VideoProcessingItem as VideoProcessingItemType,
  ProcessingStage,
  PROCESSING_STAGES,
  getStageByKey,
  formatProcessingTime
} from '../types/video'
import { cn } from '../lib/utils'

interface VideoProcessingItemProps {
  video: VideoProcessingItemType
  isExpanded?: boolean
  onToggleExpand?: () => void
  onRetry?: (videoId: string) => void
  onRemove?: (videoId: string) => void
  className?: string
}

export default function VideoProcessingItem({
  video,
  isExpanded = false,
  onToggleExpand,
  onRetry,
  onRemove,
  className
}: VideoProcessingItemProps) {
  const [expanded, setExpanded] = useState(isExpanded)
  const currentStage = getStageByKey(video.currentStage || '')

  const handleToggleExpand = () => {
    const newExpanded = !expanded
    setExpanded(newExpanded)
    onToggleExpand?.()
  }

  const getStatusIcon = () => {
    switch (video.status) {
      case 'processing':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-600" />
      case 'skipped':
        return <X className="w-5 h-5 text-gray-400" />
      default:
        return <Clock className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusColor = () => {
    switch (video.status) {
      case 'processing':
        return 'border-blue-200 bg-blue-50'
      case 'completed':
        return 'border-green-200 bg-green-50'
      case 'error':
        return 'border-red-200 bg-red-50'
      case 'skipped':
        return 'border-gray-200 bg-gray-50'
      default:
        return 'border-gray-200 bg-white'
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getProcessingTime = () => {
    if (video.startTime) {
      const endTime = video.completedTime || new Date()
      const processingTime = (endTime.getTime() - video.startTime.getTime()) / 1000
      return formatProcessingTime(processingTime)
    }
    return null
  }

  const getProgressPercentage = () => {
    if (video.status === 'completed') return 100
    if (video.status === 'error' || video.status === 'skipped') return 0
    if (video.currentStage) {
      return video.progress
    }
    return 0
  }

  return (
    <Card className={cn("transition-all duration-200", getStatusColor(), className)}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          {/* 视频缩略图或图标 */}
          <div className="flex-shrink-0">
            {video.thumbnail ? (
              <img
                src={video.thumbnail}
                alt={video.name}
                className="w-16 h-12 object-cover rounded"
              />
            ) : (
              <div className="w-16 h-12 bg-gray-100 rounded flex items-center justify-center">
                <FileVideo className="w-6 h-6 text-gray-400" />
              </div>
            )}
          </div>

          {/* 视频信息 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {getStatusIcon()}
              <h4 className="font-medium text-gray-900 truncate">{video.name}</h4>
              {video.retryCount && video.retryCount > 0 && (
                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                  重试 {video.retryCount}
                </span>
              )}
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>{formatFileSize(video.size)}</span>
              {video.duration && (
                <span>时长: {formatProcessingTime(video.duration)}</span>
              )}
              {getProcessingTime() && (
                <span>处理: {getProcessingTime()}</span>
              )}
            </div>

            {/* 当前处理阶段 */}
            {video.status === 'processing' && currentStage && (
              <div className="flex items-center gap-2 mt-2">
                <span className="text-lg">{currentStage.icon}</span>
                <span className="text-sm font-medium text-blue-700">
                  {currentStage.label}
                </span>
              </div>
            )}

            {/* 错误信息 */}
            {video.status === 'error' && video.error && (
              <div className="text-sm text-red-600 mt-1">
                {video.error}
              </div>
            )}

            {/* 进度条 */}
            {(video.status === 'processing' || video.status === 'completed') && (
              <div className="mt-2">
                <Progress
                  value={getProgressPercentage()}
                  className="h-2"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>{getProgressPercentage()}%</span>
                  {video.status === 'completed' && (
                    <span>完成</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 操作按钮 */}
          <div className="flex items-center gap-1">
            {video.status === 'error' && onRetry && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onRetry(video.id)}
                title="重试处理"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            )}

            {(video.status === 'error' || video.status === 'skipped') && onRemove && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onRemove(video.id)}
                title="移除视频"
              >
                <X className="w-4 h-4" />
              </Button>
            )}

            {/* 展开/折叠按钮 */}
            {(video.status === 'processing' || video.status === 'error') && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleToggleExpand}
                title={expanded ? "收起详情" : "查看详情"}
              >
                {expanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </Button>
            )}
          </div>
        </div>

        {/* 展开的详细信息 */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="space-y-3">
              {/* 处理阶段详情 */}
              <div>
                <h5 className="font-medium text-sm mb-2">处理阶段</h5>
                <div className="space-y-1">
                  {PROCESSING_STAGES.map((stage, index) => {
                    const isCurrentStage = video.currentStage === stage.key
                    const isCompleted = video.status === 'completed' ||
                      (PROCESSING_STAGES.findIndex(s => s.key === video.currentStage) > index)

                    return (
                      <div
                        key={stage.key}
                        className={cn(
                          "flex items-center gap-2 text-sm p-2 rounded",
                          isCurrentStage && "bg-blue-50 border border-blue-200",
                          isCompleted && !isCurrentStage && "text-green-600",
                          !isCompleted && !isCurrentStage && "text-gray-400"
                        )}
                      >
                        <span className="text-base">{stage.icon}</span>
                        <span className="flex-1">{stage.label}</span>
                        {isCurrentStage && (
                          <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
                        )}
                        {isCompleted && !isCurrentStage && (
                          <CheckCircle className="w-3 h-3 text-green-600" />
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* 时间信息 */}
              {video.startTime && (
                <div>
                  <h5 className="font-medium text-sm mb-2">时间信息</h5>
                  <div className="text-sm text-gray-600 space-y-1">
                    <div>开始时间: {video.startTime.toLocaleString()}</div>
                    {video.completedTime && (
                      <div>完成时间: {video.completedTime.toLocaleString()}</div>
                    )}
                    {getProcessingTime() && (
                      <div>处理耗时: {getProcessingTime()}</div>
                    )}
                  </div>
                </div>
              )}

              {/* 详细错误信息 */}
              {video.status === 'error' && video.error && (
                <div>
                  <h5 className="font-medium text-sm mb-2">错误详情</h5>
                  <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                    {video.error}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}