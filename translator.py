from transformers import MarianMTModel, MarianTokenizer
from firefeed_utils import clean_html
from functools import lru_cache
import asyncio
import torch
import nltk
import os
import time
import re
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
    start_time = time.time()
    print(f"[{start_time:.3f}] Начало перевода: {source_lang} -> {target_lang}, текст длиной {len(text)} символов")
    
    if source_lang == target_lang:
        result = clean_html(text)
        end_time = time.time()
        print(f"[{end_time:.3f}] Языки совпадают, возврат без перевода. Время выполнения: {end_time - start_time:.3f} сек")
        return result

    cache_key = f"{source_lang}_{target_lang}_{hash(text)}"
    if cache_key in _translation_cache:
        cached_result = _translation_cache[cache_key]
        end_time = time.time()
        print(f"[{end_time:.3f}] Результат найден в кэше. Время выполнения: {end_time - start_time:.3f} сек")
        return cached_result

    # Проверяем, нужен ли каскадный перевод
    cascade_key = (source_lang, target_lang)
    if cascade_key in CASCADE_TRANSLATIONS:
        print(f"[{time.time():.3f}] Используется каскадный перевод для {source_lang} -> {target_lang}")
        # Используем каскадный перевод через английский
        src_lang, intermediate_lang, tgt_lang = CASCADE_TRANSLATIONS[cascade_key]
        
        # Переводим на промежуточный язык (английский)
        print(f"[{time.time():.3f}] Этап 1: Перевод {src_lang} -> {intermediate_lang}")
        intermediate_start = time.time()
        intermediate_text = translate_text(text, src_lang, intermediate_lang, context_window)
        intermediate_time = time.time() - intermediate_start
        print(f"[{time.time():.3f}] Этап 1 завершен за {intermediate_time:.3f} сек")
        
        # Переводим с промежуточного на целевой язык
        print(f"[{time.time():.3f}] Этап 2: Перевод {intermediate_lang} -> {tgt_lang}")
        final_start = time.time()
        result = translate_text(intermediate_text, intermediate_lang, tgt_lang, context_window)
        final_time = time.time() - final_start
        print(f"[{time.time():.3f}] Этап 2 завершен за {final_time:.3f} сек")
    else:
        print(f"[{time.time():.3f}] Прямой перевод {source_lang} -> {target_lang}")
        print(f"[{time.time():.3f}] Токенизация текста...")
        sentences = nltk.sent_tokenize(text)
        print(f"[{time.time():.3f}] Получено {len(sentences)} предложений")
        
        print(f"[{time.time():.3f}] Начало перевода с контекстом (окно: {context_window})")
        translate_start = time.time()
        translated = " ".join(translate_with_context(sentences, source_lang, target_lang, context_window))
        translate_time = time.time() - translate_start
        print(f"[{time.time():.3f}] Перевод завершен за {translate_time:.3f} сек")
        
        result = clean_html(translated)

    _translation_cache[cache_key] = result
    end_time = time.time()
    total_time = end_time - start_time
    print(f"[{end_time:.3f}] Перевод завершен. Общее время выполнения: {total_time:.3f} сек")
    return result

def is_broken_translation(text: str, max_repeats: int = 5) -> bool:
    """
    Проверяет, содержит ли текст подозрительное количество повторяющихся символов подряд.
    Например: "......." или "........."
    """
    if not text:
        return True
    # Проверяем, есть ли последовательности из более чем max_repeats одинаковых символов
    return bool(re.search(r'(.)\1{' + str(max_repeats) + ',}', text))

async def prepare_translations(title: str, description: str, category: str, original_lang: str) -> dict:
    """
    Подготавливает переводы заголовка, описания и категории на все целевые языки.
    Не включает переводы, если:
    - Перевод совпадает с оригиналом
    - Перевод содержит битые символы (например, куча точек)
    """
    translations = {}
    target_languages = list(CHANNEL_IDS.keys())  # ['ru', 'en', 'de', 'fr']

    # Очищаем оригинальный текст один раз
    clean_title = clean_html(title)
    clean_description = clean_html(description)

    loop = asyncio.get_event_loop()
    translation_tasks = []

    for target_lang in target_languages:
        if original_lang == target_lang:
            translations[target_lang] = {
                'title': clean_title,
                'description': clean_description,
                'category': category
            }
            print(f"[LOG] Перевод с {original_lang} на {target_lang} не требуется. Используются оригинальные данные.")
            continue

        print(f"[LOG] Перевод с {original_lang} на {target_lang} запущен.")

        title_task = loop.run_in_executor(None, translate_text, clean_title, original_lang, target_lang)
        desc_task = loop.run_in_executor(None, translate_text, clean_description, original_lang, target_lang)
        cat_task = loop.run_in_executor(None, translate_text, category, 'en', target_lang)

        translation_tasks.append((target_lang, title_task, desc_task, cat_task))

    for target_lang, title_task, desc_task, cat_task in translation_tasks:
        try:
            trans_title = await title_task
            trans_description = await desc_task
            trans_category = await cat_task

            # Проверка 1: Совпадение с оригиналом
            if (
                trans_title.strip().lower() == clean_title.strip().lower() and
                trans_description.strip().lower() == clean_description.strip().lower()
            ):
                print(f"[WARN] Перевод на {target_lang} совпадает с оригиналом. Пропуск публикации.")
                continue

            # Проверка 2: Битый перевод (повторяющиеся символы)
            if (
                is_broken_translation(trans_title) or
                is_broken_translation(trans_description)
            ):
                print(f"[WARN] Перевод на {target_lang} содержит битые символы. Пропуск публикации.")
                continue

            translations[target_lang] = {
                'title': trans_title,
                'description': trans_description,
                'category': trans_category
            }
            print(f"[LOG] Перевод на {target_lang} успешно завершен.")

        except Exception as e:
            print(f"[ERROR] Ошибка перевода на {target_lang}: {e}. Пропуск публикации.")

    return translations