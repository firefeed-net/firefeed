// --- Global variables ---
const API_BASE_URL = 'https://firefeed.net/api';
const SUPPORTED_LANGUAGES = ['ru', 'en', 'de', 'fr'];
const MAX_RECONNECT_ATTEMPTS = 5;
const WEBSOCKET_RECONNECT_DELAY = 3000;
const AUTO_UPDATE_STORAGE_KEY = 'fireFeedAutoUpdateEnabled';

let currentLanguage = 'en'; // Default to English
let currentCategory = '';
let currentSource = '';
let currentLimit = 50;
let currentOffset = 0;
let totalNewsCount = 0;
let autoUpdateEnabled = false;
let websocket = null;
let websocketReconnectAttempts = 0;

// --- Translations dictionary ---
const translations = {
  ru: {
    'header-title': 'Firefeed News',
    'language-label': 'Язык:',
    'source-label': 'Источник:',
    'category-label': 'Категория:',
    'limit-label': 'Навигация:',
    'auto-update-label': 'Автообновление',
    'all-sources': 'Все источники',
    'all-categories': 'Все категории',
    'loading': 'Загрузка новостей...',
    'no-news': 'Новости не найдены.',
    'no-title': 'Без заголовка',
    'no-description': 'Нет описания',
    'no-category': 'Без категории',
    'unknown-source': 'Неизвестный источник',
    'no-date': 'Нет даты',
    'read-more': 'Читать далее',
    'prev-page': 'Назад',
    'next-page': 'Далее'
  },
  en: {
    'header-title': 'Firefeed News',
    'language-label': 'Language:',
    'source-label': 'Source:',
    'category-label': 'Category:',
    'limit-label': 'Navigation:',
    'auto-update-label': 'Auto-update',
    'all-sources': 'All sources',
    'all-categories': 'All categories',
    'loading': 'Loading news...',
    'no-news': 'No news found.',
    'no-title': 'No title',
    'no-description': 'No description',
    'no-category': 'No category',
    'unknown-source': 'Unknown source',
    'no-date': 'No date',
    'read-more': 'Read more',
    'prev-page': 'Previous',
    'next-page': 'Next'
  },
  de: {
    'header-title': 'Firefeed News',
    'language-label': 'Sprache:',
    'source-label': 'Quelle:',
    'category-label': 'Kategorie:',
    'limit-label': 'Navigation:',
    'auto-update-label': 'Auto-Update',
    'all-sources': 'Alle Quellen',
    'all-categories': 'Alle Kategorien',
    'loading': 'Nachrichten werden geladen...',
    'no-news': 'Keine Nachrichten gefunden.',
    'no-title': 'Kein Titel',
    'no-description': 'Keine Beschreibung',
    'no-category': 'Keine Kategorie',
    'unknown-source': 'Unbekannte Quelle',
    'no-date': 'Kein Datum',
    'read-more': 'Weiterlesen',
    'prev-page': 'Zurück',
    'next-page': 'Weiter'
  },
  fr: {
    'header-title': 'Firefeed News',
    'language-label': 'Langue:',
    'source-label': 'Source:',
    'category-label': 'Catégorie:',
    'limit-label': 'Navigation:',
    'auto-update-label': 'Mise à jour auto',
    'all-sources': 'Toutes les sources',
    'all-categories': 'Toutes les catégories',
    'loading': 'Chargement des actualités...',
    'no-news': 'Aucune actualité trouvée.',
    'no-title': 'Pas de titre',
    'no-description': 'Pas de description',
    'no-category': 'Pas de catégorie',
    'unknown-source': 'Source inconnue',
    'no-date': 'Pas de date',
    'read-more': 'Lire la suite',
    'prev-page': 'Précédent',
    'next-page': 'Suivant'
  }
};

// --- DOM Elements ---
const languageSelect = document.getElementById('language-select');
const categorySelect = document.getElementById('category-select');
const sourceSelect = document.getElementById('source-select');
const autoUpdateCheckbox = document.getElementById('auto-update-checkbox');
const limitSelect = document.getElementById('limit-select');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const newsContainer = document.getElementById('news-container');
const loadingElement = document.getElementById('loading');
const errorElement = document.getElementById('error');

// --- Main initialization function ---
document.addEventListener('DOMContentLoaded', async function () {
  console.log('[Extension] Popup loaded');

  // 1. Set default language based on browser language (English fallback)
  setDefaultLanguage();

  // 2. Load sources, categories and auto-update state at startup
  await loadSources();
  await loadCategories();
  await loadAutoUpdateState();

  // 3. Set up event listeners
  languageSelect.addEventListener('change', onFilterChange);
  categorySelect.addEventListener('change', onFilterChange);
  sourceSelect.addEventListener('change', onFilterChange);
  limitSelect.addEventListener('change', onLimitChange);
  prevPageBtn.addEventListener('click', goToPrevPage);
  nextPageBtn.addEventListener('click', goToNextPage);

  if (autoUpdateCheckbox) {
    autoUpdateCheckbox.addEventListener('change', onAutoUpdateChange);
  }

  // 4. Set selected language in dropdown
  languageSelect.value = currentLanguage;
  limitSelect.value = currentLimit;

  // 5. Apply interface translations
  applyTranslations();

  // 6. Load news at startup
  await loadAndDisplayNews();
  setTimeout(connectWebSocket, 100);
});

