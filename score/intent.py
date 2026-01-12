import re
from typing import Dict, List


class IntentScorer:
    def __init__(self, scoring_config: dict, keywords_config: dict):
        self.scoring = scoring_config
        self.keywords = keywords_config

        self.title_weight = scoring_config.get("title", 1)
        self.content_weight = scoring_config.get("content", 1)

        self.thresholds = scoring_config.get("thresholds", {})
        self.structural = scoring_config.get("structural_bonuses", {})

        self.positive = keywords_config.get("positive", {})
        self.negative = keywords_config.get("negative", {})

    # -----------------------------
    # Public APIs
    # -----------------------------
    def score_posts(self, posts: List[Dict]) -> List[Dict]:
        for post in posts:
            score, reasons = self.score_single_post(post)
            post["intent_score"] = score
            post["intent_reasons"] = reasons
        return posts

    def score_single_post(self, post: Dict):
        title = post.get("title", "").lower()
        content = post.get("content_text", "").lower()

        score = 0
        reasons = []

        # keyword scoring
        s, r = self._score_text(title, content)
        score += s
        reasons.extend(r)

        # structural bonuses
        s, r = self._structural_score(post, content)
        score += s
        reasons.extend(r)

        return score, reasons

    # -----------------------------
    # Keyword scoring
    # -----------------------------
    def _score_text(self, title: str, content: str):
        score = 0
        reasons = []

        # positive keywords
        for group, keywords in self.positive.items():
            for phrase, weight in keywords.items():
                p = phrase.lower()

                if p in title:
                    s = weight * self.title_weight
                    score += s
                    reasons.append(f"+{s} title:{p}")

                elif p in content:
                    s = weight * self.content_weight
                    score += s
                    reasons.append(f"+{s} content:{p}")

        # negative keywords (penalties)
        for phrase, weight in self.negative.items():
            p = phrase.lower()

            if p in title or p in content:
                score += weight
                reasons.append(f"{weight} penalty:{p}")

        return score, reasons

    # -----------------------------
    # Structural bonuses
    # -----------------------------
    def _structural_score(self, post: Dict, content: str):
        score = 0
        reasons = []

        length = len(content)

        if length > 1000:
            s = self.structural.get("post_length_gt_1000", 0)
            score += s
            if s:
                reasons.append(f"+{s} long_post_1000")

        elif length > 500:
            s = self.structural.get("post_length_gt_500", 0)
            score += s
            if s:
                reasons.append(f"+{s} long_post_500")

        if self._contains_code(content):
            s = self.structural.get("contains_code_snippet", 0)
            score += s
            if s:
                reasons.append(f"+{s} code_snippet")

        if self._contains_equity_stats(content):
            s = self.structural.get("contains_equity_curve_or_stats", 0)
            score += s
            if s:
                reasons.append(f"+{s} equity_stats")

        replies = post.get("replies", 0)
        if replies >= 10:
            s = self.structural.get("comment_count_gt_10", 0)
            score += s
            if s:
                reasons.append(f"+{s} replies_gt_10")

        return score, reasons

    # -----------------------------
    # Helpers
    # -----------------------------
    def _contains_code(self, text: str) -> bool:
        return bool(re.search(r"(<code>|```|def |class |;)", text))

    def _contains_equity_stats(self, text: str) -> bool:
        patterns = [
            r"equity curve",
            r"drawdown",
            r"sharpe",
            r"profit factor",
            r"expectancy",
            r"cagr",
            r"max drawdown",
            r"\b\d+%\b"
        ]
        return any(re.search(p, text) for p in patterns)
