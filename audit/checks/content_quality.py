"""
内容质量检查
词数/可读性/关键词密度/标题层级
"""

import re
import math
from collections import Counter
from audit.checks.base import BaseCheck


class ContentQualityCheck(BaseCheck):
    """
    内容质量分析
    - 词数统计
    - 可读性评分 (简化Flesch-Kincaid)
    - 关键词密度
    - 标题层级结构
    - 段落长度
    """

    name = "content_quality"
    description = "Content quality analysis"

    MIN_WORDS = 300
    MAX_KEYWORD_DENSITY = 3.0  # percent

    def run(self, result, response, analyzer):
        text = self._extract_text(response.text)
        words = self._get_words(text)

        self._check_word_count(result, words)
        self._check_readability(result, text, words)
        self._check_keyword_density(result, words)
        self._check_heading_structure(result, analyzer)
        self._check_paragraph_length(result, response.text)

    def _extract_text(self, html: str) -> str:
        """粗提取正文文本"""
        # 移除script/style
        text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.I)
        text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text, flags=re.I)
        # 移除标签
        text = re.sub(r'<[^>]+>', ' ', text)
        # 清理空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _get_words(self, text: str) -> list:
        return [w.lower() for w in re.findall(r'\b[a-zA-Z\u4e00-\u9fff]+\b', text) if len(w) > 1]

    def _check_word_count(self, result, words):
        count = len(words)
        result.details["word_count"] = count

        if count < 100:
            result.add_issue(
                "error", "content",
                f"Very thin content: only {count} words (minimum recommended: {self.MIN_WORDS})",
                deduction=8,
            )
        elif count < self.MIN_WORDS:
            result.add_issue(
                "warning", "content",
                f"Thin content: {count} words (recommended: {self.MIN_WORDS}+)",
                deduction=3,
            )
        else:
            result.add_pass("content", f"Content length: {count} words")

    def _check_readability(self, result, text, words):
        """简化可读性评分"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        num_sentences = max(len(sentences), 1)
        num_words = max(len(words), 1)

        # 平均句长
        avg_sentence_len = num_words / num_sentences
        result.details["avg_sentence_length"] = round(avg_sentence_len, 1)

        if avg_sentence_len > 30:
            result.add_issue(
                "warning", "content",
                f"Long average sentence length ({avg_sentence_len:.0f} words) — aim for 15-20",
                deduction=2,
            )
        else:
            result.add_pass("content", f"Readability: avg sentence length {avg_sentence_len:.0f} words")

    def _check_keyword_density(self, result, words):
        """检查关键词密度（最高频词）"""
        if not words:
            return

        STOP_WORDS = {
            "the", "a", "an", "is", "it", "in", "to", "of", "and", "for",
            "on", "at", "by", "with", "from", "as", "or", "but", "not",
            "this", "that", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "shall",
        }

        filtered = [w for w in words if w not in STOP_WORDS]
        if not filtered:
            return

        counter = Counter(filtered)
        total = len(filtered)
        top_word, top_count = counter.most_common(1)[0]
        density = (top_count / total) * 100

        result.details["top_keyword"] = top_word
        result.details["keyword_density"] = round(density, 1)

        if density > self.MAX_KEYWORD_DENSITY:
            result.add_issue(
                "warning", "content",
                f"High keyword density for '{top_word}': {density:.1f}% (max recommended: {self.MAX_KEYWORD_DENSITY}%)",
                deduction=2,
            )
        else:
            result.add_pass("content", f"Keyword density OK: '{top_word}' at {density:.1f}%")

    def _check_heading_structure(self, result, analyzer):
        """检查标题层级结构"""
        headings = getattr(analyzer, "headings", [])
        if not headings:
            result.add_issue(
                "warning", "content",
                "No headings found — use H1-H6 to structure content",
                deduction=3,
            )
            return

        # 检查H1数量
        h1s = [h for h in headings if h.get("level") == 1]
        if len(h1s) == 0:
            result.add_issue(
                "error", "content",
                "Missing H1 heading",
                deduction=5,
            )
        elif len(h1s) > 1:
            result.add_issue(
                "warning", "content",
                f"Multiple H1 headings ({len(h1s)}) — use only one H1 per page",
                deduction=3,
            )
        else:
            result.add_pass("content", "Single H1 heading present")

        # 检查层级跳跃
        levels = [h.get("level", 0) for h in headings]
        for i in range(1, len(levels)):
            if levels[i] > levels[i - 1] + 1:
                result.add_issue(
                    "warning", "content",
                    f"Heading level skip: H{levels[i-1]} → H{levels[i]} — avoid skipping levels",
                    deduction=1,
                )
                break

    def _check_paragraph_length(self, result, html):
        """检查段落长度"""
        paragraphs = re.findall(r'<p[^>]*>([\s\S]*?)</p>', html, re.I)
        long_paras = 0
        for p in paragraphs:
            text = re.sub(r'<[^>]+>', '', p).strip()
            words = text.split()
            if len(words) > 150:
                long_paras += 1

        if long_paras > 0:
            result.add_issue(
                "info", "content",
                f"{long_paras} paragraph(s) over 150 words — consider breaking up for readability",
                deduction=0,
            )
