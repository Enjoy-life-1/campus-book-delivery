<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h2 class="mb-0">
          <i class="fa fa-envelope text-success"></i> 站内消息
          <span v-if="wsOk" class="badge bg-success ms-2 small">实时</span>
          <span v-else class="badge bg-secondary ms-2 small">轮询</span>
        </h2>
        <span v-if="unreadConvTotal" class="badge bg-danger">未读会话 {{ unreadConvTotal }}</span>
      </div>
      <div v-if="muteNotice" class="alert alert-info d-flex align-items-start gap-2 mb-3">
        <i class="fa fa-microphone-slash mt-1"></i>
        <div>
          <strong>{{ muteNotice.title }}</strong>
          <p class="mb-0 small">{{ muteNotice.detail }} 您仍可查看历史消息，但无法发送新消息。</p>
        </div>
      </div>
      <div class="row g-3 msg-layout">
        <div class="col-md-4">
          <div class="card conv-list">
            <div class="conv-tabs border-bottom">
              <button type="button" class="conv-tab" :class="{ active: convFilter === 'all' }" @click="convFilter = 'all'">全部</button>
              <button type="button" class="conv-tab" :class="{ active: convFilter === 'unread' }" @click="convFilter = 'unread'">
                未读<span v-if="unreadConvTotal" class="ms-1 badge rounded-pill bg-danger">{{ unreadConvTotal }}</span>
              </button>
            </div>
            <div v-if="!shownConvs.length" class="p-4 text-muted text-center">{{ convFilter === 'unread' ? '暂无未读会话' : '暂无会话' }}</div>
            <a
              v-for="c in shownConvs"
              :key="c.id"
              href="#"
              class="conv-item d-block p-3 text-decoration-none text-dark border-bottom"
              :class="{ active: activeId === c.id, 'conv-unread': c.unread > 0 }"
              @click.prevent="selectConv(c.id)"
            >
              <div class="d-flex justify-content-between align-items-center gap-2">
                <div class="d-flex align-items-center gap-2 min-w-0">
                  <span v-if="c.unread" class="unread-dot" title="未读"></span>
                  <strong class="text-truncate" :class="{ 'fw-bold': c.unread }">{{ c.peer?.username }}</strong>
                </div>
                <span class="read-state-badge" :class="c.unread ? 'unread' : 'read'">{{ c.unread ? `${c.unread}条未读` : '已读' }}</span>
              </div>
              <small class="text-muted d-block text-truncate" :class="{ 'fw-semibold text-dark': c.unread }">{{ c.last_preview || '暂无消息' }}</small>
              <small v-if="c.book_title" class="text-success">[{{ c.book_title }}]</small>
            </a>
          </div>
        </div>
        <div class="col-md-8">
          <div v-if="!activeId" class="card p-5 text-center text-muted">选择左侧会话开始聊天</div>
          <div v-else class="card chat-panel">
            <div class="card-header d-flex justify-content-between align-items-center">
              <span>与 <strong>{{ peer?.username }}</strong> 的对话</span>
              <span v-if="conv?.book_title" class="small text-muted">{{ conv.book_title }}</span>
            </div>
            <div ref="msgBox" class="chat-body p-3">
              <div v-for="m in messages" :key="m.id" class="mb-3" :class="m.sender_id === user?.id ? 'text-end' : ''">
                <div class="d-inline-block px-3 py-2 rounded msg-bubble" :class="bubbleClass(m)">
                  <div v-if="m.is_recalled" class="text-muted fst-italic">消息已撤回</div>
                  <template v-else-if="m.msg_type === 'appointment' && m.appointment">
                    <div class="text-start appt-card">
                      <div class="fw-bold"><i class="fa fa-map-marker"></i> 面交预约</div>
                      <div>地点：{{ m.appointment.place }}</div>
                      <div>时间：{{ m.appointment.meeting_time }}</div>
                      <div v-if="m.appointment.note">备注：{{ m.appointment.note }}</div>
                      <span class="badge" :class="apptBadge(m.appointment.status)">{{ apptStatus(m.appointment.status) }}</span>
                      <div v-if="m.appointment.status === 'pending' && m.sender_id !== user?.id" class="mt-2">
                        <button class="btn btn-sm btn-success me-1" @click="confirmAppt(m.appointment.id)">确认</button>
                        <button class="btn btn-sm btn-outline-secondary" @click="cancelAppt(m.appointment.id)">拒绝</button>
                      </div>
                    </div>
                  </template>
                  <div v-else-if="m.msg_type === 'image' && m.media_url" class="text-start">
                    <a :href="m.media_url" target="_blank" rel="noopener"><img :src="m.media_url" class="msg-img" alt="图片"></a>
                  </div>
                  <div v-else-if="m.msg_type === 'audio' && m.media_url" class="text-start">
                    <audio :src="m.media_url" controls class="msg-audio"></audio>
                  </div>
                  <div v-else-if="m.msg_type === 'location'" class="text-start">
                    <div><i class="fa fa-map-marker text-danger"></i> {{ locLabel(m) }}</div>
                    <a v-if="locLink(m)" :href="locLink(m)" target="_blank" rel="noopener" class="small">在地图中打开</a>
                  </div>
                  <div v-else>{{ m.content }}</div>
                  <div class="msg-meta d-flex align-items-center gap-2 mt-1" :class="m.sender_id === user?.id ? 'justify-content-end' : ''">
                    <small class="msg-time">{{ m.created_at }}</small>
                    <span v-if="showReadTag(m)" class="read-receipt" :class="m.is_read ? 'read' : 'unread'" :title="m.is_read && m.read_at ? `已读于 ${m.read_at}` : ''">
                      <i class="fa" :class="m.is_read ? 'fa-check-circle' : 'fa-circle-o'"></i>
                      {{ m.is_read ? '已读' : '未读' }}
                    </span>
                    <span v-else-if="isIncomingUnread(m)" class="read-receipt incoming-unread">未读</span>
                  </div>
                  <button
                    v-if="canRecall(m)"
                    type="button"
                    class="btn btn-link btn-sm p-0 text-muted recall-btn"
                    @click="recall(m)"
                  >撤回</button>
                </div>
              </div>
            </div>
            <div class="card-footer" :class="{ 'opacity-75': isMuted }">
              <div class="mb-2 d-flex flex-wrap gap-1">
                <button class="btn btn-sm btn-outline-success" :disabled="isMuted" @click="showAppt = !showAppt">
                  <i class="fa fa-calendar"></i> 面交预约
                </button>
                <label class="btn btn-sm btn-outline-secondary mb-0" :class="{ disabled: isMuted }">
                  <i class="fa fa-picture-o"></i> 图片
                  <input type="file" accept="image/*" class="d-none" :disabled="isMuted" @change="onImagePick">
                </label>
                <label class="btn btn-sm btn-outline-secondary mb-0" :class="{ disabled: isMuted }">
                  <i class="fa fa-microphone"></i> 语音
                  <input type="file" accept="audio/*" class="d-none" :disabled="isMuted" @change="onAudioPick">
                </label>
                <button class="btn btn-sm btn-outline-secondary" :disabled="isMuted" @click="shareLocation">
                  <i class="fa fa-map-marker"></i> 位置
                </button>
              </div>
              <div v-if="showAppt" class="border rounded p-2 mb-2 bg-light">
                <select v-model="appt.place" class="form-select form-select-sm mb-1">
                  <option value="">选择校内面交点</option>
                  <optgroup v-for="(list, zone) in spotsByZone" :key="zone" :label="zone">
                    <option v-for="s in list" :key="s.id" :value="s.name">{{ s.name }} — {{ s.description }}</option>
                  </optgroup>
                </select>
                <input v-model="appt.meeting_time" type="datetime-local" class="form-control form-control-sm mb-1">
                <input v-model="appt.note" class="form-control form-control-sm mb-1" placeholder="备注（选填）">
                <button class="btn btn-sm btn-success" :disabled="isMuted" @click="sendAppt">发送预约</button>
              </div>
              <div class="input-group">
                <input
                  v-model="text"
                  class="form-control"
                  :placeholder="isMuted ? '您已被禁言，无法发送消息' : '输入消息...'"
                  :disabled="isMuted"
                  @keyup.enter="send"
                >
                <button class="btn btn-success" :disabled="sending || isMuted" @click="send">发送</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 私信：WebSocket 实时 + 8s 轮询降级；面交/多媒体/撤回
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { messageAPI, campusAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { useToast } from '@/composables/useToast'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { getBanNotice, isMuted as checkMuted } from '@/utils/banStatus'
import { refreshSession } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()
const { show } = useToast()
const userStore = useUserStore()
const { profile } = storeToRefs(userStore)
const user = ref(getCurrentUser())
const convs = ref([])
const convFilter = ref('all')
const messages = ref([])
const activeId = ref('')
const peer = ref(null)
const conv = ref(null)
const text = ref('')
const sending = ref(false)
const showAppt = ref(false)
const msgBox = ref(null)
const spots = ref([])
const appt = ref({ place: '', meeting_time: '', note: '' })
const wsOk = ref(false)
let ws = null
let pollTimer = null
const lastMsgAt = ref('')

const spotsByZone = computed(() => {
  const map = {}
  for (const s of spots.value) {
    const z = s.zone || '西校区'
    if (!map[z]) map[z] = []
    map[z].push(s)
  }
  return map
})

const unreadConvTotal = computed(() => convs.value.filter(c => c.unread > 0).length)

const shownConvs = computed(() =>
  convFilter.value === 'unread' ? convs.value.filter(c => c.unread > 0) : convs.value
)

const isMuted = computed(() => checkMuted(profile.value || user.value))
const muteNotice = computed(() => (isMuted.value ? getBanNotice(profile.value || user.value) : null))

function showReadTag(m) {
  return m.sender_id === user.value?.id && m.msg_type !== 'system' && !m.is_recalled
}

function isIncomingUnread(m) {
  return m.sender_id !== user.value?.id && !m.is_read && !m.is_recalled && m.msg_type !== 'system'
}

function wsUrl() {
  const p = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${p}//${location.host}/ws/chat`
}

function connectWs() {
  // /ws/chat；断线 4s 重连，失败则轮询
  try {
    ws = new WebSocket(wsUrl())
    ws.onopen = () => {
      wsOk.value = true
      stopPoll()
      if (activeId.value) wsSub(activeId.value)
    }
    ws.onclose = () => {
      wsOk.value = false
      startPoll()
      setTimeout(connectWs, 4000)
    }
    ws.onmessage = (ev) => {
      try {
        handleWs(JSON.parse(ev.data))
      } catch (_) { /* ignore */ }
    }
  } catch (_) {
    wsOk.value = false
    startPoll()
  }
}

function wsSub(convId) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'subscribe', conv_id: convId }))
  }
}

