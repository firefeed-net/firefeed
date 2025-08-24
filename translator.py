from transformers import MarianMTModel, MarianTokenizer
from firefeed_utils import clean_html
from functools import lru_cache
import asyncio
import torch
import nltk
import os
from config import CHANNEL_IDS

# Установка пути для данных NLTK
nltk_data_path = '/var/www/firefeed/data/nltk_data'
os.environ['NLTK_DATA'] = nltk_data_path

# Скачивание необходимых ресурсов
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', download_dir=nltk_data_path)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', download_dir=nltk_data_path)

# Глобальный флаг для однократной инициализации устройства
_device = None

def _get_device():
    """Определяет и кэширует устройство для моделей."""
    global _device
    if _device is None:
        # Проверяем доступность CUDA (если вы планируете использовать GPU)
        # if torch.cuda.is_available():
        #     _device = "cuda"
        # else:
        #     _device = "cpu"
        # Для простоты и избежания проблем с многопоточностью на GPU, используем CPU
        _device = "cpu"
        print(f"[TRANSLATOR] Модели будут загружаться на устройство: {_device}")
    return _device

_model_cache = {}
_tokenizer_cache = {}
_translation_cache = {}
_model_load_lock = asyncio.Lock()

# Языковые пары, требующие каскадного перевода через английский
CASCADE_TRANSLATIONS = {
    ('ru', 'de'): ('ru', 'en', 'de')
}

def get_translator_model(src_lang, tgt_lang):
    """Получает модель и токенизатор для перевода. Потокобезопасна."""
    cache_key = f"{src_lang}-{tgt_lang}"
    if cache_key not in _model_cache:
        # Используем блокировку, чтобы избежать одновременной загрузки одной и той же модели несколькими потоками
        # Это важно, если run_in_executor запустит несколько translate_text одновременно
        # для одной и той же пары языков, прежде чем модель будет закэширована.
        # asyncio.Lock не работает внутри run_in_executor (разные потоки), 
        # поэтому используем threading.Lock
        import threading
        if not hasattr(get_translator_model, '_thread_lock'):
             get_translator_model._thread_lock = threading.Lock()
        
        with get_translator_model._thread_lock:
            # Повторная проверка, может быть загружена пока ждали лок
            if cache_key not in _model_cache:
                try:
                    model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
                    print(f"[TRANSLATOR] Загрузка модели {model_name}...")
                    
                    # Явно указываем устройство и отключаем ленивую загрузку
                    # Это должно предотвратить появление meta tensors
                    model = MarianMTModel.from_pretrained(
                        model_name,
                        # device_map=None, # Явно отключаем автоматическое распределение
                        # low_cpu_mem_usage=False, # Отключаем экономию памяти при загрузке
                        # torch_dtype=None # Используем тип данных по умолчанию
                    )
                    tokenizer = MarianTokenizer.from_pretrained(model_name)
                    
                    # Явно перемещаем модель на выбранное устройство (CPU)
                    device = _get_device()
                    model = model.to(device)
                    print(f"[TRANSLATOR] Модель {model_name} загружена и перемещена на {device}.")
                    
                    _model_cache[cache_key] = model
                    _tokenizer_cache[cache_key] = tokenizer
                    
                except Exception as e:
                    print(f"[ERROR] [TRANSLATOR] Ошибка загрузки модели {model_name}: {e}")
                    # Можно залогировать traceback для деталей
                    import traceback
                    traceback.print_exc()
                    # Возвращаем None, чтобы функция вызова могла обработать ошибку
                    return None, None
    return _model_cache[cache_key], _tokenizer_cache[cache_key]

def translate_with_context(texts, source_lang='en', target_lang='ru', context_window=2):
    """
    Переводит список текстов с учётом контекста.
    
    Args:
        texts (list): Список предложений для перевода.
        context_window (int): Количество предыдущих предложений для контекста.
    """
    # Проверяем, нужен ли каскадный перевод
    cascade_key = (source_lang, target_lang)
    if cascade_key in CASCADE_TRANSLATIONS:
        # Используем каскадный перевод через английский
        src_lang, intermediate_lang, tgt_lang = CASCADE_TRANSLATIONS[cascade_key]
        
        # Переводим на промежуточный язык (английский)
        intermediate_texts = translate_with_context(texts, src_lang, intermediate_lang, context_window)
        
        # Переводим с промежуточного на целевой язык
        return translate_with_context(intermediate_texts, intermediate_lang, tgt_lang, context_window)
    
    model, tokenizer = get_translator_model(source_lang, target_lang)
    if model is None or tokenizer is None:
        return texts  # Если модель не найдена, возвращаем исходный текст
    
    translated = []
    
    for i in range(len(texts)):
        context = " ".join(texts[max(0, i-context_window):i])
        current_text = texts[i]
        
        combined = f"{context} {current_text}" if context else current_text
        
        inputs = tokenizer(combined, return_tensors="pt", truncation=True, max_length=512)

        # Перемещаем inputs на то же устройство, что и модель
        device = next(model.parameters()).device # Получаем устройство модели
        inputs = {k: v.to(device) for k, v in inputs.items()} # Перемещаем тензоры

        with torch.no_grad():
            outputs = model.generate(**inputs)
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Удаляем контекст из результата (если нужно)
        if context:
            # Это упрощённый подход - в реальности может потребоваться более сложная постобработка
            translated_text = translated_text.replace(translate_text(context, source_lang, target_lang), "").strip()
        
        translated.append(translated_text)
    
    return translated