// --- Function to apply translations ---
function applyTranslations() {
  const t = translations[currentLanguage];
  
  // Translate main interface elements
  document.getElementById('header-title').textContent = t['header-title'];
  document.getElementById('language-label').textContent = t['language-label'];
  document.getElementById('source-label').textContent = t['source-label'];
  document.getElementById('category-label').textContent = t['category-label'];
  document.getElementById('limit-label').textContent = t['limit-label'];
  document.getElementById('auto-update-label').textContent = t['auto-update-label'];
  prevPageBtn.textContent = t['prev-page'];
  nextPageBtn.textContent = t['next-page'];
  
  // Translate placeholders in selects
  const sourceOptions = sourceSelect.options;
  if (sourceOptions.length > 0) {
    sourceOptions[0].textContent = t['all-sources'];
  }
  
  const categoryOptions = categorySelect.options;
  if (categoryOptions.length > 0) {
    categoryOptions[0].textContent = t['all-categories'];
  }
  
  // Update loading text
  loadingElement.textContent = t['loading'];
}

// --- Function to set default language ---
function setDefaultLanguage() {
  // Get user's browser language
  const browserLanguage = navigator.language || navigator.userLanguage || 'en';
  console.log(`[Extension] Detected browser language: ${browserLanguage}`);
  
  // Extract language code (e.g., 'en' from 'en-US')
  const primaryLanguage = browserLanguage.split('-')[0].toLowerCase();
  
  // Check if the language is supported by our extension
  if (SUPPORTED_LANGUAGES.includes(primaryLanguage)) {
    currentLanguage = primaryLanguage;
    console.log(`[Extension] Using browser language: ${currentLanguage}`);
  } else {
    // Language not supported, use English as default
    currentLanguage = 'en';
    console.log(`[Extension] Language '${primaryLanguage}' not supported. Using default: 'en'.`);
  }
}

// --- Function to load auto-update state ---
async function loadAutoUpdateState() {
  try {
    const result = await chrome.storage.local.get([AUTO_UPDATE_STORAGE_KEY]);
    autoUpdateEnabled = result[AUTO_UPDATE_STORAGE_KEY] === true;
    if (autoUpdateCheckbox) {
      autoUpdateCheckbox.checked = autoUpdateEnabled;
    }
    console.log(`[Extension] Auto-update state loaded: ${autoUpdateEnabled}`);
  } catch (error) {
    console.error('[Extension] Error loading auto-update state:', error);
    autoUpdateEnabled = false;
    if (autoUpdateCheckbox) {
      autoUpdateCheckbox.checked = false;
    }
  }
}