function wsUnsub(convId) {
  if (ws?.readyState === WebSocket.OPEN && convId) {
    ws.send(JSON.stringify({ type: 'unsubscribe', conv_id: convId }))
  }
}

function handleWs(evt) {
  // 新消息 / 已读回执 / 撤回
  if (evt.type === 'new_message' && evt.conv_id === activeId.value) {
    const exists = messages.value.some(x => x.id === evt.message?.id)
    if (!exists) {
      messages.value.push(evt.message)
      if (evt.message?.created_at) lastMsgAt.value = evt.message.created_at
      loadConvs()
      scrollBottom()
    }
  } else if (evt.type === 'read' && evt.conv_id === activeId.value) {
    messages.value.forEach(m => {
      if (m.sender_id === user.value?.id) {
        m.is_read = true
        m.read_at = evt.read_at
      }
    })
  } else if (evt.type === 'recall' && evt.conv_id === activeId.value) {
    const i = messages.value.findIndex(x => x.id === evt.message?.id)
    if (i >= 0) messages.value[i] = evt.message
    loadConvs()
  } else if (evt.type === 'new_message' && evt.conv_id !== activeId.value) {
    loadConvs()
  }
}

function bubbleClass(m) {
  if (m.is_recalled) return 'bg-light text-muted'
  if (m.msg_type === 'system') return 'bg-light text-secondary'
  if (m.msg_type === 'appointment') return 'bg-warning-subtle'
  return m.sender_id === user.value?.id ? 'bg-success text-white' : 'bg-light'
}

