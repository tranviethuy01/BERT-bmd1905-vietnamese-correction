import logging
import random
import re
from string import ascii_letters
from typing import Dict, List
import unidecode

from config.config import AugmentationConfig, CharacterMaps

class TextAugmenter:
    """Class for text augmentation operations with Vietnamese support."""

    VIETNAMESE_CHAR_MAPPING: Dict[str, List[str]] = {
        'a': ['á', 'à', 'ả', 'ã', 'ạ', 'â', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ', 'ă', 'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ'],
        'd': ['đ'],
        'e': ['é', 'è', 'ẻ', 'ẽ', 'ẹ', 'ê', 'ế', 'ề', 'ể', 'ễ', 'ệ'],
        'i': ['í', 'ì', 'ỉ', 'ĩ', 'ị'],
        'o': ['ó', 'ò', 'ỏ', 'õ', 'ọ', 'ô', 'ố', 'ồ', 'ổ', 'ỗ', 'ộ', 'ơ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ'],
        'u': ['ú', 'ù', 'ủ', 'ũ', 'ụ', 'ư', 'ứ', 'ừ', 'ử', 'ữ', 'ự'],
        'y': ['ý', 'ỳ', 'ỷ', 'ỹ', 'ỵ'],
    }

    COMMON_TYPO_PAIRS = [
        ('tr', 'ch'), ('ch', 'tr'), ('d', 'gi'), ('gi', 'd'), ('r', 'd'),
        ('s', 'x'), ('x', 's'), ('l', 'n'), ('n', 'l'), ('v', 'd'),
        # Bổ sung các cặp phụ âm đầu phổ biến cho augment lỗi giọng vùng miền/ASR:
        ('n', 'l'), ('l', 'n'), ('s', 'x'), ('x', 's'), ('tr', 'ch'), ('ch', 'tr'), 
        ('d', 'gi'), ('gi', 'd'), ('r', 'd'), ('d', 'r'), ('t', 'c'), ('c', 't'), 
        ('v', 'b'), ('b', 'v'),
    ]

    def __init__(self, config: AugmentationConfig):
        self.config = config
        self.char_maps = CharacterMaps()
        self.clean_punctuation = re.compile(r"(?<!\d)[.,;:'?!](?!\d)")
        # Đảo ngược mapping để tra cứu nhanh
        self.REVERSE_MAPPING = {}
        for base, variants in self.VIETNAMESE_CHAR_MAPPING.items():
            for var in variants:
                self.REVERSE_MAPPING[var] = base

    def augment_text(self, text: str) -> str:
        logging.info(f"[augment_text] IN: {text}")
        try:
            text = self.swap_vietnamese_typos(text)
            text = self.swap_n_l(text)  # Thêm hoán đổi n <-> l
            text = self.modify_vietnamese_tones(text)
            # text = self.swap_characters_case(text)
            text = self.delete_vietnamese_character(text)
            text = self.insert_vietnamese_character(text)
            text = self.replace_vietnamese_character(text)
            text = self.lower_case_words(text)
            text = self.remove_punctuation(text)
            text = self.remove_random_accent(text)
            text = self.replace_accent_chars(text)
            logging.info(f"[augment_text] OUT: {text}")
            return text
        except Exception as e:
            logging.error(f"Lỗi khi biến đổi văn bản: {e}")
            return text

    def swap_vietnamese_typos(self, text: str) -> str:
        logging.debug(f"[swap_vietnamese_typos] IN: {text}")
        words = text.split()
        for i in range(len(words)):
            if random.random() < self.config.AUGMENTATION_PROBABILITY:
                for orig, repl in self.COMMON_TYPO_PAIRS:
                    if words[i].startswith(orig):
                        words[i] = repl + words[i][len(orig):]
                        break
        out = ' '.join(words)
        logging.debug(f"[swap_vietnamese_typos] OUT: {out}")
        return out

    def swap_n_l(self, text: str) -> str:
        """
        Hoán đổi phụ âm đầu 'n' <-> 'l' trong các từ với xác suất nhất định.
        """
        logging.debug(f"[swap_n_l] IN: {text}")
        words = text.split()
        for i, word in enumerate(words):
            if word and (word[0].lower() == 'n' or word[0].lower() == 'l'):
                if random.random() < getattr(self.config, "NL_SWAP_PROBABILITY", 0.1):
                    if word[0] == 'n':
                        words[i] = 'l' + word[1:]
                    elif word[0] == 'N':
                        words[i] = 'L' + word[1:]
                    elif word[0] == 'l':
                        words[i] = 'n' + word[1:]
                    elif word[0] == 'L':
                        words[i] = 'N' + word[1:]
        out = ' '.join(words)
        logging.debug(f"[swap_n_l] OUT: {out}")
        return out

    def modify_vietnamese_tones(self, text: str) -> str:
        logging.debug(f"[modify_vietnamese_tones] IN: {text}")
        chars = list(text)
        for i in range(len(chars)):
            if random.random() < self.config.AUGMENTATION_PROBABILITY:
                char = chars[i]
                if char in self.REVERSE_MAPPING:
                    base = self.REVERSE_MAPPING[char]
                    variants = self.VIETNAMESE_CHAR_MAPPING.get(base, [])
                    if variants:
                        chars[i] = random.choice(variants)
        out = ''.join(chars)
        logging.debug(f"[modify_vietnamese_tones] OUT: {out}")
        return out

    def delete_vietnamese_character(self, text: str) -> str:
        logging.debug(f"[delete_vietnamese_character] IN: {text}")
        vowels = [c for c in text if c in self.REVERSE_MAPPING]
        if not vowels or random.random() > self.config.CHAR_DELETE_PERCENTAGE:
            logging.debug(f"[delete_vietnamese_character] OUT (no change): {text}")
            return text
        char_to_delete = random.choice(vowels)
        out = text.replace(char_to_delete, '', 1)
        logging.debug(f"[delete_vietnamese_character] OUT: {out}")
        return out

    def insert_vietnamese_character(self, text: str) -> str:
        logging.debug(f"[insert_vietnamese_character] IN: {text}")
        if random.random() > self.config.AUGMENTATION_PROBABILITY:
            logging.debug(f"[insert_vietnamese_character] OUT (no change): {text}")
            return text
        insert_pos = random.randint(0, len(text))
        base_char = random.choice(list(self.VIETNAMESE_CHAR_MAPPING.keys()))
        variants = self.VIETNAMESE_CHAR_MAPPING.get(base_char, [base_char])
        insert_char = random.choice(variants) if variants else base_char
        out = text[:insert_pos] + insert_char + text[insert_pos:]
        logging.debug(f"[insert_vietnamese_character] OUT: {out}")
        return out

    def replace_vietnamese_character(self, text: str) -> str:
        logging.debug(f"[replace_vietnamese_character] IN: {text}")
        chars = list(text)
        for i in range(len(chars)):
            if random.random() < self.config.AUGMENTATION_PROBABILITY:
                char = chars[i]
                if char in self.REVERSE_MAPPING:
                    base = self.REVERSE_MAPPING[char]
                    variants = self.VIETNAMESE_CHAR_MAPPING.get(base, [])
                    alternatives = [v for v in variants if v != char]
                    if alternatives:
                        chars[i] = random.choice(alternatives)
        out = ''.join(chars)
        logging.debug(f"[replace_vietnamese_character] OUT: {out}")
        return out

    def swap_characters_case(self, text: str) -> str:
        logging.debug(f"[swap_characters_case] IN: {text}")
        out = "".join(
            c.swapcase() if random.random() < self.config.AUGMENTATION_PROBABILITY/2 else c
            for c in text
        )
        logging.debug(f"[swap_characters_case] OUT: {out}")
        return out

    def lower_case_words(self, text: str) -> str:
        logging.debug(f"[lower_case_words] IN: {text}")
        words = text.split()
        out = " ".join(
            word.lower() if word and word[0].isupper() and random.random() < self.config.LOWER_CASE_WORDS_PROBABILITY else word
            for word in words
        )
        logging.debug(f"[lower_case_words] OUT: {out}")
        return out

    def remove_punctuation(self, text: str) -> str:
        logging.debug(f"[remove_punctuation] IN: {text}")
        out = self.clean_punctuation.sub("", text)
        logging.debug(f"[remove_punctuation] OUT: {out}")
        return out

    def delete_word(self, text: str) -> str:
        logging.debug(f"[delete_word] IN: {text}")
        words = text.split()
        if len(words) >= 3 and random.random() < self.config.DELETE_WORD_PROBABILITY:
            words.pop(random.randint(0, len(words) - 1))
            out = " ".join(words)
            logging.debug(f"[delete_word] OUT: {out}")
            return out
        logging.debug(f"[delete_word] OUT (no change): {text}")
        return text

    def replace_accent_chars(self, text: str) -> str:
        logging.debug(f"[replace_accent_chars] IN: {text}")
        words = text.split()
        if random.random() < self.config.REPLACE_ACCENT_CHARS_RATIO and words:
            idx = random.randint(0, len(words) - 1)
            words[idx] = self._change_accent(words[idx])
        out = " ".join(words)
        logging.debug(f"[replace_accent_chars] OUT: {out}")
        return out

    def remove_random_accent(self, text: str) -> str:
        logging.debug(f"[remove_random_accent] IN: {text}")
        words = text.split()
        if random.random() < self.config.REMOVE_RANDOM_ACCENT_RATIO and words:
            idx = random.randint(0, len(words) - 1)
            words[idx] = unidecode.unidecode(words[idx])
        out = " ".join(words)
        logging.debug(f"[remove_random_accent] OUT: {out}")
        return out

    def _change_accent(self, text: str) -> str:
        logging.debug(f"[_change_accent] IN: {text}")
        match_chars = re.findall(self.char_maps.CHARS_REGEX, text)
        if not match_chars:
            logging.debug(f"[_change_accent] OUT (no match): {text}")
            return text
        replace_char = random.choice(match_chars)
        base_char = unidecode.unidecode(replace_char)
        candidates = [c for c in self.char_maps.SAME_CHARS.get(base_char, []) if c != replace_char]
        if candidates:
            insert_char = random.choice(candidates)
            out = text.replace(replace_char, insert_char, 1)
            logging.debug(f"[_change_accent] OUT: {out}")
            return out
        logging.debug(f"[_change_accent] OUT (no change): {text}")
        return text