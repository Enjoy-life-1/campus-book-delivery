<template>
  <div class="comment-section">
    <div class="comment-header">
      <h4>
        <i class="fa fa-comments"></i> 评论
        <span class="comment-count">({{ comments.length }})</span>
      </h4>
    </div>

    <!-- 评论输入框 -->
    <div v-if="isLoggedIn" class="comment-form">
      <div class="form-group">
        <textarea
          v-model="newComment"
          class="form-control"
          rows="4"
          placeholder="写下你的评论..."
          :disabled="submitting"
        ></textarea>
      </div>
      <div class="form-actions">
        <button
          class="btn btn-success"
          @click="submitComment"
          :disabled="!newComment.trim() || submitting"
        >
          <i class="fa fa-paper-plane"></i>
          {{ submitting ? '提交中...' : '发表评论' }}
        </button>
      </div>
    </div>
    <div v-else class="comment-login-prompt">
      <p>
        请先 <router-link to="/login">登录</router-link> 后发表评论
      </p>
    </div>

    <!-- 评论列表 -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-success" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
    </div>

    <div v-else-if="comments.length === 0" class="no-comments">
      <i class="fa fa-comment-o"></i>
      <p>暂无评论，快来发表第一条评论吧！</p>
    </div>

    <div v-else class="comments-list">
      <div
        v-for="comment in comments"
        :key="comment.id"
        class="comment-item"
        v-show="!comment.is_deleted"
      >
        <div class="comment-avatar">
          <i class="fa fa-user-circle"></i>
        </div>
        <div class="comment-content">
          <div class="comment-header-info">
            <strong class="comment-author">{{ comment.username }}</strong>
            <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          </div>
          <div class="comment-text">{{ comment.content }}</div>
          <div class="comment-actions">
            <button
              v-if="canDelete(comment)"
              class="btn btn-sm btn-link text-danger"
              @click="deleteComment(comment.id)"
            >
              <i class="fa fa-trash"></i> 删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 书籍详情评论：发表/删除；非 admin 需审核 pending
import { ref, onMounted, computed } from 'vue'
import { commentAPI } from '@/utils/api'
import { checkAuth, getCurrentUser } from '@/utils/auth'
import { refreshSession } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  bookId: {
    type: String,
    required: true
  }
})

const comments = ref([])
const newComment = ref('')
const loading = ref(false)
const submitting = ref(false)
const isLoggedIn = ref(false)
const { show } = useToast()

onMounted(async () => {
  const u = await refreshSession()
  isLoggedIn.value = !!u || checkAuth()
  loadComments()
})

function loadComments() {
  loading.value = true
  commentAPI.getComments(props.bookId)
    .then(response => {
      if (response.status === 'success') {
        // 过滤掉已删除的评论
        comments.value = response.comments.filter(c => !c.is_deleted)
      }
    })
    .catch(error => {
      console.error('加载评论失败:', error)
    })
    .finally(() => {
      loading.value = false
    })
}

async function submitComment() {
  // POST /api/comments；pending 时不立即刷新列表
  if (!newComment.value.trim() || submitting.value) return

  // 再次检查登录状态
  if (!isLoggedIn.value) {
    const u = await refreshSession()
    isLoggedIn.value = !!u
    if (!isLoggedIn.value) {
      show('请先登录', 'error')
      return
    }
  }

  submitting.value = true
  try {
    const response = await commentAPI.addComment({
      book_id: props.bookId,
      content: newComment.value.trim()
    })
    
    if (response.status === 'success') {
      newComment.value = ''
      show(response.message || '评论已发表', response.comment?.audit_status === 'pending' ? 'info' : 'success')
      if (response.comment?.audit_status === 'approved') loadComments()
    } else {
      show(response.message || '发表失败', 'error')
    }
  } catch (error) {
    show(error.message || '发表失败', 'error')
  } finally {
    submitting.value = false
  }
}

function deleteComment(commentId) {
  if (!confirm('确定要删除这条评论吗？')) return

  commentAPI.deleteComment(commentId)
    .then(response => {
      if (response.status === 'success') {
        // 重新加载评论列表
        loadComments()
      }
    })
    .catch(error => {
      alert(error.message || '删除评论失败，请重试')
    })
}

function canDelete(comment) {
  // 作者或管理员可删
  if (!isLoggedIn.value) return false
  const currentUser = getCurrentUser()
  if (!currentUser) return false
  
  // 检查是否是评论作者
  return String(comment.user_id) === String(currentUser.id) || currentUser.is_admin
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  
  const time = new Date(timeStr.replace(/-/g, '/'))
  const now = new Date()
  const diff = now - time
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 7) {
    return timeStr.split(' ')[0]
  } else if (days > 0) {
    return `${days}天前`
  } else if (hours > 0) {
    return `${hours}小时前`
  } else if (minutes > 0) {
    return `${minutes}分钟前`
  } else {
    return '刚刚'
  }
}
</script>

<style scoped>
.comment-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.comment-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.comment-header h4 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
}

.comment-header h4 i {
  color: #28a745;
  margin-right: 0.5rem;
}

.comment-count {
  color: #666;
  font-size: 0.9rem;
  font-weight: normal;
}

.comment-form {
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.comment-form textarea {
  resize: vertical;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.comment-form textarea:focus {
  border-color: #28a745;
  box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
}

.form-actions {
  margin-top: 0.5rem;
  text-align: right;
}

.comment-login-prompt {
  margin-bottom: 2rem;
  padding: 1rem;
  background: #fff3cd;
  border-radius: 8px;
  text-align: center;
}

.comment-login-prompt a {
  color: #28a745;
  font-weight: 600;
}

.no-comments {
  text-align: center;
  padding: 3rem 1rem;
  color: #999;
}

.no-comments i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #ddd;
}

.comments-list {
  space-y: 1rem;
}

.comment-item {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.comment-item:hover {
  background-color: #f8f9fa;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e9ecef;
  border-radius: 50%;
  font-size: 1.5rem;
  color: #6c757d;
}

.comment-content {
  flex: 1;
  min-width: 0;
}

.comment-header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.comment-author {
  color: #333;
  font-size: 0.95rem;
}

.comment-time {
  color: #999;
  font-size: 0.85rem;
}

.comment-text {
  color: #555;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: pre-wrap;
  margin-bottom: 0.5rem;
}

.comment-actions {
  display: flex;
  gap: 1rem;
}

.comment-actions .btn-link {
  padding: 0;
  font-size: 0.85rem;
  text-decoration: none;
}

.comment-actions .btn-link:hover {
  text-decoration: underline;
}
</style>