function apptStatus(s) {
  return { pending: '待确认', confirmed: '已确认', cancelled: '已取消' }[s] || s
}

function apptBadge(s) {
  return { pending: 'bg-warning', confirmed: 'bg-success', cancelled: 'bg-secondary' }[s] || 'bg-secondary'
}

function locLabel(m) {
  return m.content || m.media_meta?.place || '位置'
}

function locLink(m) {
  const lat = m.media_meta?.lat
  const lng = m.media_meta?.lng
  if (lat != null && lng != null) {
    return `https://uri.amap.com/marker?position=${lng},${lat}&name=${encodeURIComponent(locLabel(m))}`
  }
  return ''
}

function canRecall(m) {
  if (m.sender_id !== user.value?.id || m.is_recalled) return false
  if (['system', 'appointment'].includes(m.msg_type)) return false
  try {
    const sent = new Date((m.created_at || '').replace(' ', 'T'))
    return Date.now() - sent.getTime() < 2 * 60 * 1000
  } catch (_) {
    return false
  }
}

async function loadConvs() {
  const res = await messageAPI.getConversations()
  if (res.status === 'success') convs.value = res.conversations || []
  userStore.refreshBadges()
}

async function selectConv(id) {
  // 切换会话：unsub 旧 / sub 新 / 拉历史
  if (activeId.value && activeId.value !== id) wsUnsub(activeId.value)
  activeId.value = id
  router.replace({ query: { conv: id } })
  await fetchMessages(id, false)
  wsSub(id)
  if (!wsOk.value) startPoll()
}

