// 选图 → 压缩 → POST /api/books/upload-image → 服务器 URL
import { ref } from 'vue'
import { compressImageFile } from '@/utils/imageCompress'
import { bookAPI } from '@/utils/api'

const MAX_SIZE = 5 * 1024 * 1024
const MAX_COUNT = 3

async function uploadDataUrl(dataUrl) {
  // data URL 转 blob 再上传，避免 base64 入库
  if (!dataUrl?.startsWith('data:image')) {
    return dataUrl
  }
  const blob = await (await fetch(dataUrl)).blob()
  const fd = new FormData()
  fd.append('file', blob, 'book.jpg')
  const res = await bookAPI.uploadImage(fd)
  if (res.status !== 'success' || !res.url) {
    throw new Error(res.message || '图片上传失败')
  }
  return res.url
}

export function useImageUpload(maxCount = MAX_COUNT) {
  const previews = ref([])
  const uploading = ref(false)

  function readFile(file) {
    return new Promise((resolve, reject) => {
      if (!file.type.startsWith('image/')) {
        reject(new Error('请选择图片文件'))
        return
      }
      if (file.size > MAX_SIZE) {
        reject(new Error('单张图片不能超过5MB'))
        return
      }
      compressImageFile(file).then(resolve).catch(() => {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target.result)
        reader.onerror = () => reject(new Error('读取图片失败'))
        reader.readAsDataURL(file)
      })
    })
  }

  async function addFiles(fileList) {
    const files = Array.from(fileList || [])
    const remain = maxCount - previews.value.length
    if (remain <= 0) throw new Error(`最多上传${maxCount}张图片`)
    uploading.value = true
    try {
      for (const file of files.slice(0, remain)) {
        const dataUrl = await readFile(file)
        const url = await uploadDataUrl(dataUrl)
        previews.value.push(url)
      }
    } finally {
      uploading.value = false
    }
  }

  function removeAt(index) {
    previews.value.splice(index, 1)
  }

  function setFromUrls(urls) {
    previews.value = (urls || []).filter(Boolean).slice(0, maxCount)
  }

  function getUrls() {
    return [...previews.value]
  }

  function clear() {
    previews.value = []
  }

  return { previews, uploading, addFiles, removeAt, setFromUrls, getUrls, clear }
}
