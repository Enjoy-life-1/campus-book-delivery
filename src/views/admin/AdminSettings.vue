<template>
  <AdminLayout title="系统设置">
    <div class="page-header"><h2>系统设置</h2></div>
    <div class="row g-4">
      <div class="col-lg-5">
        <div class="admin-panel">
          <div class="admin-panel-title">基本设置</div>
          <form @submit.prevent="saveSettings">
            <div class="mb-3"><label class="form-label">系统名称</label><input v-model="settings.systemName" class="form-control"></div>
            <div class="mb-3"><label class="form-label">每页条数</label><input v-model.number="settings.pageSize" type="number" class="form-control" min="5" max="50"></div>
            <div class="form-check mb-2"><input v-model="settings.notify_email_enabled" class="form-check-input" type="checkbox" id="ne"><label class="form-check-label" for="ne">开启邮件推送（模拟）</label></div>
            <div class="form-check mb-3"><input v-model="settings.notify_sms_enabled" class="form-check-input" type="checkbox" id="ns"><label class="form-check-label" for="ns">开启短信推送</label></div>
            <div class="mb-3"><label class="form-label">ISBN 聚合 Key（聚合数据）</label><input v-model="settings.juhe_isbn_key" class="form-control" placeholder="juhe.cn 申请的 Key"></div>
            <div class="mb-3"><label class="form-label">ISBN 备用 Key（竹简 feelyou）</label><input v-model="settings.bamboo_isbn_apikey" class="form-control" placeholder="公众号「正版乔」获取的 apikey"></div>
            <hr class="my-3">
            <div class="small text-muted mb-2">阿里云短信（优先于 Webhook；Secret 请写在 .env 的 ALIBABA_CLOUD_ACCESS_KEY_SECRET）</div>
            <div class="mb-3"><label class="form-label">AccessKey ID</label><input v-model="settings.sms_access_key_id" class="form-control" placeholder="或 .env ALIBABA_CLOUD_ACCESS_KEY_ID"></div>
            <div class="mb-3"><label class="form-label">短信签名</label><input v-model="settings.sms_sign_name" class="form-control" placeholder="已审核签名"></div>
            <div class="mb-3"><label class="form-label">验证码模板 CODE</label><input v-model="settings.sms_template_code" class="form-control" placeholder="SMS_xxx，变量 ${code}"></div>
            <div class="mb-3"><label class="form-label">通知模板 CODE（可选）</label><input v-model="settings.sms_notify_template_code" class="form-control" placeholder="SMS_xxx，变量 ${content}"></div>
            <div class="mb-3"><label class="form-label">短信 Webhook（备用）</label><input v-model="settings.sms_webhook_url" class="form-control" placeholder="https://..."></div>
            <div class="mb-3"><label class="form-label">邮件 Webhook</label><input v-model="settings.email_webhook_url" class="form-control" placeholder="https://..."></div>
            <button type="submit" class="btn btn-success">保存</button>
          </form>
          <div class="border-top pt-3 mt-3">
            <div class="admin-panel-title mb-2">网关测试</div>
            <div class="mb-2">
              <select v-model="gwTest.channel" class="form-select form-select-sm">
                <option value="sms">短信</option>
                <option value="email">邮件</option>
              </select>
            </div>
            <input v-model="gwTest.recipient" class="form-control form-control-sm mb-2" :placeholder="gwTest.channel === 'sms' ? '手机号' : '邮箱'">
            <p v-if="gwTest.channel === 'sms'" class="small text-warning mb-2">Webhook 模式：先运行「启动短信Webhook.bat」，验证码在本窗口或 logs/sms_webhook.log，不会发到手机</p>
            <button type="button" class="btn btn-sm btn-outline-primary" :disabled="gwTesting" @click="testGw">发送测试</button>
          </div>
        </div>
      </div>
      <div class="col-lg-7">
        <div class="admin-panel">
          <div class="admin-panel-title d-flex justify-content-between">
            <span>推送记录（邮件/短信）</span>
            <div class="btn-group btn-group-sm">
              <button type="button" class="btn" :class="ch===''?'btn-success':'btn-outline-success'" @click="ch='';loadOutbox()">全部</button>
              <button type="button" class="btn" :class="ch==='email'?'btn-success':'btn-outline-success'" @click="ch='email';loadOutbox()">邮件</button>
              <button type="button" class="btn" :class="ch==='sms'?'btn-success':'btn-outline-success'" @click="ch='sms';loadOutbox()">短信</button>
            </div>
          </div>
          <div class="data-table" style="max-height:220px;overflow-y:auto">
            <table><thead><tr><th>用户</th><th>通道</th><th>状态</th><th>收件人</th><th>标题</th><th>时间</th><th></th></tr></thead>
              <tbody>
                <tr v-for="r in outbox" :key="r.id">
                  <td>{{ r.username }}</td>
                  <td>{{ r.channel }}</td>
                  <td><span class="badge" :class="statusBadge(r.status)">{{ r.status }}</span></td>
                  <td>{{ r.recipient }}</td>
                  <td class="text-truncate" style="max-width:100px">{{ r.title }}</td>
                  <td>{{ r.created_at }}</td>
                  <td><button v-if="r.status === 'failed'" type="button" class="btn btn-sm btn-outline-warning" @click="retry(r.id)">重试</button></td>
                </tr>
              </tbody>
            </table>
            <p v-if="!outbox.length" class="text-muted small p-2 mb-0">暂无推送记录</p>
          </div>
        </div>
        <div class="admin-panel">
          <div class="admin-panel-title">发布公告</div>
          <form @submit.prevent="addAnn">
            <input v-model="ann.title" class="form-control mb-2" placeholder="标题" required>
            <textarea v-model="ann.content" class="form-control mb-2" rows="3" placeholder="内容" required></textarea>
            <select v-model="ann.type" class="form-select mb-2">
              <option value="rule">平台规则</option>
              <option value="guide">使用指南</option>
              <option value="safety">安全提示</option>
            </select>
            <button type="submit" class="btn btn-outline-success">发布</button>
          </form>
        </div>
        <div class="admin-panel">
          <div class="admin-panel-title">已发布公告</div>
          <div v-for="a in annList" :key="a.id" class="border-bottom py-2 d-flex justify-content-between align-items-start">
            <div><strong>{{ a.title }}</strong><p class="small text-muted mb-0">{{ a.content.slice(0, 60) }}...</p></div>
            <button type="button" class="btn btn-sm btn-outline-danger" @click="delAnn(a.id)">删</button>
          </div>
          <p v-if="!annList.length" class="text-muted small mb-0">暂无公告</p>
        </div>
        <div class="admin-panel">
          <div class="admin-panel-title">分类管理</div>
          <form @submit.prevent="addCat" class="row g-2 mb-3">
            <div class="col-4"><input v-model="newCat.code" class="form-control" placeholder="代码" required></div>
            <div class="col-5"><input v-model="newCat.name" class="form-control" placeholder="名称" required></div>
            <div class="col-3"><button type="submit" class="btn btn-success w-100">添加</button></div>
          </form>
          <ul class="list-group">
            <li v-for="c in categories" :key="c.id" class="list-group-item d-flex justify-content-between align-items-center">
              {{ c.name }} <code>{{ c.code }}</code>
              <button type="button" class="btn btn-sm btn-outline-danger" @click="removeCat(c.id)">删除</button>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 系统设置：分类/公告/ISBN Key/SMS 等 KV
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI, categoryAPI } from '@/utils/api'
import { useToast } from '@/composables/useToast'
import { useSmsWebhookHint } from '@/composables/useSmsWebhookHint'