async function fetchMessages(id, incremental) {
  const params = incremental && lastMsgAt.value ? { since: lastMsgAt.value } : {}
  const res = await messageAPI.getMessages(id, params)
  if (res.status === 'success') {
    const incoming = res.messages || []
    if (incremental && incoming.length) {
      for (const m of incoming) {
        if (!messages.value.some(x => x.id === m.id)) messages.value.push(m)
      }
    } else if (!incremental) {
      messages.value = incoming
    }
    if (messages.value.length) {
      lastMsgAt.value = messages.value[messages.value.length - 1].created_at
    }
    peer.value = res.peer
    conv.value = res.conversation
    if (!incremental) {
      messages.value.forEach(m => {
        if (m.sender_id !== user.value?.id) m.is_read = true
      })
    }
    await loadConvs()
    scrollBottom()
  }
}

function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

function startPoll() {
  // WebSocket 不可用时增量拉 since
  stopPoll()
  pollTimer = setInterval(() => {
    if (activeId.value && !wsOk.value) fetchMessages(activeId.value, true)
  }, 8000)
}

function stopPoll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function send() {
  if (isMuted.value) {
    show('您已被禁言，暂无法发送私信', 'warning')
    return
  }
  if (!text.value.trim() || sending.value) return
  sending.value = true
  try {
    const res = await messageAPI.sendMessage(activeId.value, { content: text.value.trim(), msg_type: 'text' })
    if (res.status === 'success') {
      if (!messages.value.some(x => x.id === res.message.id)) messages.value.push(res.message)
      text.value = ''
      loadConvs()
      scrollBottom()
    }
  } catch (e) { show(e.message || '发送失败', 'danger') }
  finally { sending.value = false }
}

async function sendMedia(file, kind) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('kind', kind)
  const up = await messageAPI.uploadMedia(fd)
  if (up.status !== 'success') throw new Error(up.message || '上传失败')
  const res = await messageAPI.sendMessage(activeId.value, {
    msg_type: up.msg_type,
    media_url: up.url,
    content: kind === 'audio' ? '[语音]' : ''
  })
  if (res.status === 'success') {
    messages.value.push(res.message)
    loadConvs()
    scrollBottom()
  }
}

async function onImagePick(e) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  try { await sendMedia(f, 'image') } catch (err) { show(err.message || '发送失败', 'danger') }
}

async function onAudioPick(e) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  try { await sendMedia(f, 'audio') } catch (err) { show(err.message || '发送失败', 'danger') }
}

function shareLocation() {
  const fallback = () => {
    const place = prompt('输入面交地点名称')
    if (!place) return
    sendLocation(place, null, null)
  }
  if (!navigator.geolocation) return fallback()
  navigator.geolocation.getCurrentPosition(
    (pos) => sendLocation(appt.value.place || '当前位置', pos.coords.latitude, pos.coords.longitude),
    () => fallback(),
    { timeout: 8000 }
  )
}

async function sendLocation(place, lat, lng) {
  try {
    const res = await messageAPI.sendMessage(activeId.value, {
      msg_type: 'location',
      content: place,
      media_meta: { place, lat, lng }
    })
    if (res.status === 'success') {
      messages.value.push(res.message)
      loadConvs()
      scrollBottom()
    }
  } catch (e) { show(e.message || '发送失败', 'danger') }
}

