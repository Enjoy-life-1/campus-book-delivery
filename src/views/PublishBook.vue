<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4 publish-wrap">
      <h2 class="mb-4">{{ isEdit ? '编辑书籍' : '发布闲置书籍' }}</h2>
      <div v-if="banNotice" class="alert alert-danger">
        <strong><i class="fa fa-ban me-1"></i>{{ banNotice.title }}</strong>
        <p class="mb-0 small mt-1">{{ banNotice.detail }} 请前往账户设置提交申诉。</p>
      </div>
      <form @submit.prevent="handleSubmit" class="publish-form card p-4 shadow-sm">
        <div v-if="!isEdit" class="row g-2 mb-3">
          <div class="col-md-6">
            <label class="form-label small">发布模板</label>
            <select class="form-select form-select-sm" @change="applyTemplate($event)">
              <option value="">选择模板快速填充</option>
              <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <div class="col-md-6 d-flex align-items-end">
            <div class="form-check">
              <input v-model="isBundle" class="form-check-input" type="checkbox" id="bundleCk">
              <label class="form-check-label" for="bundleCk">教材套装（多本一起卖）</label>
            </div>
          </div>
        </div>
        <div v-if="isBundle" class="mb-3">
          <label class="form-label">套装书目（每行：书名|作者）</label>
          <textarea v-model="bundleText" class="form-control" rows="3" placeholder="高等数学|张三&#10;线性代数|李四"></textarea>
        </div>
        <div v-if="publishHints.warnings.length || publishHints.tips.length" class="mb-3">
          <div v-for="(w,i) in publishHints.warnings" :key="'pw'+i" class="alert alert-warning py-2 small mb-1">{{ w }}</div>
          <div v-for="(t,i) in publishHints.tips" :key="'pt'+i" class="alert alert-info py-2 small mb-1">{{ t }}</div>
        </div>
        <div class="row g-3">
          <div class="col-md-8">
            <div class="mb-3">
              <label class="form-label">ISBN</label>
              <div class="input-group">
                <input v-model="form.isbn" class="form-control" placeholder="输入ISBN后点查询自动填书">
                <button type="button" class="btn btn-outline-success" :disabled="isbnLoading" @click="fillByIsbn">
                  <i :class="['fa', isbnLoading ? 'fa-spinner fa-spin' : 'fa-barcode']"></i> 查询填书
                </button>
                <IsbnScanner @scan="onIsbnScan" />
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">书名 <span class="text-danger">*</span></label>
              <input v-model="form.title" class="form-control" placeholder="如：九成新高等数学" required>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">作者</label>
                <input v-model="form.author" class="form-control" placeholder="选填">
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">版次/出版年</label>
                <input v-model="form.edition" class="form-control" placeholder="如：第7版 / 2022">
              </div>
            </div>
            <div class="row">
              <div class="col-md-4 mb-3">
                <label class="form-label">关联课程</label>
                <select v-model="form.course_code" class="form-select">
                  <option value="">不关联</option>
                  <option v-for="c in courseList" :key="c.course_code" :value="c.course_code">{{ c.course_name }}</option>
                </select>
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">分类 <span class="text-danger">*</span></label>
                <select v-model="form.category" class="form-select" required>
                  <option v-for="c in cats" :key="c.code" :value="c.code">{{ c.name }}</option>
                </select>
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">成色 <span class="text-danger">*</span></label>
                <select v-model="form.condition" class="form-select" required>
                  <option v-for="o in conditionOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
              </div>
            </div>
            <div class="row">
              <div class="col-md-4 mb-3">
                <label class="form-label">价格（元）<span class="text-danger">*</span></label>
                <input v-model.number="form.price" type="number" step="0.01" min="0.01" class="form-control" required>
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">校区</label>
                <select v-model="form.campus_zone" class="form-select">
                  <option value="西校区">西校区</option>
                  <option value="北校区">北校区</option>
                  <option value="校外">校外</option>
                </select>
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">宿舍楼栋</label>
                <select v-model="form.dorm_building" class="form-select">
                  <option value="">不标注</option>
                  <option v-for="d in filteredDorms" :key="d" :value="d">{{ d }}</option>
                </select>
              </div>
            </div>
            <div class="row mb-3" v-if="!isEdit && campaigns.length">
              <div class="col-md-6">
                <label class="form-label">学期专场</label>
                <select v-model="form.campaign_tag" class="form-select">
                  <option value="">不参与</option>
                  <option v-for="c in campaigns" :key="c.tag" :value="c.tag">{{ c.title }}</option>
                </select>
              </div>
              <div class="col-md-6" v-if="form.enable_drop">
                <label class="form-label">倒计时降价目标价</label>
                <input v-model.number="form.drop_price" type="number" step="0.01" class="form-control" placeholder="低于现价">
              </div>
            </div>
            <div v-if="!isEdit" class="form-check mb-3">
              <input v-model="form.enable_drop" class="form-check-input" type="checkbox" id="dropCheck">
              <label class="form-check-label" for="dropCheck">开启72小时倒计时降价（需审核通过后生效）</label>
            </div>
            <div class="mb-3">
              <label class="form-label">描述 <span class="text-danger">*</span></label>
              <textarea v-model="form.desc" class="form-control" rows="4" placeholder="新旧程度、笔记、瑕疵等" required></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">联系方式 <span class="text-danger">*</span></label>
              <input v-model="form.contact" class="form-control" placeholder="手机号或微信" required>
            </div>
          </div>
          <div class="col-md-4">
            <ImageUploader ref="uploaderRef" label="书籍图片" :required="true" />
            <img v-if="isbnCover" :src="isbnCover" class="img-fluid mt-2 rounded border" alt="封面预览">
          </div>
        </div>
        <p v-if="!isEdit" class="text-muted small"><i class="fa fa-info-circle"></i> 提交后需管理员审核通过后才会上架展示</p>
        <div class="d-flex gap-2">
          <button type="submit" class="btn btn-success px-4" :disabled="loading || !!banNotice">
            <i class="fa fa-paper-plane"></i> {{ loading ? '提交中...' : (isEdit ? '保存修改' : '提交发布') }}
          </button>
          <router-link to="/myBooks" class="btn btn-outline-secondary">取消</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