# @lru_cache(maxsize=1000)
def cached_translate_text(text, source_lang, target_lang):
    return translate_text(text, source_lang, target_lang)

def translate_text(text, source_lang='en', target_lang='ru', context_window=2):
    if source_lang == target_lang:
        return clean_html(text)

    cache_key = f"{source_lang}_{target_lang}_{hash(text)}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    # Проверяем, нужен ли каскадный перевод
    cascade_key = (source_lang, target_lang)
    if cascade_key in CASCADE_TRANSLATIONS:
        # Используем каскадный перевод через английский
        src_lang, intermediate_lang, tgt_lang = CASCADE_TRANSLATIONS[cascade_key]
        
        # Переводим на промежуточный язык (английский)
        intermediate_text = translate_text(text, src_lang, intermediate_lang, context_window)
        
        # Переводим с промежуточного на целевой язык
        result = translate_text(intermediate_text, intermediate_lang, tgt_lang, context_window)
    else:
        sentences = nltk.sent_tokenize(text)
        translated = " ".join(translate_with_context(sentences, source_lang, target_lang, context_window))
        result = clean_html(translated)

    _translation_cache[cache_key] = result
    return result

async def prepare_translations(title: str, description: str, category: str, original_lang: str) -> dict:
    """
    Подготавливает переводы заголовка, описания и категории на все целевые языки.
    Оборачивает синхронные вызовы translate_text в run_in_executor.

    :param title: Оригинальный заголовок.
    :param description: Оригинальное описание.
    :param category: Категория (предположительно на английском).
    :param original_lang: Оригинальный язык новости.
    :return: Словарь переводов вида {
        'ru': {'title': '...', 'description': '...', 'category': '...'},
        'en': {...},
        ...
    }
    """
    translations = {}
    target_languages = list(CHANNEL_IDS.keys()) # ['ru', 'en', 'de', 'fr']

    # Очищаем оригинальный текст один раз
    clean_title = clean_html(title)
    clean_description = clean_html(description)

    # Получаем ссылку на текущий event loop
    loop = asyncio.get_event_loop()

    # Создаем список задач для параллельного выполнения всех переводов
    translation_tasks = []

    for target_lang in target_languages:
        # Копируем оригинальные данные на случай, если перевод не нужен или произойдет ошибка
        trans_title = clean_title
        trans_description = clean_description
        trans_category = category

        needs_translation = original_lang != target_lang

        if needs_translation:
            # Создаем задачи для асинхронного выполнения синхронных функций в пуле потоков
            title_task = loop.run_in_executor(None, translate_text, clean_title, original_lang, target_lang)
            desc_task = loop.run_in_executor(None, translate_text, clean_description, original_lang, target_lang)
            # Переводим категорию, если она не на целевом языке (предполагаем 'en' как базовый для категорий)
            cat_task = loop.run_in_executor(None, translate_text, category, 'en', target_lang) 
            
            # Сохраняем задачи и связанный с ними язык
            translation_tasks.append((target_lang, title_task, desc_task, cat_task))
        else:
            # Если перевод не нужен, просто сохраняем оригиналы
            translations[target_lang] = {
                'title': trans_title,
                'description': trans_description,
                'category': trans_category
            }
            print(f"[LOG] Перевод с {original_lang} на {target_lang} не требуется. Используются оригинальные данные.")

    # Дожидаемся завершения всех задач перевода
    for target_lang, title_task, desc_task, cat_task in translation_tasks:
        try:
            # Дожидаемся результата каждой задачи
            trans_title = await title_task
            trans_description = await desc_task
            trans_category = await cat_task

            # Сохраняем результаты перевода
            translations[target_lang] = {
                'title': trans_title,
                'description': trans_description,
                'category': trans_category
            }
            print(f"[LOG] Перевод на {target_lang} успешно завершен.")

        except Exception as e:
            print(f"[ERROR] Ошибка перевода на {target_lang}: {e}. Используются оригинальные данные.")
            # В случае ошибки перевода, используем оригинальные данные (уже установлены по умолчанию выше)
            # translations[target_lang] уже содержит оригиналы, так как мы их не перезаписали

    return translations