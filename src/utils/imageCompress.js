/** 上传前压缩图片，减小 base64 体积 */
export function compressImageFile(file, maxW = 1280, quality = 0.82) {
  return new Promise((resolve, reject) => {
    if (!file?.type?.startsWith('image/')) {
      reject(new Error('请选择图片文件'))
      return
    }
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      let { width, height } = img
      if (width > maxW) {
        // 等比缩放到 maxW，再转 JPEG
        height = Math.round(height * (maxW / width))
        width = maxW
      }
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      canvas.getContext('2d').drawImage(img, 0, 0, width, height)
      const out = canvas.toDataURL('image/jpeg', quality)
      resolve(out)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('图片解析失败'))
    }
    img.src = url
  })
}
