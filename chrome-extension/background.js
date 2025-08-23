// Пример: Логирование установки расширения
chrome.runtime.onInstalled.addListener(() => {
    console.log('[Background] Firefeed News Reader extension installed.');
    // Здесь можно инициализировать настройки по умолчанию в chrome.storage
  });
  
  // Пример: Логирование запуска расширения (например, при обновлении)
  chrome.runtime.onStartup.addListener(() => {
      console.log('[Background] Firefeed News Reader extension started up.');
  });
  
  // Пример: Прослушивание сообщений от popup или content scripts (если понадобится)
  // chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  //   if (request.action === "someAction") {
  //     // Обработка сообщения
  //     sendResponse({farewell: "goodbye"});
  //   }
  // });