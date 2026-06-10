<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4 mb-5 ai-wrap">
      <h2 class="text-success mb-1"><i class="fa fa-magic"></i> 智能找书</h2>
      <p class="text-muted small mb-3">
        根据在售书籍、课程教材与平台说明回答；未配置大模型时使用检索摘要。
        <span v-if="aiStatus.llm" class="badge bg-success ms-1">{{ aiStatus.provider === 'dashscope' ? '通义' : 'LLM' }}</span>
        <span v-else class="badge bg-secondary ms-1">检索模式</span>
        <span v-if="aiStatus.model" class="text-muted ms-1">{{ aiStatus.model }}</span>
        <span class="ms-2">索引 {{ aiStatus.indexed_count || 0 }} 条</span>
      </p>

      <div class="card shadow-sm mb-3 chat-box">
        <div ref="scrollEl" class="chat-messages p-3">
          <div v-if="!messages.length" class="text-muted text-center py-5">
            例如：西校区软件工程大一要买什么书？ / 数据结构二手书多少钱？ / 如何学籍认证？
          </div>
          <div
            v-for="(m, i) in messages"
            :key="i"
            class="mb-3"
            :class="m.role === 'user' ? 'text-end' : ''"
          >
            <div class="d-inline-block text-start p-2 rounded" :class="m.role === 'user' ? 'bg-success text-white' : 'bg-light'">
              <pre class="mb-0 chat-text">{{ m.content }}</pre>
            </div>
            <div v-if="m.sources?.length" class="mt-2 small">
              <div class="text-muted mb-1">参考来源：</div>
              <router-link
                v-for="s in m.sources"
                :key="s.id"
                :to="s.link || '/booksList'"
                class="badge bg-outline-success border text-success text-decoration-none me-1 mb-1"
              >
                {{ s.title || s.type }}
              </router-link>
            </div>
          </div>
          <div v-if="loading" class="text-muted small"><i class="fa fa-spinner fa-spin"></i> 思考中…</div>
        </div>
        <div class="card-footer bg-white">
          <form class="d-flex gap-2" @submit.prevent="send">
            <input
              v-model="input"
              type="text"
              class="form-control"
              placeholder="输入问题…"
              maxlength="500"
              :disabled="loading"
            />
            <button type="submit" class="btn btn-success" :disabled="loading || input.trim().length < 2">
              发送
            </button>
          </form>
        </div>
      </div>

      <div class="d-flex flex-wrap gap-2">
        <button
          v-for="q in quickQs"
          :key="q"
          type="button"
          class="btn btn-outline-success btn-sm"
          @click="askQuick(q)"
        >
          {{ q }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
// RAG 智能找书：/api/ai/ask，展示 sources 链接
import { ref, onMounted, nextTick } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { aiAPI } from '@/utils/api'

const input = ref('')
const loading = ref(false)
const messages = ref([])
const scrollEl = ref(null)
const aiStatus = ref({ indexed_count: 0, llm: false })

const quickQs = [
  '西校区计算机专业教材',
  '如何面交转让',
  '学籍认证怎么做',
  '按课找书在哪',
]

async function scrollBottom() {
  await nextTick()
  const el = scrollEl.value
  if (el) el.scrollTop = el.scrollHeight
}

async function send() {
  // 追加 user 消息 → aiAPI.ask → assistant + 参考来源
  const q = input.value.trim()
  if (q.length < 2 || loading.value) return
  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true
  await scrollBottom()
  try {
    const res = await aiAPI.ask({ question: q })
    messages.value.push({
      role: 'assistant',
      content: res.answer || '暂无回答',
      sources: res.sources || [],
    })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: e.message || '请求失败' })
  } finally {
    loading.value = false
    scrollBottom()
  }
}

function askQuick(q) {
  input.value = q
  send()
}

onMounted(async () => {
  // 拉 RAG 索引数、LLM 是否配置
  try {
    const st = await aiAPI.status()
    aiStatus.value = st
  } catch {
    /* ignore */
  }
})
</script>

<style scoped>
.ai-wrap { max-width: 800px; }
.chat-box { min-height: 420px; }
.chat-messages { max-height: 480px; overflow-y: auto; min-height: 320px; }
.chat-text { white-space: pre-wrap; font-family: inherit; font-size: 0.95rem; background: transparent; border: 0; }
</style>
