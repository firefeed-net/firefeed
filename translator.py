from transformers import MarianMTModel, MarianTokenizer
import torch

# Кэш для хранения загруженных моделей и токенизаторов
_model_cache = {}

def get_translator_model(src_lang, tgt_lang):
    """Получает или загружает модель и токенизатор для указанной языковой пары"""
    cache_key = f"{src_lang}-{tgt_lang}"
    
    if cache_key not in _model_cache:
        model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
        print(f"Загрузка модели {model_name}...")
        
        model = MarianMTModel.from_pretrained(model_name)
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        
        _model_cache[cache_key] = (model, tokenizer)
        print(f"Модель {model_name} загружена и кэширована")
    
    return _model_cache[cache_key]

def translate_text(text, source_lang = 'en', target_lang = 'en'):
    """
    Переводит текст с исходного языка на целевой
    
    Args:
        text (str): Текст для перевода
        source_lang (str): Исходный язык (например, 'en', 'ru', 'de', 'fr')
        target_lang (str): Целевой язык (например, 'en', 'ru', 'de', 'fr')
    
    Returns:
        str: Переведенный текст
    """
    # Очистка входного текста
    cleaned_text = text.strip()
    
    if not cleaned_text:
        return ""
    
    try:
        # Получаем модель и токенизатор для языковой пары
        model, tokenizer = get_translator_model(source_lang, target_lang)
        
        # Токенизация текста
        inputs = tokenizer(cleaned_text, return_tensors="pt", padding=True, truncation=True)
        
        # Генерация перевода
        with torch.no_grad():  # Отключаем вычисление градиентов для экономии памяти
            translated = model.generate(**inputs)
        
        # Декодирование результата
        translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True)
        
        return translated_text[0].strip()  # Возвращаем очищенный перевод
    
    except Exception as e:
        print(f"Ошибка при переводе: {e}")
        return text  # В случае ошибки возвращаем исходный текст