// 发布/编辑书籍：ISBN 填书、套装、降价、审核上架
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import ImageUploader from '@/components/ImageUploader.vue'
import { bookAPI, categoryAPI, campusAPI, sellerAPI, discoveryAPI } from '@/utils/api'
import { conditionOptions } from '@/utils/helpers'
import { getCurrentUser } from '@/utils/auth'
import { normalizeCampusZone, dormsForZone, syncDormToZone } from '@/utils/campus'
import { useToast } from '@/composables/useToast'
import { useIsbnLookup } from '@/composables/useIsbnLookup'
import IsbnScanner from '@/components/IsbnScanner.vue'
import { getBanNotice, isBanned } from '@/utils/banStatus'
import { refreshSession } from '@/composables/useAuth'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

const route = useRoute()
const router = useRouter()
const { show } = useToast()
const { profile } = storeToRefs(useUserStore())
const banNotice = computed(() => (isBanned(profile.value) ? getBanNotice(profile.value) : null))
const { loading: isbnLoading, lookup } = useIsbnLookup()
const uploaderRef = ref(null)
const isEdit = computed(() => !!route.query.edit)
const cats = ref([{ code: 'textbook', name: '教材教辅' }])
const courseList = ref([])
const dormCatalog = ref(null)
const filteredDorms = computed(() => dormsForZone(dormCatalog.value, form.value.campus_zone))
const campaigns = ref([])
const isbnCover = ref('')
const loading = ref(false)
const templates = ref([])
const isBundle = ref(false)
const bundleText = ref('')
const form = ref({
  title: '', author: '', isbn: '', edition: '', category: 'textbook', condition: 'like_new',
  course_code: '', campus_zone: '西校区', dorm_building: '', campaign_tag: '',
  price: null, desc: '', contact: '', enable_drop: false, drop_price: null
})
const publishHints = ref({ warnings: [], tips: [] })
let hintsTimer = null

async function refreshHints() {
  const res = await discoveryAPI.publishHints({
    isbn: form.value.isbn,
    course_code: form.value.course_code,
    edition: form.value.edition,
    title: form.value.title,
    price: form.value.price,
    category: form.value.category
  }).catch(() => null)
  if (res?.status === 'success') {
    publishHints.value = { warnings: res.warnings || [], tips: res.tips || [] }
  }
}

watch(() => [form.value.isbn, form.value.course_code, form.value.edition, form.value.title, form.value.price], () => {
  clearTimeout(hintsTimer)
  hintsTimer = setTimeout(refreshHints, 400)
})

watch(() => form.value.campus_zone, () => syncDormToZone(form.value, dormCatalog.value))

function onIsbnScan(code) {
  form.value.isbn = code
  fillByIsbn()
}

