// --- Глобальные переменные ---
const API_BASE_URL = 'https://firefeed.net/api'; // Или http://localhost:8000/api для разработки
const SUPPORTED_LANGUAGES = ['ru', 'en', 'de', 'fr']; // Поддерживаемые языки API
let currentLanguage = 'en'; // Будет установлено ниже
let currentCategory = '';   // Категория по умолчанию (все)

// --- Элементы DOM ---
const languageSelect = document.getElementById('language-select');
const categorySelect = document.getElementById('category-select');
const newsContainer = document.getElementById('news-container');
const loadingElement = document.getElementById('loading');
const errorElement = document.getElementById('error');

// --- Основная функция инициализации ---
document.addEventListener('DOMContentLoaded', async function () {
  console.log('[Extension] Popup loaded');

  // 1. Определяем язык по умолчанию
  setDefaultLanguage();

  // 2. Загружаем категории при старте
  await loadCategories();

  // 3. Устанавливаем обработчики событий
  languageSelect.addEventListener('change', onFilterChange);
  categorySelect.addEventListener('change', onFilterChange);

  // 4. Устанавливаем выбранный язык в dropdown
  languageSelect.value = currentLanguage;

  // 5. Загружаем новости при старте
  await loadAndDisplayNews();
});

// --- Функция для установки языка по умолчанию ---
function setDefaultLanguage() {
  // Получаем язык браузера пользователя
  const browserLanguage = navigator.language || navigator.userLanguage || 'en';
  console.log(`[Extension] Detected browser language: ${browserLanguage}`);

  // Извлекаем код языка (например, 'en' из 'en-US')
  const primaryLanguage = browserLanguage.split('-')[0].toLowerCase();

  // Проверяем, поддерживается ли язык API
  if (SUPPORTED_LANGUAGES.includes(primaryLanguage)) {
    currentLanguage = primaryLanguage;
    console.log(`[Extension] Using primary language code: ${currentLanguage}`);
  } else {
    // Язык не поддерживается, используем 'en' по умолчанию
    currentLanguage = 'en';
    console.log(`[Extension] Language '${primaryLanguage}' not supported. Falling back to 'en'.`);
  }
}


// --- Функция загрузки списка категорий ---
async function loadCategories() {
  showLoading();
  hideError();
  try {
    const response = await fetch(`${API_BASE_URL}/categories/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const categories = await response.json();

    // Очищаем старые опции (кроме "Все категории")
    categorySelect.innerHTML = '<option value="">Все категории</option>';

    // Добавляем новые опции
    categories.forEach(cat => {
      const option = document.createElement('option');
      option.value = cat.category;
      option.textContent = cat.category;
      categorySelect.appendChild(option);
    });
    console.log('[Extension] Categories loaded:', categories);
  } catch (error) {
    console.error('[Extension] Error loading categories:', error);
    showError(`Ошибка загрузки категорий: ${error.message}`);
  }
}

// --- Обработчик изменения фильтров ---
async function onFilterChange() {
  currentLanguage = languageSelect.value;
  currentCategory = categorySelect.value;
  console.log(`[Extension] Filters changed: lang=${currentLanguage}, cat=${currentCategory}`);
  await loadAndDisplayNews();
}

// --- Функция загрузки и отображения новостей ---
async function loadAndDisplayNews() {
  showLoading();
  hideError();
  clearNewsContainer();

  try {
    let url = `${API_BASE_URL}/news/?display_language=${currentLanguage}`;
    if (currentCategory) {
      url += `&category=${encodeURIComponent(currentCategory)}`;
    }
    // Можно добавить limit, если нужно ограничить количество
    url += '&limit=20';

    console.log(`[Extension] Fetching news from: ${url}`);
    const response = await fetch(url);

    if (!response.ok) {
      // Попробуем получить детали ошибки из тела ответа
      let errorMsg = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMsg = errorData.detail;
        }
      } catch (e) {
        // Игнорируем ошибку парсинга JSON, если тело не JSON
      }
      throw new Error(errorMsg);
    }

    const newsList = await response.json();
    console.log(`[Extension] Received ${newsList.length} news items.`);
    displayNews(newsList);

  } catch (error) {
    console.error('[Extension] Error fetching or displaying news:', error);
    showError(`Ошибка загрузки новостей: ${error.message}`);
  } finally {
    hideLoading();
  }
}

// --- Функция отображения новостей в DOM ---
function displayNews(newsList) {
  clearNewsContainer();

  if (!newsList || newsList.length === 0) {
    newsContainer.innerHTML = '<p>Новости не найдены.</p>';
    return;
  }

  newsList.forEach(item => {
    // Определяем, какие поля использовать в зависимости от выбранного языка
    let titleKey = `title_${currentLanguage}`;
    let contentKey = `content_${currentLanguage}`;

    // Fallback на оригинальные данные, если перевод отсутствует
    const title = item[titleKey] || item.original_title || 'Без заголовка';
    let content = item[contentKey] || item.original_content || 'Нет описания';
    // Ограничиваем длину описания для popup
    if (content.length > 300) {
        content = content.substring(0, 300) + '...';
    }

    const category = item.category || 'Без категории';
    const source = item.source_url ? new URL(item.source_url).hostname : 'Неизвестный источник';
    // Форматируем дату
    let dateStr = 'Нет даты';
    if (item.published_at) {
        const date = new Date(item.published_at);
        // Простое форматирование, можно использовать библиотеки типа moment.js/date-fns
        dateStr = date.toLocaleString('ru-RU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    const newsElement = document.createElement('div');
    newsElement.className = 'news-item';
    newsElement.innerHTML = `
      <div class="news-title">${escapeHtml(title)}</div>
      <div class="news-content">${escapeHtml(content)}</div>
      <div class="news-meta">
        <span class="news-source">${escapeHtml(source)}</span>
        <span class="news-category">${escapeHtml(category)}</span>
        <span class="news-date">${escapeHtml(dateStr)}</span>
      </div>
      ${item.source_url ? `<a href="${item.source_url}" target="_blank" rel="noopener noreferrer" class="news-link">Читать далее</a>` : ''}
    `;
    newsContainer.appendChild(newsElement);
  });
}

// --- Вспомогательные функции ---
function showLoading() {
  loadingElement.style.display = 'block';
}

function hideLoading() {
  loadingElement.style.display = 'none';
}

function showError(message) {
  errorElement.textContent = message;
  errorElement.style.display = 'block';
  newsContainer.innerHTML = ''; // Очищаем контейнер новостей при ошибке
}

function hideError() {
  errorElement.style.display = 'none';
}

function clearNewsContainer() {
  newsContainer.innerHTML = '';
}

// --- Функция для экранирования HTML (безопасность) ---
function escapeHtml(unsafe) {
  if (typeof unsafe !== 'string') return '';
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "<")
    .replace(/>/g, ">")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
