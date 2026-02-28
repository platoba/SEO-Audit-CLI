"""Keyword density analyzer - word frequency, TF analysis, over-optimization detection."""

import re
from collections import Counter
from typing import Dict, List, Tuple, Optional
from .base import BaseCheck


# Common stop words (English + Chinese markers)
STOP_WORDS_EN = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "this", "that",
    "these", "those", "it", "its", "not", "no", "nor", "as", "if", "then",
    "than", "when", "while", "so", "about", "up", "out", "just", "also",
    "how", "what", "which", "who", "whom", "where", "very", "more", "most",
    "all", "each", "every", "both", "few", "many", "some", "any", "such",
    "only", "own", "same", "other", "new", "old", "into", "over", "after",
})


class KeywordAnalyzer:
    """Analyze text for keyword density and distribution."""

    def __init__(self, text: str, title: str = "", meta_desc: str = ""):
        self.raw_text = text
        self.title = title
        self.meta_desc = meta_desc
        self.words: List[str] = []
        self.word_freq: Counter = Counter()
        self.bigrams: Counter = Counter()
        self.trigrams: Counter = Counter()
        self._analyze()

    def _clean_text(self, text: str) -> str:
        """Remove HTML tags and normalize whitespace."""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words, filtering stop words."""
        words = text.split()
        return [w for w in words if w not in STOP_WORDS_EN and len(w) > 1]

    def _analyze(self):
        clean = self._clean_text(self.raw_text)
        self.words = self._tokenize(clean)
        self.word_freq = Counter(self.words)

        # N-grams
        for i in range(len(self.words) - 1):
            bigram = f"{self.words[i]} {self.words[i+1]}"
            self.bigrams[bigram] += 1

        for i in range(len(self.words) - 2):
            trigram = f"{self.words[i]} {self.words[i+1]} {self.words[i+2]}"
            self.trigrams[trigram] += 1

    @property
    def total_words(self) -> int:
        return len(self.words)

    @property
    def unique_words(self) -> int:
        return len(self.word_freq)

    @property
    def lexical_diversity(self) -> float:
        """Ratio of unique words to total words (0-1)."""
        if self.total_words == 0:
            return 0
        return round(self.unique_words / self.total_words, 3)

    def top_keywords(self, n: int = 20) -> List[Tuple[str, int, float]]:
        """Top N keywords with count and density percentage."""
        total = self.total_words or 1
        return [
            (word, count, round(count / total * 100, 2))
            for word, count in self.word_freq.most_common(n)
        ]

    def top_bigrams(self, n: int = 10) -> List[Tuple[str, int, float]]:
        total = max(self.total_words - 1, 1)
        return [
            (bg, count, round(count / total * 100, 2))
            for bg, count in self.bigrams.most_common(n)
        ]

    def top_trigrams(self, n: int = 10) -> List[Tuple[str, int, float]]:
        total = max(self.total_words - 2, 1)
        return [
            (tg, count, round(count / total * 100, 2))
            for tg, count in self.trigrams.most_common(n)
        ]

    def keyword_in_title(self, keyword: str) -> bool:
        return keyword.lower() in self.title.lower()

    def keyword_in_meta(self, keyword: str) -> bool:
        return keyword.lower() in self.meta_desc.lower()

    def density_of(self, keyword: str) -> float:
        """Density percentage of a specific keyword."""
        total = self.total_words or 1
        count = self.word_freq.get(keyword.lower(), 0)
        return round(count / total * 100, 2)


class KeywordCheck(BaseCheck):
    """Keyword density and content quality analysis."""
    name = "keywords"
    description = "Keyword density, n-gram analysis, over-optimization detection"

    # Thresholds
    MIN_WORDS = 300
    MAX_KEYWORD_DENSITY = 3.0  # % — above this is keyword stuffing
    IDEAL_DENSITY_RANGE = (0.5, 2.5)  # %
    MIN_LEXICAL_DIVERSITY = 0.3

    def run(self, result, response, analyzer):
        # Extract body text (strip tags)
        body_text = re.sub(r"<script[^>]*>.*?</script>", "", analyzer.html_raw, flags=re.DOTALL | re.IGNORECASE)
        body_text = re.sub(r"<style[^>]*>.*?</style>", "", body_text, flags=re.DOTALL | re.IGNORECASE)

        kw_analyzer = KeywordAnalyzer(
            body_text,
            title=analyzer.title,
            meta_desc=analyzer.meta.get("description", ""),
        )

        details = {
            "total_words": kw_analyzer.total_words,
            "unique_words": kw_analyzer.unique_words,
            "lexical_diversity": kw_analyzer.lexical_diversity,
            "top_keywords": [
                {"word": w, "count": c, "density": d}
                for w, c, d in kw_analyzer.top_keywords(15)
            ],
            "top_bigrams": [
                {"phrase": p, "count": c, "density": d}
                for p, c, d in kw_analyzer.top_bigrams(10)
            ],
            "top_trigrams": [
                {"phrase": p, "count": c, "density": d}
                for p, c, d in kw_analyzer.top_trigrams(5)
            ],
        }
        result.details["keywords"] = details

        # Word count check
        if kw_analyzer.total_words < self.MIN_WORDS:
            result.add_issue("warning", "keywords",
                             f"页面内容过少 ({kw_analyzer.total_words}词)，建议至少{self.MIN_WORDS}词", 3)
        elif kw_analyzer.total_words >= 1000:
            result.add_pass("keywords", f"页面内容丰富 ({kw_analyzer.total_words}词)")
        else:
            result.add_pass("keywords", f"页面内容量OK ({kw_analyzer.total_words}词)")

        # Lexical diversity
        if kw_analyzer.lexical_diversity < self.MIN_LEXICAL_DIVERSITY:
            result.add_issue("warning", "keywords",
                             f"词汇多样性低 ({kw_analyzer.lexical_diversity})，内容可能重复", 2)

        # Over-optimization (keyword stuffing)
        top = kw_analyzer.top_keywords(5)
        stuffed = [(w, d) for w, c, d in top if d > self.MAX_KEYWORD_DENSITY]
        if stuffed:
            words_str = ", ".join(f'"{w}" ({d}%)' for w, d in stuffed)
            result.add_issue("warning", "keywords",
                             f"关键词密度过高(可能过度优化): {words_str}", 3)
        else:
            result.add_pass("keywords", "关键词密度正常，无过度优化")

        # Title keyword alignment
        if kw_analyzer.total_words > 0 and kw_analyzer.title:
            top_kw = top[0][0] if top else ""
            if top_kw and kw_analyzer.keyword_in_title(top_kw):
                result.add_pass("keywords", f"主关键词 \"{top_kw}\" 出现在标题中")
            elif top_kw:
                result.add_issue("info", "keywords",
                                 f"主关键词 \"{top_kw}\" 未出现在标题中，考虑优化")

        # Meta description keyword alignment
        if kw_analyzer.total_words > 0 and kw_analyzer.meta_desc:
            top_kw = top[0][0] if top else ""
            if top_kw and kw_analyzer.keyword_in_meta(top_kw):
                result.add_pass("keywords", f"主关键词 \"{top_kw}\" 出现在meta描述中")
