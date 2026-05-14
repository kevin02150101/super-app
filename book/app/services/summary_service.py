"""書籍分類與查詢總結服務。

- `classify(book)`:依書名/作者/出版社/查詢關鍵字,以關鍵字白名單規則歸類。
- `summarize(keyword, books)`:產生這一次查詢的簡單摘要(統計數字 + 一段中文敘述)。
- `summarize_text(text)`:對單本書的「內容簡介」做精簡摘要(取首數句)。

> 規則式分類為主、可離線運作,不依賴外部 LLM。
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

# (分類, 比對用關鍵字串) — 由上而下優先比對
CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Programming", (
        "python", "java", "javascript", "typescript", "kotlin", "swift",
        "c++", "c#", "golang", " go ", "rust", "php", "ruby",
        "react", "vue", "angular", "node", "django", "flask", "spring",
        "演算法", "資料結構", "程式", "程式設計", "軟體", "工程師", "coding",
        "linux", "docker", "kubernetes", "git", "devops", "雲端", "aws", "azure",
        "資料庫", "sql", "mysql", "postgres",
    )),
    ("AI / Data Science", (
        "ai", "人工智慧", "機器學習", "machine learning", "deep learning",
        "深度學習", "神經網路", "neural", "資料科學", "data science",
        "大數據", "big data", "資料分析", "統計學", "資料視覺化",
        "chatgpt", "llm", "生成式", "gpt", "transformer",
    )),
    ("Business / Finance", (
        "投資", "理財", "股票", "基金", "etf", "財務", "財報", "經濟",
        "管理", "行銷", "marketing", "業務", "創業", "商業", "策略",
        "領導", "leadership", "致富", "金錢", "現金流", "房地產",
    )),
    ("Psychology / Self-help", (
        "心理", "心靈", "勵志", "正向", "自我", "成長", "習慣",
        "情緒", "焦慮", "療癒", "人生", "幸福", "禪", "冥想",
    )),
    ("Language Learning", (
        "英文", "英語", "english", "toeic", "toefl", "ielts",
        "日文", "日語", "韓文", "韓語", "法文", "德文", "西班牙文",
        "文法", "單字", "會話", "口說", "聽力", "翻譯",
    )),
    ("Literature / Fiction", (
        "小說", "長篇", "短篇", "散文", "詩", "詩集", "novel",
        "推理", "懸疑", "驚悚", "愛情", "言情", "奇幻", "fantasy",
        "科幻", "歷史小說", "古典文學",
    )),
    ("Comics / Light Novels", (
        "漫畫", "comic", "manga", "輕小說", "插畫", "畫集",
    )),
    ("Children / Family", (
        "童書", "繪本", "兒童", "親子", "幼兒", "教養", "育兒",
    )),
    ("Art / Design", (
        "設計", "design", "美學", "藝術", "繪畫", "攝影", "photo",
        "建築", "字體", "排版", "ui", "ux",
    )),
    ("Lifestyle / Food", (
        "料理", "食譜", "烘焙", "甜點", "咖啡", "茶", "美食",
        "旅遊", "旅行", "travel", "健身", "瑜珈", "瘦身", "減重",
        "健康", "養生", "醫學", "中醫",
    )),
    ("Humanities / History", (
        "歷史", "history", "哲學", "宗教", "佛教", "基督",
        "文化", "社會", "政治", "考古",
    )),
    ("Popular Science", (
        "科學", "物理", "化學", "生物", "天文", "宇宙", "數學",
        "科普", "演化", "腦科學",
    )),
]

DEFAULT_CATEGORY = "Other"


@dataclass
class BookLike:
    title: str | None = None
    authors: str | None = None
    publisher: str | None = None


class SummaryService:
    # ---- 分類 ----
    def classify(self, book: BookLike, fallback_keyword: str = "") -> str:
        haystack = " ".join(
            (book.title or "", book.authors or "", book.publisher or "", fallback_keyword)
        ).lower()
        if not haystack.strip():
            return DEFAULT_CATEGORY
        for category, keywords in CATEGORY_RULES:
            for kw in keywords:
                if kw.lower() in haystack:
                    return category
        return DEFAULT_CATEGORY

    def classify_many(
        self, books: Iterable[BookLike], fallback_keyword: str = ""
    ) -> list[str]:
        return [self.classify(b, fallback_keyword) for b in books]

    # ---- 單書內容摘要 ----
    @staticmethod
    def summarize_text(
        text: str | None, max_sentences: int = 3, max_chars: int = 220
    ) -> str | None:
        """從書籍簡介萃取首數句作為短摘要。

        - 移除多餘空白與導覽詞。
        - 以中英文標點切句,取前 N 句並截斷至 max_chars。
        """
        if not text:
            return None
        cleaned = re.sub(r"\s+", " ", text).strip()
        # 去掉常見前綴
        cleaned = re.sub(r"^(內容簡介|內容介紹|本書簡介|書籍簡介)\s*[::]?\s*", "", cleaned)
        if not cleaned:
            return None
        # 切句:保留分句符號
        parts = re.split(r"(?<=[。!?!?\.])\s*", cleaned)
        parts = [p.strip() for p in parts if p and p.strip()]
        if not parts:
            return cleaned[:max_chars]
        summary = "".join(parts[:max_sentences]).strip()
        if len(summary) > max_chars:
            summary = summary[: max_chars - 1].rstrip() + "…"
        return summary or None

    # ---- 總結 ----
    def summarize(self, keyword: str, books: list[BookLike], categories: list[str]) -> dict:
        total = len(books)
        if total == 0:
            return {
                "text": f"No books found for “{keyword}”.",
                "stats": {
                    "total": 0,
                    "avg_price": None,
                    "min_price": None,
                    "max_price": None,
                    "top_publishers": [],
                    "top_authors": [],
                    "category_distribution": [],
                    "primary_category": DEFAULT_CATEGORY,
                },
            }

        prices = [b for b in (getattr(x, "price", None) for x in books) if isinstance(b, int)]
        avg_price = round(sum(prices) / len(prices)) if prices else None
        min_price = min(prices) if prices else None
        max_price = max(prices) if prices else None

        publishers = [b.publisher for b in books if getattr(b, "publisher", None)]
        authors_raw = [b.authors for b in books if getattr(b, "authors", None)]
        # 作者欄位可能含 "/" 或 "、",做粗略切分
        authors_flat: list[str] = []
        for a in authors_raw:
            for part in str(a).replace("、", ",").replace("/", ",").split(","):
                p = part.strip()
                if p:
                    authors_flat.append(p)

        top_publishers = Counter(publishers).most_common(3)
        top_authors = Counter(authors_flat).most_common(3)
        cat_counter = Counter(categories)
        cat_dist = cat_counter.most_common()
        primary_category = cat_dist[0][0] if cat_dist else DEFAULT_CATEGORY

        # Compose narrative sentence
        parts = [f"Found {total} book(s) for “{keyword}”"]
        if cat_dist:
            head = ", ".join(f"{c} ({n})" for c, n in cat_dist[:3])
            parts.append(f"main categories: {head}")
        if avg_price is not None:
            parts.append(
                f"average price ~ NT$ {avg_price} (min {min_price} / max {max_price})"
            )
        if top_publishers:
            ph = ", ".join(f"{p} ({n})" for p, n in top_publishers)
            parts.append(f"top publishers: {ph}")
        if top_authors:
            ah = ", ".join(f"{a} ({n})" for a, n in top_authors)
            parts.append(f"top authors: {ah}")
        text = ". ".join(parts) + "."

        return {
            "text": text,
            "stats": {
                "total": total,
                "avg_price": avg_price,
                "min_price": min_price,
                "max_price": max_price,
                "top_publishers": [{"name": p, "count": n} for p, n in top_publishers],
                "top_authors": [{"name": a, "count": n} for a, n in top_authors],
                "category_distribution": [
                    {"category": c, "count": n} for c, n in cat_dist
                ],
                "primary_category": primary_category,
            },
        }
