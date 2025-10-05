// Import API_BASE_URL from api config
const API_BASE_URL = (import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : `http://localhost:${import.meta.env.VITE_API_PORT || 64451}`))

import React, { useState, useEffect, useCallback } from 'react'
import { Folder, FolderOpen, FileVideo, ChevronRight, ChevronDown, Check, Minus, Loader2, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { videoRAGApi, VideoItem } from '../services/api'
import { toast } from 'sonner'

interface VideoSelectorProps {
  chatId: string
  onSubmitComplete?: (chatId: string) => void
  disabled?: boolean
}

export default function VideoSelector({ chatId, onSubmitComplete, disabled = false }: VideoSelectorProps) {
  const [videoTree, setVideoTree] = useState<VideoItem[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())

  // Load available videos on component mount
  useEffect(() => {
    loadAvailableVideos()
  }, [])

  const loadAvailableVideos = async () => {
    setLoading(true)
    try {
      const response = await videoRAGApi.getAvailableVideos()
      if (response.data.success) {
        setVideoTree(response.data.structure.items)
        toast.success(`找到 ${response.data.structure.total_items} 个视频项目`)
      } else {
        toast.error(response.data.error || '获取视频列表失败')
      }
    } catch (error) {
      console.error('Load videos error:', error)
      toast.error('加载视频列表失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const toggleExpanded = useCallback((item: VideoItem, path: string) => {
    const updateTree = (items: VideoItem[], currentPath: string): VideoItem[] => {
      return items.map(treeItem => {
        if (treeItem.path === path) {
          return { ...treeItem, expanded: !treeItem.expanded }
        } else if (treeItem.children && treeItem.children.length > 0) {
          return { ...treeItem, children: updateTree(treeItem.children, currentPath) }
        }
        return treeItem
      })
    }

    setVideoTree(prev => updateTree(prev, path))
  }, [])

  const toggleSelection = useCallback((item: VideoItem) => {
    const newSelected = new Set(selectedItems)

    if (item.type === 'directory') {
      // Directory selection - select/deselect all children
      const childPaths = getAllChildFilePaths(item)
      if (isDirectoryFullySelected(item, selectedItems)) {
        // Deselect all children
        childPaths.forEach(path => newSelected.delete(path))
      } else {
        // Select all children
        childPaths.forEach(path => newSelected.add(path))
      }
    } else {
      // File selection
      if (newSelected.has(item.path)) {
        newSelected.delete(item.path)
      } else {
        newSelected.add(item.path)
      }
    }

    setSelectedItems(newSelected)
  }, [selectedItems])

  const isDirectoryFullySelected = useCallback((item: VideoItem, selected: Set<string>): boolean => {
    if (!item.children || item.children.length === 0) return false
    const childFiles = item.children.filter(child => child.type === 'file')
    return childFiles.every(child => selected.has(child.path))
  }, [])

  const isDirectoryPartiallySelected = useCallback((item: VideoItem, selected: Set<string>): boolean => {
    if (!item.children || item.children.length === 0) return false
    const childFiles = item.children.filter(child => child.type === 'file')
    const selectedCount = childFiles.filter(child => selected.has(child.path)).length
    return selectedCount > 0 && selectedCount < childFiles.length
  }, [])

  const getAllChildFilePaths = useCallback((item: VideoItem): string[] => {
    const paths: string[] = []

    const collectPaths = (currentItem: VideoItem) => {
      if (currentItem.type === 'file') {
        paths.push(currentItem.path)
      } else if (currentItem.children) {
        currentItem.children.forEach(child => collectPaths(child))
      }
    }

    collectPaths(item)
    return paths
  }, [])

  const getSelectedFilesCount = useCallback((): number => {
    return selectedItems.size
  }, [selectedItems])

  const getTotalSelectedSize = useCallback((): { size: number; size_mb: number } => {
    let totalSize = 0

    const collectSize = (items: VideoItem[]) => {
      items.forEach(item => {
        if (item.type === 'file' && selectedItems.has(item.path)) {
          totalSize += item.size || 0
        } else if (item.children) {
          collectSize(item.children)
        }
      })
    }

    collectSize(videoTree)
    return {
      size: totalSize,
      size_mb: Math.round(totalSize / (1024 * 1024) * 100) / 100
    }
  }, [videoTree, selectedItems])

  const selectAll = useCallback(() => {
    const allPaths: string[] = []
    const collectAllPaths = (items: VideoItem[]) => {
      items.forEach(item => {
        if (item.type === 'file') {
          allPaths.push(item.path)
        } else if (item.children) {
          collectAllPaths(item.children)
        }
      })
    }
    collectAllPaths(videoTree)
    setSelectedItems(new Set(allPaths))
  }, [videoTree])

  const deselectAll = useCallback(() => {
    setSelectedItems(new Set())
  }, [])

  const handleSubmit = async () => {
    if (selectedItems.size === 0) {
      toast.error('请先选择要处理的视频文件')
      return
    }

    setSubmitting(true)
    try {
      const selectedFiles = Array.from(selectedItems)

      // Call the upload-web endpoint using axios for better error handling
      const response = await videoRAGApi.uploadVideosWeb(chatId, selectedFiles)

      const data = response.data

      if (data.success) {
        toast.success(`成功提交 ${selectedItems.size} 个视频文件进行处理`)
        setSelectedItems(new Set())
        onSubmitComplete?.(chatId)
      } else {
        toast.error(data.error || '提交处理失败')
      }
    } catch (error) {
      console.error('Submit error:', error)
      toast.error('提交失败，请重试')
    } finally {
      setSubmitting(false)
    }
  }

  const renderVideoTree = (items: VideoItem[]): JSX.Element[] => {
    return items.map(item => {
      const isSelected = item.type === 'file' ? selectedItems.has(item.path) :
                        item.type === 'directory' ? isDirectoryFullySelected(item, selectedItems) : false
      const isPartiallySelected = item.type === 'directory' ? isDirectoryPartiallySelected(item, selectedItems) : false

      return (
        <div key={item.path}>
          <div className="flex items-center py-2 px-2 hover:bg-gray-50 rounded">
            {/* Expand/Collapse icon for directories */}
            {item.type === 'directory' && item.children && item.children.length > 0 && (
              <button
                onClick={() => toggleExpanded(item, item.path)}
                className="mr-2 p-1 hover:bg-gray-200 rounded"
                disabled={disabled}
              >
                {item.expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
            )}

            {/* File/Directory icon */}
            <div className="mr-2">
              {item.type === 'directory' ? (
                item.expanded ? <FolderOpen size={16} /> : <Folder size={16} />
              ) : (
                <FileVideo size={16} />
              )}
            </div>

            {/* Checkbox */}
            <button
              onClick={() => toggleSelection(item)}
              className="mr-3 p-1 border rounded hover:bg-gray-100"
              disabled={disabled}
            >
              {isSelected ? (
                <Check size={14} />
              ) : isPartiallySelected ? (
                <Minus size={14} />
              ) : (
                null
              )}
            </button>

            {/* Name and metadata */}
            <div className="flex-1">
              <div className="flex items-center">
                <span className="font-medium text-sm">{item.name}</span>
                {item.type === 'directory' && item.total_files && (
                  <span className="ml-2 text-xs text-gray-500">
                    ({item.total_files} 个文件, {item.total_size_mb}MB)
                  </span>
                )}
                {item.type === 'file' && item.format && (
                  <span className="ml-2 text-xs bg-gray-100 px-2 py-1 rounded">
                    {item.format.toUpperCase()}
                  </span>
                )}
                {item.type === 'file' && item.size_mb && (
                  <span className="ml-2 text-xs text-gray-500">
                    {item.size_mb}MB
                  </span>
                )}
              </div>

              {item.type === 'directory' && item.total_files && (
                <div className="text-xs text-gray-400 mt-1">
                  最后修改: {new Date(item.modified * 1000).toLocaleDateString()}
                </div>
              )}
              {item.type === 'file' && (
                <div className="text-xs text-gray-400 mt-1">
                  修改时间: {new Date(item.modified * 1000).toLocaleString()}
                </div>
              )}
            </div>
          </div>

          {/* Children (only show if expanded) */}
          {item.type === 'directory' && item.expanded && item.children && (
            <div className="ml-6 border-l border-gray-200 pl-4">
              {renderVideoTree(item.children)}
            </div>
          )}
        </div>
      )
    })
  }

  const filteredTree = useCallback(() => {
    if (!searchQuery.trim()) return videoTree

    const filterItems = (items: VideoItem[]): VideoItem[] => {
      return items.filter(item => {
        const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase())

        if (item.children && item.children.length > 0) {
          item.children = filterItems(item.children)
          return matchesSearch || item.children.length > 0
        }

        return matchesSearch
      })
    }

    return filterItems([...videoTree])
  }, [videoTree, searchQuery])

  const selectedStats = getTotalSelectedSize()

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileVideo className="w-5 h-5" />
          选择视频文件进行处理
        </CardTitle>
        <CardDescription>
          从服务器端选择视频文件或整个目录进行批量VideoRAG处理
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Search and controls */}
        <div className="flex gap-4 items-center">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="搜索视频文件..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="max-w-sm"
            />
          </div>
          <Button
            variant="outline"
            onClick={loadAvailableVideos}
            disabled={loading || disabled}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>

        {/* Selection stats */}
        {selectedItems.size > 0 && (
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex justify-between items-center">
              <div>
                <span className="font-medium text-blue-700">
                  已选择: {selectedItems.size} 个文件
                </span>
                <span className="ml-2 text-blue-600">
                  总大小: {selectedStats.size_mb}MB
                </span>
              </div>
              <div className="space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={selectAll}
                  disabled={disabled}
                >
                  全选
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={deselectAll}
                  disabled={disabled}
                >
                  取消选择
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Video tree */}
        <div className={`border rounded-lg max-h-96 overflow-y-auto ${disabled ? 'opacity-50' : ''}`}>
          {loading ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              正在加载视频文件...
            </div>
          ) : videoTree.length === 0 ? (
            <div className="flex flex-col justify-center items-center py-8 text-gray-500">
              <FileVideo className="w-12 h-12 mb-4 opacity-50" />
              <p>未找到可用视频文件</p>
              <p className="text-sm mt-1">请检查服务器存储目录</p>
            </div>
          ) : (
            <div className="p-4">
              {renderVideoTree(filteredTree())}
            </div>
          )}
        </div>

        {/* Submit button */}
        <div className="flex justify-end">
          <Button
            onClick={handleSubmit}
            disabled={selectedItems.size === 0 || submitting || disabled}
            className="min-w-32"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                提交中...
              </>
            ) : (
              `处理 ${selectedItems.size} 个文件`
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}