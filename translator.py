from transformers import MarianMTModel, MarianTokenizer
from functools import lru_cache
from firefeed_utils import clean_html
import asyncio
import torch
import nltk
import os

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

_model_cache = {}
_tokenizer_cache = {}
_translation_cache = {}

# Языковые пары, требующие каскадного перевода через английский
CASCADE_TRANSLATIONS = {
    ('ru', 'de'): ('ru', 'en', 'de')
}

def get_translator_model(src_lang, tgt_lang):
    cache_key = f"{src_lang}-{tgt_lang}"
    if cache_key not in _model_cache:
        try:
            model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
            model = MarianMTModel.from_pretrained(model_name)
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            _model_cache[cache_key] = model
            _tokenizer_cache[cache_key] = tokenizer
        except Exception as e:
            print(f"Модель {model_name} не найдена: {e}")
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
        with torch.no_grad():
            outputs = model.generate(**inputs)
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Удаляем контекст из результата (если нужно)
        if context:
            # Это упрощённый подход - в реальности может потребоваться более сложная постобработка
            translated_text = translated_text.replace(translate_text(context, source_lang, target_lang), "").strip()
        
        translated.append(translated_text)
    
    return translated

@lru_cache(maxsize=1000)
def cached_translate_text(text, source_lang, target_lang):
    return translate_text(text, source_lang, target_lang)

def translate_text(text, source_lang='en', target_lang='ru', context_window=2):
    if source_lang == target_lang:
        return text

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