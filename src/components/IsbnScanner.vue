<template>
  <div>
    <button type="button" class="btn btn-outline-secondary btn-sm" @click="open = true">
      <i class="fa fa-camera"></i> 扫码
    </button>
    <div v-if="open" class="isbn-scan-mask" @click.self="close">
      <div class="isbn-scan-box card p-3">
        <div class="d-flex justify-content-between mb-2">
          <strong>扫描 ISBN 条码</strong>
          <button type="button" class="btn-close" @click="close"></button>
        </div>
        <video ref="video" class="w-100 rounded" playsinline muted></video>
        <p class="small text-muted mt-2 mb-0">{{ hint }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// BarcodeDetector 扫 ISBN，emit('scan', code)
import { ref, watch, onUnmounted } from 'vue'

const emit = defineEmits(['scan'])
const open = ref(false)
const video = ref(null)
const hint = ref('')
let stream = null
let timer = null

async function start() {
  hint.value = '正在打开摄像头…'
  if (!('BarcodeDetector' in window)) {
    hint.value = '当前浏览器不支持扫码，请手动输入 ISBN'
    return
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    if (video.value) {
      video.value.srcObject = stream
      await video.value.play()
    }
    const detector = new window.BarcodeDetector({ formats: ['ean_13', 'ean_8', 'code_128'] })
    hint.value = '将条码对准画面'
    timer = setInterval(async () => {
      if (!video.value || video.value.readyState < 2) return
      try {
        const codes = await detector.detect(video.value)
        const raw = codes[0]?.rawValue?.replace(/[^0-9Xx]/g, '')
        if (raw && raw.length >= 10) {
          emit('scan', raw)
          close()
        }
      } catch (_) { /* ignore frame errors */ }
    }, 500)
  } catch (e) {
    hint.value = '无法访问摄像头：' + (e.message || '请授权相机')
  }
}

function stop() {
  if (timer) { clearInterval(timer); timer = null }
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  if (video.value) video.value.srcObject = null
}

function close() {
  open.value = false
  stop()
}

watch(open, (v) => { if (v) start(); else stop() })
onUnmounted(stop)
</script>

<style scoped>
.isbn-scan-mask {
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(0,0,0,.55);
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
}
.isbn-scan-box { max-width: 420px; width: 100%; }
</style>