async function recall(m) {
  try {
    const res = await messageAPI.recallMessage(activeId.value, m.id)
    if (res.status === 'success') {
      const i = messages.value.findIndex(x => x.id === m.id)
      if (i >= 0) messages.value[i] = res.message
      loadConvs()
    }
  } catch (e) { show(e.message || '撤回失败', 'danger') }
}

async function sendAppt() {
  if (!appt.value.place || !appt.value.meeting_time) {
    show('请填写地点和时间', 'warning')
    return
  }
  try {
    const res = await messageAPI.createAppointment(activeId.value, {
      place: appt.value.place,
      meeting_time: appt.value.meeting_time.replace('T', ' '),
      note: appt.value.note,
      order_id: conv.value?.order_id
    })
    if (res.status === 'success') {
      messages.value.push(res.message)
      showAppt.value = false
      appt.value = { place: '', meeting_time: '', note: '' }
      loadConvs()
      scrollBottom()
    }
  } catch (e) { show(e.message || '预约失败', 'danger') }
}

async function confirmAppt(id) {
  await messageAPI.updateAppointment(id, { status: 'confirmed' })
  show('已确认面交', 'success')
  selectConv(activeId.value)
}

async function cancelAppt(id) {
  await messageAPI.updateAppointment(id, { status: 'cancelled' })
  selectConv(activeId.value)
}

async function tryStartFromQuery() {
  const { peer: peerId, book, order, conv: convId } = route.query
  if (convId) {
    await selectConv(String(convId))
    return
  }
  if (peerId) {
    const res = await messageAPI.startConversation({
      peer_id: peerId,
      book_id: book || '',
      order_id: order || ''
    })
    if (res.status === 'success') await selectConv(res.conversation.id)
  }
}

onMounted(async () => {
  await refreshSession()
  user.value = getCurrentUser()
  const sp = await campusAPI.getSpots()
  if (sp.status === 'success') spots.value = sp.spots || []
  await loadConvs()
  connectWs()
  startPoll()
  await tryStartFromQuery()
})

onUnmounted(() => {
  stopPoll()
  if (activeId.value) wsUnsub(activeId.value)
  if (ws) { ws.close(); ws = null }
})

watch(() => route.query.conv, (id) => {
  if (id && id !== activeId.value) selectConv(String(id))
})
</script>

<style scoped>
.conv-tabs { display: flex; background: #f8f9fa; }
.conv-tab {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 8px;
  font-size: 0.9rem;
  color: #666;
}
.conv-tab.active { color: #198754; font-weight: 600; box-shadow: inset 0 -2px 0 #198754; background: #fff; }
.conv-list { max-height: 520px; overflow-y: auto; }
.conv-item.active { background: #e8f5e9; }
.conv-item.conv-unread { background: #fff8f8; }
.conv-item.conv-unread:not(.active):hover { background: #fff0f0; }
.unread-dot { width: 8px; height: 8px; border-radius: 50%; background: #dc3545; flex-shrink: 0; }
.read-state-badge { font-size: 0.72rem; padding: 2px 8px; border-radius: 10px; white-space: nowrap; flex-shrink: 0; }
.read-state-badge.unread { background: #dc3545; color: #fff; }
.read-state-badge.read { background: #e9ecef; color: #6c757d; }
.chat-panel { min-height: 520px; display: flex; flex-direction: column; }
.chat-body { flex: 1; max-height: 360px; overflow-y: auto; }
.appt-card { min-width: 200px; }
.msg-bubble { max-width: 85%; text-align: left; }
.msg-meta { font-size: 0.75rem; }
.msg-time { opacity: 0.75; }
.read-receipt { display: inline-flex; align-items: center; gap: 3px; padding: 1px 6px; border-radius: 8px; font-size: 0.72rem; }
.read-receipt.unread { background: rgba(255,255,255,0.25); color: rgba(255,255,255,0.9); }
.read-receipt.read { background: rgba(255,255,255,0.2); color: #d4edda; }
.msg-bubble.bg-light .read-receipt.unread { background: #fff3cd; color: #856404; }
.msg-bubble.bg-light .read-receipt.read { background: #e9ecef; color: #6c757d; }
.read-receipt.incoming-unread { background: #dc3545; color: #fff; }
.msg-img { max-width: 220px; max-height: 180px; border-radius: 8px; }
.msg-audio { max-width: 240px; height: 36px; }
.recall-btn { font-size: 0.75rem; }
</style>