async function fillByIsbn() {
  // /api/isbn → 自动填书名作者封面
  const r = await lookup(form.value.isbn, (b) => {
    if (b.title) form.value.title = b.title
    if (b.author) form.value.author = b.author
    if (b.isbn) form.value.isbn = b.isbn
    if (b.edition) form.value.edition = b.edition
    if (b.desc && !form.value.desc) form.value.desc = b.desc
    if (b.cover_url) isbnCover.value = b.cover_url
  })
  if (r.ok) show('已自动填充图书信息', 'success')
  else show(r.message, 'warning')
}

async function loadCats() {
  const res = await categoryAPI.getCategories()
  if (res.status === 'success' && res.categories?.length) cats.value = res.categories
  if (route.query.category && !isEdit.value) form.value.category = route.query.category
  if (route.query.isbn) form.value.isbn = route.query.isbn
  if (route.query.title) form.value.title = decodeURIComponent(route.query.title)
}

async function loadEdit() {
  if (!route.query.edit) return
  const res = await bookAPI.getBookDetail(route.query.edit)
  if (res.status === 'success' && res.book) {
    const b = res.book
    form.value = {
      title: b.title, author: b.author, isbn: b.isbn || '', edition: b.edition || '',
      category: b.category, course_code: b.course_code || '',
      campus_zone: normalizeCampusZone(b.campus_zone), dorm_building: b.dorm_building || '',
      campaign_tag: b.campaign_tag || '', condition: b.condition || 'like_new', price: b.price,
      desc: b.desc || b.description, contact: b.contact, enable_drop: false, drop_price: null
    }
    uploaderRef.value?.setFromUrls(b.imgs || [])
    syncDormToZone(form.value, dormCatalog.value)
  }
}

function parseBundle() {
  if (!isBundle.value || !bundleText.value.trim()) return []
  return bundleText.value.trim().split('\n').map(line => {
    const [title, author] = line.split('|').map(s => s.trim())
    return { title: title || line.trim(), author: author || '' }
  }).filter(x => x.title)
}

function applyTemplate(e) {
  const t = templates.value.find(x => x.id === e.target.value)
  if (!t?.payload) return
  const p = t.payload
  form.value = { ...form.value, ...p, price: p.price ?? form.value.price }
  if (p.bundle_items?.length) {
    isBundle.value = true
    bundleText.value = p.bundle_items.map(i => `${i.title}|${i.author || ''}`).join('\n')
  }
  e.target.value = ''
}

async function handleSubmit() {
  // 新建走 addBook（待审核）；可选 setPriceDrop
  if (banNotice.value) {
    show('账号已封禁，无法发布书籍', 'warning')
    return
  }
  const imgs = uploaderRef.value?.getUrls() || []
  if (!imgs.length) return show('请至少上传一张图片', 'error')
  loading.value = true
  try {
    const data = { ...form.value, imgs, listing_type: isBundle.value ? 'bundle' : 'single', bundle_items: parseBundle() }
    delete data.enable_drop
    delete data.drop_price
    const res = isEdit.value
      ? await bookAPI.updateBook(route.query.edit, data)
      : await bookAPI.addBook(data)
    if (res.status === 'success') {
      const bookId = res.book_id || res.book?.id
      if (!isEdit.value && form.value.enable_drop && form.value.drop_price && bookId) {
        await campusAPI.setPriceDrop(bookId, { hours: 72, target_price: form.value.drop_price })
      }
      show(res.message || (isEdit.value ? '更新成功' : '已提交审核'), 'success')
      router.push('/myBooks')
    } else show(res.message || '失败', 'error')
  } catch (e) {
    show(e.message || '提交失败', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await refreshSession()
  const u = getCurrentUser()
  if (u?.campus_zone) form.value.campus_zone = normalizeCampusZone(u.campus_zone)
  if (u?.dorm_building) form.value.dorm_building = u.dorm_building
  const tr = await sellerAPI.getTemplates()
  if (tr.status === 'success') templates.value = tr.templates || []
  const [cr, dr, sm] = await Promise.all([
    campusAPI.getCourses(),
    campusAPI.getDorms(),
    campusAPI.getSemester()
  ])
  if (cr.status === 'success') courseList.value = cr.courses || []
  if (dr.status === 'success') dormCatalog.value = dr
  syncDormToZone(form.value, dormCatalog.value)
  if (sm.status === 'success') campaigns.value = sm.campaigns || []
  await loadCats()
  await loadEdit()
  if (route.query.isbn && !isEdit.value) fillByIsbn()
})
</script>

<style scoped>
.publish-wrap { max-width: 960px; }
</style>
