// PWA 离线缓存：BooksList / BookDetail / Home 用 localStorage
const BOOKS_KEY = 'offline_books_list'
const BOOK_DETAIL_PREFIX = 'offline_book_'
const HOME_KEY = 'offline_home_books'

export function isOnline() {
  return typeof navigator !== 'undefined' ? navigator.onLine : true
}

export function saveBooksList(books, paramsKey = 'default') {
  // paramsKey 对应 BooksList 筛选条件
  try {
    localStorage.setItem(`${BOOKS_KEY}:${paramsKey}`, JSON.stringify({
      at: Date.now(),
      books: books || []
    }))
  } catch (_) {}
}

export function loadBooksList(paramsKey = 'default') {
  try {
    const raw = localStorage.getItem(`${BOOKS_KEY}:${paramsKey}`)
    if (!raw) return null
    const data = JSON.parse(raw)
    return data.books || null
  } catch (_) {
    return null
  }
}

export function saveBookDetail(id, book) {
  try {
    localStorage.setItem(`${BOOK_DETAIL_PREFIX}${id}`, JSON.stringify({ at: Date.now(), book }))
  } catch (_) {}
}

export function loadBookDetail(id) {
  try {
    const raw = localStorage.getItem(`${BOOK_DETAIL_PREFIX}${id}`)
    if (!raw) return null
    return JSON.parse(raw).book || null
  } catch (_) {
    return null
  }
}

export function saveHomeBooks(books) {
  try {
    localStorage.setItem(HOME_KEY, JSON.stringify({ at: Date.now(), books: books || [] }))
  } catch (_) {}
}

export function loadHomeBooks() {
  try {
    const raw = localStorage.getItem(HOME_KEY)
    if (!raw) return null
    return JSON.parse(raw).books || null
  } catch (_) {
    return null
  }
}