const { show } = useToast()
const { open: openSmsWebhookHint } = useSmsWebhookHint()
const settings = ref({
  systemName: '校园书递', pageSize: 10, notify_email_enabled: true, notify_sms_enabled: true,
  juhe_isbn_key: '', bamboo_isbn_apikey: '',
  sms_access_key_id: '', sms_sign_name: '', sms_template_code: '', sms_notify_template_code: '',
  sms_webhook_url: '', email_webhook_url: ''
})
const ann = ref({ title: '', content: '', type: 'guide' })
const newCat = ref({ code: '', name: '' })
const categories = ref([])
const annList = ref([])
const outbox = ref([])
const ch = ref('')
const gwTest = ref({ channel: 'sms', recipient: '' })
const gwTesting = ref(false)

function statusBadge(s) {
  return { sent: 'bg-success', failed: 'bg-danger', simulated: 'bg-secondary', skipped: 'bg-warning text-dark' }[s] || 'bg-secondary'
}

async function loadOutbox() {
  const res = await adminAPI.getNotifyOutbox(ch.value ? { channel: ch.value } : {})
  if (res.status === 'success') outbox.value = res.records || []
}

async function testGw() {
  if (!gwTest.value.recipient?.trim()) {
    show('请填写收件人', 'danger')
    return
  }
  gwTesting.value = true
  try {
    const r = await adminAPI.testGateway(gwTest.value)
    if (r.webhook_mode) openSmsWebhookHint(r.message)
    else show(r.message || '已发送', r.status === 'success' ? 'success' : 'danger')
    loadOutbox()
  } catch (e) { show(e.message || '失败', 'danger') }
  finally { gwTesting.value = false }
}

async function retry(id) {
  try {
    await adminAPI.retryOutbox(id)
    show('已重试', 'success')
    loadOutbox()
  } catch (e) { show(e.message || '重试失败', 'danger') }
}

async function load() {
  const s = await adminAPI.getSettings()
  if (s.status === 'success') {
    settings.value = { ...settings.value, ...s.settings }
    settings.value.notify_email_enabled = s.settings.notify_email_enabled !== false && s.settings.enableEmailNotification !== false
    settings.value.notify_sms_enabled = s.settings.notify_sms_enabled !== false
  }
  const c = await categoryAPI.getCategories()
  if (c.status === 'success') categories.value = c.categories || []
  const a = await adminAPI.getAnnouncements()
  if (a.status === 'success') annList.value = a.announcements || []
  loadOutbox()
}

async function delAnn(id) {
  if (!confirm('删除公告？')) return
  await adminAPI.deleteAnnouncement(id)
  show('已删除', 'info')
  load()
}

async function saveSettings() {
  const res = await adminAPI.saveSettings(settings.value)
  if (res.status === 'success') show('设置已保存', 'success')
}

async function addAnn() {
  const res = await adminAPI.addAnnouncement(ann.value)
  if (res.status === 'success') {
    show('公告已发布', 'success')
    ann.value = { title: '', content: '', type: 'guide' }
    load()
  }
}

async function addCat() {
  const res = await adminAPI.addCategory(newCat.value)
  if (res.status === 'success') {
    show('分类已添加', 'success')
    newCat.value = { code: '', name: '' }
    load()
  } else show(res.message, 'error')
}

async function removeCat(id) {
  if (!confirm('删除该分类？')) return
  await adminAPI.deleteCategory(id)
  show('已删除', 'info')
  load()
}

onMounted(load)
</script>