// --- Function to load categories ---
async function loadCategories() {
  showLoading();
  hideError();
  try {
    const response = await fetch(`${API_BASE_URL}/categories/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    const categories = data.results || data;

    const t = translations[currentLanguage];
    categorySelect.innerHTML = `<option value="">${t['all-categories']}</option>`;

    categories.forEach(cat => {
      const option = document.createElement('option');
      option.value = cat.id;
      option.textContent = cat.name;
      categorySelect.appendChild(option);
    });
    console.log('[Extension] Categories loaded:', categories);
  } catch (error) {
    console.error('[Extension] Error loading categories:', error);
    showError(`Error loading categories: ${error.message}`);
  }
}

// --- Function to load sources ---
async function loadSources() {
  showLoading();
  hideError();
  try {
    const response = await fetch(`${API_BASE_URL}/sources/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    const sources = data.results || data;

    const t = translations[currentLanguage];
    sourceSelect.innerHTML = `<option value="">${t['all-sources']}</option>`;

    sources.forEach(source => {
      const option = document.createElement('option');
      option.value = source.id;
      option.textContent = source.description;
      sourceSelect.appendChild(option);
    });
    console.log('[Extension] Sources loaded:', sources);
  } catch (error) {
    console.error('[Extension] Error loading sources:', error);
    showError(`Error loading sources: ${error.message}`);
  }
}

// --- Filter change handler ---
async function onFilterChange() {
  currentLanguage = languageSelect.value;
  currentCategory = categorySelect.value;
  currentSource = sourceSelect.value;
  currentOffset = 0;
  
  console.log(`[Extension] Filters changed: lang=${currentLanguage}, cat=${currentCategory}, source=${currentSource}`);
  
  // Apply translations when language changes
  applyTranslations();
  
  await loadAndDisplayNews();
}

// --- Limit change handler ---
async function onLimitChange() {
  currentLimit = parseInt(limitSelect.value);
  currentOffset = 0;
  console.log(`[Extension] Limit changed to: ${currentLimit}`);
  await loadAndDisplayNews();
}

// --- Auto-update change handler ---
// --- Auto-update change handler ---
function onAutoUpdateChange() {
  autoUpdateEnabled = autoUpdateCheckbox.checked;
  
  chrome.storage.local.set({ [AUTO_UPDATE_STORAGE_KEY]: autoUpdateEnabled })
    .then(() => {
      console.log(`[Extension] Auto-update state saved: ${autoUpdateEnabled}`);
    })
    .catch(error => {
      console.error('[Extension] Error saving auto-update state:', error);
      autoUpdateCheckbox.checked = !autoUpdateEnabled;
    });
}

// --- Pagination handlers ---
async function goToPrevPage() {
  if (currentOffset >= currentLimit) {
    currentOffset -= currentLimit;
    await loadAndDisplayNews();
  }
}

async function goToNextPage() {
  if (currentOffset + currentLimit < totalNewsCount) {
    currentOffset += currentLimit;
    await loadAndDisplayNews();
  }
}

// --- Function to update pagination buttons state ---
function updatePaginationButtons(newsList) {
  prevPageBtn.disabled = currentOffset === 0;
  nextPageBtn.disabled = currentOffset + currentLimit >= totalNewsCount;
}

// --- Function to load and display news ---
async function loadAndDisplayNews() {
  showLoading();
  hideError();
  clearNewsContainer();

  try {
    let url = `${API_BASE_URL}/news/?display_language=${currentLanguage}`;
    if (currentCategory) {
      url += `&category_id=${encodeURIComponent(currentCategory)}`;
    }
    if (currentSource) {
      url += `&source_id=${encodeURIComponent(currentSource)}`;
    }
    url += `&limit=${currentLimit}&offset=${currentOffset}`;

    console.log(`[Extension] Fetching news from: ${url}`);
    const response = await fetch(url);

    if (!response.ok) {
      let errorMsg = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMsg = errorData.detail;
        }
      } catch (e) {}
      throw new Error(errorMsg);
    }

    const data = await response.json();
    console.log('[Extension] Raw API response:', data);
    
    let newsList;
    if (data.results) {
      newsList = data.results;
      totalNewsCount = data.count || newsList.length;
      console.log('[Extension] Total news count from API:', totalNewsCount);
      console.log('[Extension] News received in this page:', newsList.length);
    } else {
      newsList = Array.isArray(data) ? data : [];
      totalNewsCount = newsList.length;
      console.log('[Extension] News received (old format):', newsList.length);
    }

    console.log(`[Extension] Received ${newsList.length} news items.`);
    displayNews(newsList);
    updatePaginationButtons(newsList);

  } catch (error) {
    console.error('[Extension] Error fetching or displaying news:', error);
    showError(`Error loading news: ${error.message}`);
    totalNewsCount = 0;
    updatePaginationButtons([]);
  } finally {
    hideLoading();
  }
}

// --- Function to display news in DOM ---
function displayNews(newsList) {
  clearNewsContainer();

  const t = translations[currentLanguage];
  
  if (!newsList || newsList.length === 0) {
    newsContainer.innerHTML = `<p>${t['no-news']}</p>`;
    return;
  }

  newsList.forEach(item => {
    let title = item.original_title || t['no-title'];
    let content = item.original_content || t['no-description'];

    if (item.translations && item.translations[currentLanguage]) {
      const translation = item.translations[currentLanguage];
      title = translation.title || title;
      content = translation.content || content;
    }

    if (content.length > 300) {
        content = content.substring(0, 300) + '...';
    }

    const category = item.category || t['no-category'];
    const source = item.source ? item.source : t['unknown-source'];
    
    let dateStr = t['no-date'];
    if (item.published_at) {
        const date = new Date(item.published_at);
        // Format date according to language
        const dateOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        dateStr = date.toLocaleString(currentLanguage === 'en' ? 'en-US' : currentLanguage, dateOptions);
    }

    let imageHtml = '';
    if (item.image_url) {
      imageHtml = `<div class="news-image-container">
        <img src="${item.image_url}" alt="${escapeHtml(title)}" class="news-image" onerror="this.style.display='none'">
      </div>`;
    }

    const newsElement = document.createElement('div');
    newsElement.className = 'news-item';
    newsElement.innerHTML = `
      ${imageHtml}
      <div class="news-content-container">
        <div class="news-title">${escapeHtml(title)}</div>
        <div class="news-content">${escapeHtml(content)}</div>
        <div class="news-meta">
          <span class="news-source">${escapeHtml(source)}</span>
          <span class="news-category">${escapeHtml(category)}</span>
          <span class="news-date">${escapeHtml(dateStr)}</span>
        </div>
        ${item.source_url ? `<a href="${item.source_url}" target="_blank" rel="noopener noreferrer" class="news-link">${t['read-more']}</a>` : ''}
      </div>
    `;
    newsContainer.appendChild(newsElement);
  });
}

