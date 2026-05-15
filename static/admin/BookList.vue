<template>
  <div class="book-list">
    <!-- 搜索和筛选区域 -->
    <div class="search-filter">
      <div class="search-input">
        <input
          type="text"
          v-model="searchKeyword"
          placeholder="搜索书籍名称或作者..."
          class="form-control"
          @input="handleSearch"
        />
      </div>
      <div class="filter-select">
        <select v-model="selectedCategory" class="form-control" @change="handleFilter">
          <option value="">全部分类</option>
          <option v-for="category in categories" :key="category.id" :value="category.code">
            {{ category.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <p>加载中...</p>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- 书籍列表 -->
    <div v-else class="books-container">
      <div v-if="books.length === 0" class="no-data">
        <p>暂无数据</p>
      </div>
      <div v-else class="books-grid">
        <div v-for="book in books" :key="book.id" class="book-card">
          <div class="book-image">
            <!-- 这里可以添加书籍封面图片 -->
            <div class="image-placeholder">{{ book.title.charAt(0) }}</div>
          </div>
          <div class="book-info">
            <h3 class="book-title">{{ book.title }}</h3>
            <p class="book-author">作者：{{ book.author }}</p>
            <p class="book-category">分类：{{ getCategoryName(book.category) }}</p>
            <div class="book-footer">
              <span class="book-price">¥{{ book.price.toFixed(2) }}</span>
              <button class="btn btn-primary add-to-cart" @click="addToCart(book)">
                加入购物车
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="total > pageSize" class="pagination">
        <button
          class="btn btn-outline"
          :disabled="currentPage <= 1"
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        <span class="page-info">
          第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
        </span>
        <button
          class="btn btn-outline"
          :disabled="currentPage >= totalPages"
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { books, categories as categoriesApi, cart } from '../utils/api.js';

export default {
  name: 'BookList',
  setup() {
    // 响应式数据
    const books = ref([]);
    const categories = ref([]);
    const loading = ref(false);
    const error = ref('');
    const searchKeyword = ref('');
    const selectedCategory = ref('');
    const currentPage = ref(1);
    const pageSize = ref(10);
    const total = ref(0);

    // 计算总页数
    const totalPages = computed(() => {
      return Math.ceil(total.value / pageSize.value);
    });

    // 获取书籍列表
    const fetchBooks = async () => {
      loading.value = true;
      error.value = '';
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value
        };

        // 添加搜索和筛选参数
        if (searchKeyword.value) {
          params.keyword = searchKeyword.value;
        }
        if (selectedCategory.value) {
          params.category = selectedCategory.value;
        }

        const response = await books.getList(params);
        books.value = response.data || [];
        total.value = response.total || 0;
      } catch (err) {
        error.value = err.message || '获取书籍列表失败';
        console.error('获取书籍列表失败:', err);
      } finally {
        loading.value = false;
      }
    };

    // 获取分类列表
    const fetchCategories = async () => {
      try {
        const response = await categoriesApi.getList();
        categories.value = response.data || [];
      } catch (err) {
        console.error('获取分类列表失败:', err);
      }
    };

    // 根据分类代码获取分类名称
    const getCategoryName = (code) => {
      const category = categories.value.find(cat => cat.code === code);
      return category ? category.name : '未知分类';
    };

    // 处理搜索
    const handleSearch = () => {
      currentPage.value = 1;
      fetchBooks();
    };

    // 处理筛选
    const handleFilter = () => {
      currentPage.value = 1;
      fetchBooks();
    };

    // 切换页码
    const changePage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page;
        fetchBooks();
      }
    };

    // 添加到购物车
    const addToCart = async (book) => {
      try {
        await cart.add(book.id);
        alert('已添加到购物车');
      } catch (err) {
        alert(err.message || '添加失败，请先登录');
      }
    };

    // 组件挂载时获取数据
    onMounted(() => {
      fetchCategories();
      fetchBooks();
    });

    return {
      books,
      categories,
      loading,
      error,
      searchKeyword,
      selectedCategory,
      currentPage,
      pageSize,
      total,
      totalPages,
      getCategoryName,
      handleSearch,
      handleFilter,
      changePage,
      addToCart
    };
  }
};
</script>

<style scoped>
.book-list {
  width: 100%;
}

.search-filter {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
}

.filter-select {
  width: 200px;
}

.books-container {
  width: 100%;
}

.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.book-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.book-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.book-image {
  height: 180px;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-placeholder {
  font-size: 48px;
  color: #999;
  font-weight: bold;
}

.book-info {
  padding: 16px;
}

.book-title {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
  line-height: 1.4;
  height: 48px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.book-author {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.book-category {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
}

.book-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.book-price {
  font-size: 20px;
  font-weight: 500;
  color: #f56c6c;
}

.add-to-cart {
  padding: 6px 16px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
}

.page-info {
  font-size: 14px;
  color: #606266;
}

.no-data {
  text-align: center;
  padding: 60px;
  color: #909399;
  font-size: 16px;
}

@media (max-width: 768px) {
  .search-filter {
    flex-direction: column;
  }
  
  .filter-select {
    width: 100%;
  }
  
  .books-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
  }
  
  .book-title {
    font-size: 16px;
    height: 40px;
  }
  
  .book-footer {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .add-to-cart {
    width: 100%;
  }
}
</style>