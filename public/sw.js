// PWA Service Worker：静态资源 + 书籍列表 API 离线缓存
const CACHE = 'campus-book-v3'
const API_CACHE = 'campus-book-api-v1'

self.addEventListener('install', (e) => {
  e.waitUntil(self.skipWaiting())
})

self.addEventListener('activate', (e) => {
  // 清理旧版本 cache
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE && k !== API_CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
})

function isSpaNavigation(request, url) {
  return request.mode === 'navigate' || !url.pathname.includes('.')
}

function cacheableApi(url) {
  return url.pathname === '/api/books' && url.searchParams.has('page_size')
}

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return
  const u = new URL(e.request.url)
  if (u.origin !== location.origin) return

  if (u.pathname.startsWith('/api/')) {
    if (!cacheableApi(u)) return
    // 网络优先，失败回退缓存
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone()
            caches.open(API_CACHE).then((c) => c.put(e.request, copy))
          }
          return res
        })
        .catch(() => caches.match(e.request).then((hit) => hit || Response.error()))
    )
    return
  }

  if (u.pathname.startsWith('/assets/') || u.pathname.startsWith('/static/')) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone()
            caches.open(CACHE).then((c) => c.put(e.request, copy))
          }
          return res
        })
        .catch(() => caches.match(e.request))
    )
    return
  }

  if (isSpaNavigation(e.request, u)) {
    // SPA 导航：离线时 fallback index.html
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone()
            caches.open(CACHE).then((c) => c.put(e.request, copy))
          }
          return res
        })
        .catch(() => caches.match(e.request).then((hit) => hit || caches.match('/index.html')))
    )
    return
  }

  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)))
})
