import React from 'react'
import { CheckCircle, Circle, Loader2 } from 'lucide-react'
import { Progress } from './ui/progress'
import { ProcessingStage, getStageByKey } from '../types/video'
import { cn } from '../lib/utils'

interface MultiStageProgressProps {
  currentStage: string
  stages: ProcessingStage[]
  overallProgress?: number
  showLabels?: boolean
  showDescriptions?: boolean
  compact?: boolean
  className?: string
}

export default function MultiStageProgress({
  currentStage,
  stages,
  overallProgress = 0,
  showLabels = true,
  showDescriptions = false,
  compact = false,
  className
}: MultiStageProgressProps) {
  const currentStageIndex = stages.findIndex(stage => stage.key === currentStage)
  const currentStageInfo = getStageByKey(currentStage)

  // 计算整体进度（基于阶段权重）
  const calculateProgress = () => {
    if (currentStageIndex === -1) return 0

    let totalWeight = 0
    let completedWeight = 0

    for (let i = 0; i < stages.length; i++) {
      totalWeight += stages[i].weight
      if (i < currentStageIndex) {
        completedWeight += stages[i].weight
      }
    }

    return Math.round((completedWeight / totalWeight) * 100)
  }

  const progress = calculateProgress()

  return (
    <div className={cn("space-y-4", className)}>
      {/* 总体进度条 */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">总体进度</span>
          <span className="text-sm text-muted-foreground">{progress}%</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* 阶段进度 */}
      <div className="space-y-3">
        {stages.map((stage, index) => {
          const isActive = currentStage === stage.key
          const isCompleted = index < currentStageIndex
          const isPending = index > currentStageIndex

          return (
            <div
              key={stage.key}
              className={cn(
                "flex items-center gap-3",
                compact && "gap-2"
              )}
            >
              {/* 阶段图标 */}
              <div className="flex-shrink-0">
                {isCompleted ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : isActive ? (
                  <div className="relative">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    <div className="absolute inset-0 w-5 h-5 animate-ping bg-blue-600 rounded-full opacity-20" />
                  </div>
                ) : (
                  <Circle className="w-5 h-5 text-gray-400" />
                )}
              </div>

              {/* 阶段信息 */}
              <div className="flex-1 min-w-0">
                <div className={cn(
                  "flex items-center gap-2",
                  compact && "gap-1"
                )}>
                  <span className="text-lg">{stage.icon}</span>
                  {showLabels && (
                    <span className={cn(
                      "font-medium text-sm",
                      isActive && "text-blue-700",
                      isCompleted && "text-green-600",
                      isPending && "text-gray-500"
                    )}>
                      {stage.label}
                    </span>
                  )}
                </div>

                {showDescriptions && !compact && (
                  <p className={cn(
                    "text-xs mt-1",
                    isActive && "text-blue-600",
                    isCompleted && "text-green-600",
                    isPending && "text-gray-500"
                  )}>
                    {stage.description}
                  </p>
                )}

                {isActive && currentStageInfo && (
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-1">
                      <div className="bg-blue-600 h-1 rounded-full animate-pulse" />
                    </div>
                    <span className="text-xs text-blue-600">处理中...</span>
                  </div>
                )}
              </div>

              {/* 阶段权重指示 */}
              {!compact && (
                <div className="text-xs text-muted-foreground">
                  {stage.weight}%
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* 当前阶段详细信息 */}
      {currentStageInfo && !compact && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">{currentStageInfo.icon}</span>
            <h4 className="font-medium text-blue-900">
              {currentStageInfo.label}
            </h4>
          </div>
          <p className="text-sm text-blue-700">
            {currentStageInfo.description}
          </p>
        </div>
      )}
    </div>
  )
}

// 连接式进度条组件
export function ConnectedProgress({
  currentStage,
  stages,
  className
}: {
  currentStage: string
  stages: ProcessingStage[]
  className?: string
}) {
  const currentStageIndex = stages.findIndex(stage => stage.key === currentStage)

  return (
    <div className={cn("relative", className)}>
      {/* 连接线 */}
      <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-gray-200" />

      {/* 阶段列表 */}
      <div className="space-y-6">
        {stages.map((stage, index) => {
          const isActive = currentStage === stage.key
          const isCompleted = index < currentStageIndex
          const isPending = index > currentStageIndex

          return (
            <div key={stage.key} className="flex items-center gap-4">
              {/* 阶段圆点 */}
              <div className="relative z-10">
                <div className={cn(
                  "w-12 h-12 rounded-full flex items-center justify-center text-lg font-medium transition-all",
                  isCompleted && "bg-green-600 text-white",
                  isActive && "bg-blue-600 text-white ring-4 ring-blue-100",
                  isPending && "bg-gray-200 text-gray-500"
                )}>
                  {isCompleted ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : isActive ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <span>{stage.icon}</span>
                  )}
                </div>
              </div>

              {/* 阶段信息 */}
              <div className="flex-1">
                <h4 className={cn(
                  "font-medium",
                  isActive && "text-blue-700",
                  isCompleted && "text-green-600",
                  isPending && "text-gray-500"
                )}>
                  {stage.label}
                </h4>
                <p className="text-sm text-gray-600 mt-1">
                  {stage.description}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}