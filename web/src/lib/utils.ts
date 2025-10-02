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

export function getVideoThumbnail(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    video.preload = 'metadata'
    video.src = URL.createObjectURL(file)

    video.onloadeddata = () => {
      // Set canvas dimensions to match video
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      // Seek to 1 second (or first frame if shorter)
      const seekTime = Math.min(1, video.duration)
      video.currentTime = seekTime
    }

    video.onseeked = () => {
      // Draw the video frame to canvas
      ctx?.drawImage(video, 0, 0, canvas.width, canvas.height)

      // Convert to blob and then to URL
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob)
          resolve(url)
        } else {
          reject(new Error('Failed to generate thumbnail'))
        }
      }, 'image/jpeg', 0.8)

      // Cleanup
      URL.revokeObjectURL(video.src)
    }

    video.onerror = () => {
      reject(new Error('Failed to load video'))
      URL.revokeObjectURL(video.src)
    }
  })
}