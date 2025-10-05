import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function generateChatId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

export function validateVideoFile(file: File): boolean {
  const allowedTypes = ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime', 'video/x-msvideo']
  const maxSize = 2 * 1024 * 1024 * 1024 // 2GB

  return allowedTypes.includes(file.type) && file.size <= maxSize
}

// 获取视频错误的详细信息
function getVideoErrorDetails(event: Event, video: HTMLVideoElement): string {
  const videoError = video.error
  if (!videoError) return '未知视频错误'

  switch (videoError.code) {
    case MediaError.MEDIA_ERR_ABORTED:
      return '视频加载被用户取消'
    case MediaError.MEDIA_ERR_NETWORK:
      return '网络错误导致视频无法加载'
    case MediaError.MEDIA_ERR_DECODE:
      return '视频解码失败，可能是不支持的编码格式'
    case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
      return '不支持的视频格式或文件损坏'
    default:
      return `视频错误 (代码: ${videoError.code})`
  }
}

export function getVideoThumbnail(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    // 文件完整性检查
    if (!file || file.size === 0) {
      reject(new Error('文件为空或无效'))
      return
    }

    const video = document.createElement('video')
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    // 改为none避免自动加载，使用手动控制
    video.preload = 'none'
    video.muted = true // 避免自动播放限制

    // 超时机制 - 10秒
    const timeoutId = setTimeout(() => {
      if (video.src) URL.revokeObjectURL(video.src)
      video.remove()
      reject(new Error('视频加载超时，请检查文件是否损坏'))
    }, 10000)

    // 改进的事件处理
    video.onloadeddata = () => {
      clearTimeout(timeoutId)

      try {
        // 检查视频是否有有效的尺寸
        if (video.videoWidth === 0 || video.videoHeight === 0) {
          throw new Error('视频尺寸无效')
        }

        // Set canvas dimensions to match video
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight

        // Seek to 1 second (or first frame if shorter)
        const seekTime = Math.min(1, video.duration)
        video.currentTime = seekTime
      } catch (error) {
        cleanup()
        reject(new Error(`视频处理失败: ${error.message}`))
      }
    }

    video.onseeked = () => {
      try {
        // Draw the video frame to canvas
        ctx?.drawImage(video, 0, 0, canvas.width, canvas.height)

        // Convert to blob and then to URL
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob)
            cleanup()
            resolve(url)
          } else {
            cleanup()
            reject(new Error('缩略图生成失败，请重试'))
          }
        }, 'image/jpeg', 0.8)
      } catch (error) {
        cleanup()
        reject(new Error(`缩略图绘制失败: ${error.message}`))
      }
    }

    video.onerror = (event) => {
      clearTimeout(timeoutId)
      const errorDetails = getVideoErrorDetails(event, video)
      cleanup()
      reject(new Error(errorDetails))
    }

    // 添加canplay事件作为备选
    video.oncanplay = () => {
      // 如果onloadeddata未触发但canplay触发，尝试继续处理
      if (video.videoWidth > 0 && video.videoHeight > 0) {
        try {
          canvas.width = video.videoWidth
          canvas.height = video.videoHeight
          const seekTime = Math.min(1, video.duration)
          video.currentTime = seekTime
        } catch (error) {
          cleanup()
          reject(new Error(`视频播放就绪但处理失败: ${error.message}`))
        }
      }
    }

    // 清理函数
    const cleanup = () => {
      if (video.src) URL.revokeObjectURL(video.src)
      video.remove()
    }

    // 设置视频源并开始加载
    try {
      video.src = URL.createObjectURL(file)
      video.load() // 手动触发加载
    } catch (error) {
      clearTimeout(timeoutId)
      cleanup()
      reject(new Error(`视频源设置失败: ${error.message}`))
    }
  })
}