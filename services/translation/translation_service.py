# services/translation/translation_service.py
import asyncio
import logging
import re
import time
from typing import List, Dict, Any, Optional
from interfaces import ITranslationService, IModelManager, ITranslatorQueue
from services.translation.terminology_dict import TERMINOLOGY_DICT

logger = logging.getLogger(__name__)


class TranslationService(ITranslationService):
    """Service for text translation operations"""

    def __init__(self, model_manager: IModelManager, translator_queue: ITranslatorQueue,
                 max_concurrent_translations: int = 3):
        self.model_manager = model_manager
        self.translator_queue = translator_queue
        self.max_concurrent_translations = max_concurrent_translations
        self.translation_semaphore = asyncio.Semaphore(max_concurrent_translations)

        # Terminology dictionary for preprocessing
        self.terminology_dict = TERMINOLOGY_DICT

        # Translation cache
        self.translation_cache = {}

    async def translate_async(self, texts: List[str], source_lang: str, target_lang: str,
                             context_window: int = 2, beam_size: Optional[int] = None) -> List[str]:
        """Translate texts asynchronously using m2m100 multilingual model"""
        if not texts:
            return []

        async with self.translation_semaphore:
            logger.debug(f"[TRANSLATE] Starting translation: {len(texts)} texts {source_lang} -> {target_lang}")

            try:
                # Preprocess texts with terminology
                processed_texts = [self._preprocess_text_with_terminology(text, target_lang) for text in texts]

                # Check cache for existing translations
                cached_results = []
                texts_to_translate = []
                cache_indices = []

                for i, text in enumerate(processed_texts):
                    cache_key = f"{source_lang}_{target_lang}_{hash(text)}_{context_window}_{beam_size or 'default'}"
                    if cache_key in self.translation_cache:
                        cached_results.append((i, self.translation_cache[cache_key]))
                    else:
                        texts_to_translate.append(text)
                        cache_indices.append(i)

                # Translate uncached texts
                if texts_to_translate:
                    # Get the multilingual m2m100 model (same for all directions)
                    model, tokenizer = await self.model_manager.get_model(source_lang, target_lang)

                    # Prepare texts for translation
                    sentences = self._prepare_sentences_for_batch(texts_to_translate, source_lang)
                    sentence_counts = [len(self._split_into_sentences(text)) for text in texts_to_translate]

                    # Determine optimal batch size
                    batch_size = self._get_optimal_batch_size()

                    # Translate in batches
                    translated_sentences = await self._translate_sentence_batches_m2m100(
                        sentences, model, tokenizer, source_lang, target_lang, batch_size, beam_size
                    )

                    # Assemble back into full texts
                    translated_texts = self._assemble_translated_texts(texts_to_translate, translated_sentences, sentence_counts, target_lang)

                    # Post-process translations
                    translated_texts = [self._postprocess_text(text, target_lang) for text in translated_texts]

                    # Cache results
                    for original_text, translated_text in zip(texts_to_translate, translated_texts):
                        cache_key = f"{source_lang}_{target_lang}_{hash(original_text)}_{context_window}_{beam_size or 'default'}"
                        self.translation_cache[cache_key] = translated_text

                    # Reconstruct full result list
                    result_texts = [''] * len(processed_texts)
                    cache_idx = 0
                    translate_idx = 0

                    for i in range(len(processed_texts)):
                        if i in [idx for idx, _ in cached_results]:
                            result_texts[i] = next(result for orig_idx, result in cached_results if orig_idx == i)
                        else:
                            result_texts[i] = translated_texts[translate_idx]
                            translate_idx += 1
                else:
                    # All results from cache
                    result_texts = [result for _, result in sorted(cached_results, key=lambda x: x[0])]

                logger.debug(f"[TRANSLATE] Translation completed: {len(result_texts)} texts")
                return result_texts

            except Exception as e:
                logger.error(f"[TRANSLATE] Error translating {source_lang} -> {target_lang}: {e}")
                # Return original texts on error
                return texts

    async def prepare_translations(self, title: str, content: str, original_lang: str,
                                  target_langs: List[str]) -> Dict[str, Dict[str, str]]:
        """Prepare translations for title and content to multiple languages with complex validation"""
        start_time = time.time()
        logger.info(f"[TRANSLATE] prepare_translations started for '{original_lang}'")

        translations = {}

        # Always include original language
        translations[original_lang] = {
            "title": title,
            "content": content
        }
        logger.debug(f"[TRANSLATE] Original language '{original_lang}' included")

        # Process each target language
        for target_lang in target_langs:
            if target_lang == original_lang:
                continue

            logger.debug(f"[TRANSLATE] Processing {original_lang} -> {target_lang}")

            try:
                lang_translations = {}

                # Translate title and content
                translated_title, translated_content = await asyncio.gather(
                    self.translate_async([title], original_lang, target_lang),
                    self.translate_async([content], original_lang, target_lang)
                )

                final_title = translated_title[0] if translated_title else title
                final_content = translated_content[0] if translated_content else content

                # Process title
                if final_title and final_title.strip() != title.strip():
                    # Check if translation differs from original
                    if not self._check_translation_language(final_title, target_lang):
                        logger.warning(f"[LANG_CHECK] Title not in '{target_lang}': '{final_title[:50]}...', skipping")
                        continue

                    # Semantic check
                    if not await self._semantic_check(title, final_title, original_lang):
                        logger.warning(f"[SEMANTIC] Title semantic check failed for {target_lang}")
                        # Try fallback with beam_size=1
                        fallback_titles = await self.translate_async([title], original_lang, target_lang, beam_size=1)
                        fallback_title = fallback_titles[0] if fallback_titles else ""
                        if (fallback_title and fallback_title.strip() != title.strip() and
                            self._check_translation_language(fallback_title, target_lang) and
                            await self._semantic_check(title, fallback_title, original_lang)):
                            logger.info(f"[FALLBACK] Title fallback successful for {target_lang}")
                            lang_translations["title"] = fallback_title
                        else:
                            # Try second fallback with beam_size=20 if gibberish detected
                            if self._is_broken_translation(final_title):
                                logger.warning(f"[GIBBERISH] Gibberish detected, trying beam_size=20 for title")
                                fallback_titles_2 = await self.translate_async([title], original_lang, target_lang, beam_size=20)
                                fallback_title_2 = fallback_titles_2[0] if fallback_titles_2 else ""
                                if (fallback_title_2 and fallback_title_2.strip() != title.strip() and
                                    self._check_translation_language(fallback_title_2, target_lang) and
                                    await self._semantic_check(title, fallback_title_2, original_lang) and
                                    not self._is_broken_translation(fallback_title_2)):
                                    logger.info(f"[FALLBACK2] Title second fallback successful for {target_lang}")
                                    lang_translations["title"] = fallback_title_2
                                else:
                                    logger.warning(f"[FALLBACK2] Title second fallback failed, skipping")
                            else:
                                logger.warning(f"[FALLBACK] Title fallback failed, skipping")
                    else:
                        lang_translations["title"] = final_title
                elif final_title == title:
                    # Original language case
                    lang_translations["title"] = final_title

                # Process content (same logic as title)
                if final_content and final_content.strip() != content.strip():
                    if not self._check_translation_language(final_content, target_lang):
                        logger.warning(f"[LANG_CHECK] Content not in '{target_lang}': '{final_content[:50]}...', skipping")
                        continue

                    if not await self._semantic_check(content, final_content, original_lang):
                        logger.warning(f"[SEMANTIC] Content semantic check failed for {target_lang}")
                        # Try fallback with beam_size=1
                        fallback_contents = await self.translate_async([content], original_lang, target_lang, beam_size=1)
                        fallback_content = fallback_contents[0] if fallback_contents else ""
                        if (fallback_content and fallback_content.strip() != content.strip() and
                            self._check_translation_language(fallback_content, target_lang) and
                            await self._semantic_check(content, fallback_content, original_lang)):
                            logger.info(f"[FALLBACK] Content fallback successful for {target_lang}")
                            lang_translations["content"] = fallback_content
                        else:
                            # Try second fallback with beam_size=20 if gibberish detected
                            if self._is_broken_translation(final_content):
                                logger.warning(f"[GIBBERISH] Gibberish detected, trying beam_size=20 for content")
                                fallback_contents_2 = await self.translate_async([content], original_lang, target_lang, beam_size=20)
                                fallback_content_2 = fallback_contents_2[0] if fallback_contents_2 else ""
                                if (fallback_content_2 and fallback_content_2.strip() != content.strip() and
                                    self._check_translation_language(fallback_content_2, target_lang) and
                                    await self._semantic_check(content, fallback_content_2, original_lang) and
                                    not self._is_broken_translation(fallback_content_2)):
                                    logger.info(f"[FALLBACK2] Content second fallback successful for {target_lang}")
                                    lang_translations["content"] = fallback_content_2
                                else:
                                    logger.warning(f"[FALLBACK2] Content second fallback failed, skipping")
                            else:
                                logger.warning(f"[FALLBACK] Content fallback failed, skipping")
                    else:
                        lang_translations["content"] = final_content
                elif final_content == content:
                    # Original language case
                    lang_translations["content"] = final_content

                # Only add language if both title and content are available
                if "title" in lang_translations and "content" in lang_translations:
                    translations[target_lang] = lang_translations
                    logger.info(f"[TRANSLATE] Translation for '{target_lang}' successfully added")
                else:
                    logger.warning(f"[TRANSLATE] Translation for '{target_lang}' incomplete, language skipped")

            except Exception as e:
                logger.error(f"[TRANSLATE] Error processing {target_lang}: {e}")
                continue

        # Remove duplicate translations between languages
        seen_titles = set()
        to_remove = []
        for lang, data in translations.items():
            title = data.get("title", "")
            if title in seen_titles:
                logger.warning(f"[TRANSLATE] Removing duplicate translation for language '{lang}' (same title)")
                to_remove.append(lang)
            else:
                seen_titles.add(title)
        for lang in to_remove:
            del translations[lang]

        total_duration = time.time() - start_time
        logger.info(f"[TRANSLATE] prepare_translations completed in {total_duration:.2f}s. Total translations: {len(translations)}")

        # Unload unused models after batch translation processing
        unloaded = await self.model_manager.unload_unused_models(max_age_seconds=1800)
        logger.info(f"[TRANSLATE] Unloaded {unloaded} unused models after prepare_translations")

        return translations

    def _preprocess_text_with_terminology(self, text: str, target_lang: str) -> str:
        """Preprocess text by replacing terminology before translation"""
        if target_lang not in ["ru", "de", "fr", "en"]:
            return text  # If language not supported, return as is

        for eng_term, translations in self.terminology_dict.items():
            if target_lang in translations:
                translated_term = translations[target_lang]
                if translated_term != eng_term:  # Replace only if translation differs
                    text = re.sub(r"\b" + re.escape(eng_term) + r"\b", translated_term, text, flags=re.IGNORECASE)
        return text

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - can be improved with NLP libraries
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _prepare_sentences_for_batch(self, texts: List[str], source_lang: str) -> List[str]:
        """Prepare sentences for batch translation"""
        all_sentences = []
        for text in texts:
            sentences = self._split_into_sentences(text)
            all_sentences.extend(sentences)
        return all_sentences

    async def _translate_sentence_batches_m2m100(self, sentences: List[str], model, tokenizer,
                                                 source_lang: str, target_lang: str, batch_size: int,
                                                 beam_size: Optional[int]) -> List[str]:
        """Translate sentences in batches using m2m100 or MarianMT model"""
        translated_sentences = []

        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]

            try:
                # Handle different tokenizer types
                if hasattr(tokenizer, 'get_lang_id'):
                    # M2M100 tokenizer
                    tokenizer.src_lang = source_lang
                    inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)

                    # Generate translations with target language
                    outputs = model.generate(
                        **inputs,
                        forced_bos_token_id=tokenizer.get_lang_id(target_lang),
                        max_length=512,
                        num_beams=beam_size or 4,
                        early_stopping=True
                    )
                else:
                    # MarianMT tokenizer (fallback)
                    inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)

                    # Generate translations (MarianMT doesn't need forced_bos_token_id)
                    outputs = model.generate(
                        **inputs,
                        max_length=512,
                        num_beams=beam_size or 4,
                        early_stopping=True
                    )

                # Decode translations
                batch_translations = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                translated_sentences.extend(batch_translations)

            except Exception as e:
                logger.error(f"[TRANSLATE] Error in batch translation: {e}")
                # Add original sentences on error
                translated_sentences.extend(batch)

        return translated_sentences

    async def _translate_sentence_batches(self, sentences: List[str], model, tokenizer,
                                         source_lang: str, target_lang: str, batch_size: int,
                                         beam_size: Optional[int]) -> List[str]:
        """Translate sentences in batches (fallback for other models)"""
        translated_sentences = []

        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]

            try:
                # Tokenize batch
                inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)

                # Generate translations
                outputs = model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=beam_size or 4,
                    early_stopping=True
                )

                # Decode translations
                batch_translations = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                translated_sentences.extend(batch_translations)

            except Exception as e:
                logger.error(f"[TRANSLATE] Error in batch translation: {e}")
                # Add original sentences on error
                translated_sentences.extend(batch)

        return translated_sentences

    def _assemble_translated_texts(self, original_texts: List[str], translated_sentences: List[str],
                                 sentence_counts: List[int], target_lang: str) -> List[str]:
        """Assemble translated sentences back into full texts"""
        translated_texts = []
        sentence_idx = 0

        for original_text, count in zip(original_texts, sentence_counts):
            if sentence_idx + count <= len(translated_sentences):
                translated_sentences_for_text = translated_sentences[sentence_idx:sentence_idx + count]
                translated_text = '. '.join(translated_sentences_for_text)
                if original_text.endswith('!'):
                    translated_text = translated_text.replace('.', '!')
                elif original_text.endswith('?'):
                    translated_text = translated_text.replace('.', '?')
                translated_texts.append(translated_text)
            else:
                # Fallback to original if something went wrong
                translated_texts.append(original_text)

            sentence_idx += count

        return translated_texts

    def _postprocess_text(self, text: str, target_lang: str = "ru") -> str:
        """Post-process translated text with comprehensive cleaning"""
        if not text:
            return text

        # Clean extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove consecutive repeated words (improved version)
        words = text.split()
        if words:
            deduped_words = [words[0]]
            for word in words[1:]:
                # Check for exact match or partial match (for words like "five-year" -> "five")
                if (word.lower() != deduped_words[-1].lower() and
                    not word.lower().startswith(deduped_words[-1].lower()[:3])):
                    deduped_words.append(word)
            text = " ".join(deduped_words)

        # Remove consecutive identical characters (more than 3)
        text = re.sub(r"(.)\1{3,}", r"\1\1\1", text)

        # Fix capitalization at sentence starts
        sentences = re.split(r"([.!?]+)", text)
        processed = []
        for i, part in enumerate(sentences):
            if part.strip() and part[0].isalpha():
                processed.append(part[0].upper() + part[1:])
            else:
                processed.append(part)
        text = "".join(processed)

        # Remove duplicate sentences
        lines = text.split(". ")
        unique_lines = []
        seen = set()
        for line in lines:
            line_clean = re.sub(r"\W+", "", line.lower())
            if line_clean not in seen and len(line_clean) > 5:  # Skip very short lines
                seen.add(line_clean)
                unique_lines.append(line)
        text = ". ".join(unique_lines)

        # Replace terminology (case-insensitive) - for cases where translation failed
        for eng, translations in self.terminology_dict.items():
            if target_lang in translations:
                translated_term = translations[target_lang]
                text = re.sub(r"\b" + re.escape(eng) + r"\b", translated_term, text, flags=re.IGNORECASE)

        # Remove trailing punctuation
        text = text.strip(" .,;")

        # Final validation: if text is too short or has too few letters, return empty
        if len(text) < 10 or len(re.findall(r"[a-zA-Zа-яА-Я]", text)) < len(text) * 0.5:
            return ""

        return text

    def _check_translation_language(self, translated_text: str, target_lang: str) -> bool:
        """Check if translation contains sufficient characters of target language (at least 60%)"""
        if not translated_text or not target_lang:
            return False

        # Language character sets (simplified)
        lang_chars = {
            "ru": "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
            "en": "abcdefghijklmnopqrstuvwxyz",
            "de": "abcdefghijklmnopqrstuvwxyzäöüß",
            "fr": "abcdefghijklmnopqrstuvwxyzàâäéèêëïîôöùûüÿç"
        }

        target_chars = lang_chars.get(target_lang.lower(), "")
        if not target_chars:
            return True  # Unknown language, assume valid

        translated_lower = translated_text.lower()

        # Count only alphabetic characters (ignore numbers, punctuation, spaces)
        alphabetic_chars = re.findall(r'[a-zа-яёäöüßàâäéèêëïîôöùûüÿç]', translated_lower)

        if not alphabetic_chars:
            return False

        # Count characters of target language
        target_count = sum(1 for char in alphabetic_chars if char in target_chars)
        target_ratio = target_count / len(alphabetic_chars)

        # Require at least 60% of characters to be in target language
        # This allows for company names, quotes, and proper nouns in other languages
        return target_ratio >= 0.6

    def _is_broken_translation(self, text: str, max_repeats: int = 15) -> bool:
        """Check if text contains suspicious repeats or gibberish"""
        if len(text) < 5:
            return False

        words = text.split()

        # Check for 15+ consecutive identical words
        for i in range(len(words) - max_repeats + 1):
            chunk = words[i : i + max_repeats]
            if len(set(chunk)) == 1:
                return True

        # Check for too many repeating characters
        if re.search(r"(.)\1{10,}", text):
            return True

        # Check for no spaces in long text
        if len(text) > 50 and " " not in text:
            return True

        # Check for too few unique words
        unique_words = set(words)
        if len(unique_words) < len(words) * 0.3 and len(words) > 10:
            return True

        # Check for too many words starting with same chars
        word_starts = [word[:3].lower() for word in words if len(word) >= 3]
        if word_starts:
            most_common_start = max(set(word_starts), key=word_starts.count)
            if word_starts.count(most_common_start) > len(word_starts) * 0.6:
                return True

        # Check for too many non-alphanumeric characters
        alphanumeric_ratio = len(re.findall(r"[a-zA-Zа-яА-Я0-9]", text)) / len(text) if text else 0
        if alphanumeric_ratio < 0.7:
            return True

        # Check for too many short words
        short_words_count = sum(1 for word in words if len(word) < 3)
        if len(words) > 5 and short_words_count > len(words) * 0.8:
            return True

        # Check for repeating patterns
        for i in range(len(words) - 1):
            if words[i] in words[i + 1] and len(words[i]) > 3:
                return True

        return False

    async def _semantic_check(self, original_text: str, translated_text: str, lang_code: str = "en") -> bool:
        """Check semantic similarity between original and translated text"""
        if not original_text or not translated_text:
            return False

        # If translation is identical to original, it's bad
        if original_text.strip() == translated_text.strip():
            logger.warning("[SEMANTIC] Translation identical to original")
            return False

        # Check for gibberish
        if self._is_broken_translation(translated_text):
            logger.warning("[SEMANTIC] Translation contains gibberish")
            return False

        try:
            # Use embeddings processor for semantic check
            from services.text_analysis.embeddings_processor import FireFeedEmbeddingsProcessor

            processor = FireFeedEmbeddingsProcessor()
            original_embedding, translated_embedding = await asyncio.gather(
                processor.generate_embedding(original_text, lang_code),
                processor.generate_embedding(translated_text, lang_code)
            )
            similarity = await processor.calculate_similarity(original_embedding, translated_embedding)

            # Dynamic threshold based on text length
            text_length = len(original_text)
            if text_length < 50:
                threshold = 0.6  # Shorter texts need higher similarity
            elif text_length < 200:
                threshold = 0.5
            else:
                threshold = 0.4  # Longer texts can have more variation

            return similarity >= threshold

        except Exception as e:
            logger.warning(f"[TRANSLATE] Error in semantic check: {e}")
            return True  # Allow translation if check fails

    def _get_optimal_batch_size(self) -> int:
        """Determine optimal batch size based on available memory"""
        # Simple heuristic - can be improved with actual memory monitoring
        try:
            import psutil
            available_memory = psutil.virtual_memory().available / (1024 * 1024 * 1024)  # GB

            if available_memory > 8:
                return 16
            elif available_memory > 4:
                return 8
            elif available_memory > 2:
                return 4
            else:
                return 2
        except ImportError:
            # Fallback if psutil not available
            return 4

    def clear_translation_cache(self):
        """Clear translation cache"""
        cache_size = len(self.translation_cache)
        self.translation_cache.clear()
        logger.info(f"[TRANSLATE] Cleared {cache_size} entries from translation cache")