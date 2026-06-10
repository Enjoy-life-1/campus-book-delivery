<template>
  <div class="image-uploader">
    <label class="form-label">{{ label }} <span v-if="required" class="text-danger">*</span></label>
    <div class="d-flex flex-wrap gap-2 mb-2">
      <div v-for="(url, i) in previews" :key="i" class="preview-box">
        <img :src="url" alt="预览">
        <button type="button" class="remove-btn" @click="removeAt(i)">×</button>
      </div>
      <label v-if="previews.length < maxCount" class="add-box">
        <i class="fa fa-plus"></i>
        <span>上传</span>
        <input type="file" accept="image/*" multiple hidden @change="onPick">
      </label>
    </div>
    <p class="text-muted small mb-0">最多{{ maxCount }}张，压缩后保存至服务器{{ uploading ? '（上传中…）' : '' }}</p>
  </div>
</template>

<script setup>
// 发布页多图上传；expose getUrls/setFromUrls 给父组件
import { useImageUpload } from '@/composables/useImageUpload'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  label: { type: String, default: '书籍图片' },
  required: { type: Boolean, default: true },
  maxCount: { type: Number, default: 3 }
})

const { previews, uploading, addFiles, removeAt, setFromUrls, getUrls } = useImageUpload(props.maxCount)
const { show } = useToast()

async function onPick(e) {
  try {
    await addFiles(e.target.files)
    e.target.value = ''
  } catch (err) {
    show(err.message, 'error')
  }
}

defineExpose({ getUrls, setFromUrls, previews })
</script>

<style scoped>
.preview-box, .add-box {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  border: 1px dashed #ccc;
}
.preview-box img { width: 100%; height: 100%; object-fit: cover; }
.remove-btn {
  position: absolute; top: 2px; right: 2px;
  width: 22px; height: 22px; border: none; border-radius: 50%;
  background: rgba(0,0,0,.6); color: #fff; line-height: 1; cursor: pointer;
}
.add-box {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  cursor: pointer; color: #28a745; background: #f8f9fa;
}
.add-box:hover { border-color: #28a745; }
</style>
