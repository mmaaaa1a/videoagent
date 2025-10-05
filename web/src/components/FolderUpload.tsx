import React, { useState, useCallback } from 'react'
import {
  Upload,
  Folder,
  FileVideo,
  X,
  CheckCircle,
  AlertTriangle,
  Filter,
  ChevronDown,
  ChevronUp,
  FileText,
  Image,
  Music
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import {
  FileWithPath,
  FolderUploadResult
} from '../types/video'
import { toast } from 'sonner'
import { cn } from '../lib/utils'

interface FolderUploadProps {
  onFolderSelect: (result: FolderUploadResult) => void
  disabled?: boolean
  maxTotalSize?: number // bytes
  acceptedFormats?: string[]
  className?: string
}

const VIDEO_FORMATS = [
  '.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v', '.3gp'
]

const DEFAULT_MAX_SIZE = 10 * 1024 * 1024 * 1024 // 10GB

export default function FolderUpload({
  onFolderSelect,
  disabled = false,
  maxTotalSize = DEFAULT_MAX_SIZE,
  acceptedFormats = VIDEO_FORMATS,
  className
}: FolderUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [isScanning, setIsScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)
  const [scanResult, setScanResult] = useState<FolderUploadResult | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  // 检查文件是否为视频格式
  const isVideoFile = (file: File): boolean => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()
    return acceptedFormats.includes(extension)
  }

  // 递归扫描文件夹结构
  const scanFileStructure = async (items: DataTransferItemList): Promise<FileWithPath[]> => {
    const files: FileWithPath[] = []
    let processedCount = 0
    let totalCount = 0

    // 首先计算总数
    const countItems = async (items: DataTransferItemList): Promise<number> => {
      let count = 0
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.kind === 'file') {
          const entry = item.webkitGetAsEntry?.()
          if (entry) {
            if (entry.isFile) {
              count++
            } else if (entry.isDirectory) {
              const dirReader = (entry as FileSystemDirectoryEntry).createReader()
              const entries = await new Promise<FileSystemEntry[]>((resolve) => {
                dirReader.readEntries(resolve)
              })
              count += await countItems(entries as any)
            }
          }
        }
      }
      return count
    }

    // 递归处理项目
    const processItem = async (
      item: DataTransferItem,
      relativePath: string = ''
    ): Promise<void> => {
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry?.()
        if (!entry) return

        if (entry.isFile) {
          const file = await new Promise<File>((resolve, reject) => {
            (entry as FileSystemFileEntry).file(resolve, reject)
          })

          if (isVideoFile(file)) {
            files.push({
              file,
              path: file.name,
              relativePath: relativePath ? `${relativePath}/${file.name}` : file.name
            })
          }

          processedCount++
          setScanProgress(Math.round((processedCount / totalCount) * 100))

        } else if (entry.isDirectory) {
          const dirReader = (entry as FileSystemDirectoryEntry).createReader()
          const entries = await new Promise<FileSystemEntry[]>((resolve) => {
            dirReader.readEntries(resolve)
          })

          await Promise.all(
            entries.map(subEntry =>
              processItem(
                { kind: 'file', getAsEntry: () => subEntry } as any,
                relativePath ? `${relativePath}/${entry.name}` : entry.name
              )
            )
          )
        }
      }
    }

    try {
      totalCount = await countItems(items)
      setScanProgress(0)

      await Promise.all(
        Array.from(items).map(item => processItem(item))
      )

    } catch (error) {
      console.error('Error scanning file structure:', error)
      throw new Error('文件夹扫描失败')
    }

    return files
  }

  // 处理文件选择
  const handleFileSelect = useCallback(async (files: FileList | File[]) => {
    if (disabled) return

    setIsScanning(true)
    setScanProgress(0)

    try {
      const fileArray = Array.from(files)

      // 过滤视频文件并添加路径信息
      const videoFiles: FileWithPath[] = fileArray
        .filter(file => isVideoFile(file))
        .map(file => ({
          file,
          path: file.name,
          relativePath: file.name
        }))

      // 计算统计信息
      const totalSize = videoFiles.reduce((sum, { file }) => sum + file.size, 0)
      const videoCount = videoFiles.length
      const skippedCount = fileArray.length - videoCount

      if (totalSize > maxTotalSize) {
        throw new Error(`文件总大小 ${formatFileSize(totalSize)} 超过限制 ${formatFileSize(maxTotalSize)}`)
      }

      if (videoCount === 0) {
        throw new Error('未找到支持的视频文件')
      }

      const result: FolderUploadResult = {
        files: videoFiles,
        totalCount: fileArray.length,
        totalSize,
        videoCount,
        directoryCount: 0, // 普通文件选择不涉及目录
        skippedCount
      }

      setScanResult(result)
      onFolderSelect(result)

      toast.success(`找到 ${videoCount} 个视频文件，总大小 ${formatFileSize(totalSize)}`)

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '文件扫描失败'
      toast.error(errorMessage)
      console.error('File scan error:', error)
    } finally {
      setIsScanning(false)
      setScanProgress(100)
    }
  }, [disabled, maxTotalSize, onFolderSelect])

  // 处理拖拽
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    if (disabled) return

    const items = e.dataTransfer.items
    if (!items || items.length === 0) return

    setIsScanning(true)

    try {
      const videoFiles = await scanFileStructure(items)

      if (videoFiles.length === 0) {
        throw new Error('未找到支持的视频文件')
      }

      const totalSize = videoFiles.reduce((sum, { file }) => sum + file.size, 0)
      const videoCount = videoFiles.length

      if (totalSize > maxTotalSize) {
        throw new Error(`文件总大小超过限制 ${formatFileSize(maxTotalSize)}`)
      }

      const result: FolderUploadResult = {
        files: videoFiles,
        totalCount: videoFiles.length,
        totalSize,
        videoCount,
        directoryCount: 1, // 拖拽通常涉及目录
        skippedCount: 0
      }

      setScanResult(result)
      onFolderSelect(result)

      toast.success(`扫描完成：找到 ${videoCount} 个视频文件`)

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '文件夹扫描失败'
      toast.error(errorMessage)
      console.error('Folder scan error:', error)
    } finally {
      setIsScanning(false)
    }
  }, [disabled, maxTotalSize, onFolderSelect, scanFileStructure])

  // 获取文件图标
  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase()

    if (VIDEO_FORMATS.includes('.' + (extension || ''))) {
      return <FileVideo className="w-4 h-4" />
    }

    switch (extension) {
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return <Image className="w-4 h-4" />
      case 'mp3':
      case 'wav':
      case 'flac':
        return <Music className="w-4 h-4" />
      case 'txt':
      case 'md':
        return <FileText className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 清除结果
  const clearResult = () => {
    setScanResult(null)
    setScanProgress(0)
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Folder className="w-5 h-5" />
          文件夹上传
          {scanResult && (
            <Badge variant="outline">
              {scanResult.videoCount} 个视频
            </Badge>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {!scanResult ? (
          // 上传区域
          <div
            className={cn(
              "upload-area p-8 text-center cursor-pointer transition-all border-2 border-dashed rounded-lg",
              isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !disabled && document.getElementById('folder-input')?.click()}
          >
            <input
              id="folder-input"
              type="file"
              multiple
              {...({ directory: '', webkitdirectory: '' } as any)}
              onChange={(e) => e.target.files && handleFileSelect(e.target.files)}
              className="hidden"
              disabled={disabled}
            />

            <Folder className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />

            <h3 className="text-lg font-medium mb-2">
              {isDragOver ? '释放文件夹以上传' : '拖拽文件夹或文件到此处'}
            </h3>

            <p className="text-sm text-muted-foreground mb-4">
              支持批量上传整个文件夹或多个文件
            </p>

            <p className="text-xs text-muted-foreground mb-4">
              支持格式: {acceptedFormats.join(', ')}
            </p>

            <Button variant="outline" disabled={disabled}>
              选择文件夹
            </Button>
          </div>
        ) : (
          // 扫描结果
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium">扫描结果</h4>
                <p className="text-sm text-muted-foreground">
                  找到 {scanResult.videoCount} 个视频文件，
                  总大小 {formatFileSize(scanResult.totalSize)}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDetails(!showDetails)}
                >
                  {showDetails ? (
                    <ChevronUp className="w-4 h-4 mr-1" />
                  ) : (
                    <ChevronDown className="w-4 h-4 mr-1" />
                  )}
                  {showDetails ? '收起详情' : '查看详情'}
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearResult}
                >
                  <X className="w-4 h-4 mr-1" />
                  重新选择
                </Button>
              </div>
            </div>

            {/* 扫描进度 */}
            {isScanning && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>扫描文件中...</span>
                  <span>{scanProgress}%</span>
                </div>
                <Progress value={scanProgress} className="h-2" />
              </div>
            )}

            {/* 详细文件列表 */}
            {showDetails && !isScanning && (
              <div className="max-h-60 overflow-y-auto border rounded-lg">
                <div className="space-y-1 p-2">
                  {scanResult.files.map(({ file, relativePath }, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-2 rounded hover:bg-gray-50"
                    >
                      {getFileIcon(file.name)}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">
                          {file.name}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {relativePath !== file.name && relativePath}
                          {' • '}
                          {formatFileSize(file.size)}
                        </div>
                      </div>
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 统计信息 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
              <div className="text-center">
                <div className="text-lg font-bold text-blue-600">
                  {scanResult.videoCount}
                </div>
                <div className="text-xs text-gray-600">视频文件</div>
              </div>

              <div className="text-center">
                <div className="text-lg font-bold text-green-600">
                  {scanResult.totalSize > 0 ? formatFileSize(scanResult.totalSize) : '0 B'}
                </div>
                <div className="text-xs text-gray-600">总大小</div>
              </div>

              <div className="text-center">
                <div className="text-lg font-bold text-purple-600">
                  {Math.round(scanResult.totalSize / scanResult.videoCount / 1024 / 1024)}MB
                </div>
                <div className="text-xs text-gray-600">平均大小</div>
              </div>

              <div className="text-center">
                <div className="text-lg font-bold text-orange-600">
                  {scanResult.directoryCount}
                </div>
                <div className="text-xs text-gray-600">文件夹数</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}