// --- Helper functions ---
function showLoading() {
  const t = translations[currentLanguage];
  loadingElement.textContent = t['loading'];
  loadingElement.style.display = 'block';
}

function hideLoading() {
  loadingElement.style.display = 'none';
}

function showError(message) {
  errorElement.textContent = message;
  errorElement.style.display = 'block';
  newsContainer.innerHTML = '';
  totalNewsCount = 0;
  updatePaginationButtons([]);
}

function hideError() {
  errorElement.style.display = 'none';
}

function clearNewsContainer() {
  newsContainer.innerHTML = '';
}

function escapeHtml(unsafe) {
  if (typeof unsafe !== 'string') return '';
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "<")
    .replace(/>/g, ">")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// WebSocket connection with error handling
function connectWebSocket() {
    if (websocket) {
        try {
            websocket.close();
        } catch (e) {
            console.log('[WebSocket] Error closing existing connection:', e);
        }
        websocket = null;
    }
    
    try {
        if (!window.WebSocket) {
            console.error('[WebSocket] WebSocket is not supported by your browser');
            return;
        }
        
        const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws/news';
        console.log('[WebSocket] Attempting to connect to:', wsUrl);
        
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function(event) {
            console.log('[WebSocket] Connected to server');
            websocketReconnectAttempts = 0;
            
            try {
                websocket.send(JSON.stringify({type: "hello", timestamp: new Date().toISOString()}));
            } catch (e) {
                console.error('[WebSocket] Error sending hello message:', e);
            }
        };
        
        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('[WebSocket] Received:', data);
                
                if (data.type === 'new_news') {
                    showNewsUpdateNotification(data.count || 0);
                } else if (data.type === 'pong') {
                    console.log('[WebSocket] Pong received');
                }
            } catch (e) {
                console.error('[WebSocket] Error parsing message:', e, 'Raw data:', event.data);
            }
        };
        
        websocket.onclose = function(event) {
            console.log('[WebSocket] Connection closed:', event.code, event.reason);
            websocket = null;
            
            if (websocketReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                websocketReconnectAttempts++;
                console.log(`[WebSocket] Attempting to reconnect (${websocketReconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
                setTimeout(connectWebSocket, WEBSOCKET_RECONNECT_DELAY);
            }
        };
        
        websocket.onerror = function(error) {
            console.error('[WebSocket] Error:', error);
            try {
                websocket.close();
            } catch (e) {
                console.error('[WebSocket] Error closing connection after error:', e);
            }
        };
        
    } catch (e) {
        console.error('[WebSocket] Connection failed:', e);
        websocket = null;
        
        if (websocketReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            websocketReconnectAttempts++;
            console.log(`[WebSocket] Retrying connection (${websocketReconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
            setTimeout(connectWebSocket, WEBSOCKET_RECONNECT_DELAY);
        }
    }
}

// Show news update notification
function showNewsUpdateNotification(count = 0) {
    const existingNotifications = document.querySelectorAll('.news-update-notification');
    existingNotifications.forEach(el => el.remove());
    
    const notification = document.createElement('div');
    notification.className = 'news-update-notification';
    
    // Determine notification text based on language
    const t = translations[currentLanguage];
    const notificationText = count > 0 ? 
        `🔥 ${t['header-title']}! (${count})` : 
        `🔥 ${t['header-title']}!`;
    
    notification.innerHTML = `
        <span>${notificationText}</span>
        <button id="refresh-news-btn" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-left: 10px;">${t['read-more']}</button>
        <button id="close-notification" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer; margin-left: 5px;">×</button>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 15px;
        border-radius: 8px;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-family: Arial, sans-serif;
        font-size: 14px;
    `;
    
    document.body.appendChild(notification);
    
    const refreshBtn = document.getElementById('refresh-news-btn');
    const closeBtn = document.getElementById('close-notification');
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            try {
                await loadAndDisplayNews();
            } catch (e) {
                console.error('[Notification] Error refreshing news:', e);
            }
            if (notification.parentNode) {
                notification.remove();
            }
        });
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.remove();
            }
        });
    }
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 15000);
}

window.addEventListener('beforeunload', function() {
    if (websocket) {
        try {
            if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
                websocket.close();
            }
        } catch (e) {
            console.error('[WebSocket] Error closing connection on unload:', e);
        }
        websocket = null;
    }
});