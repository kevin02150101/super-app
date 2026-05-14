"""博客來爬蟲 Service — 完整移植自 book 原專案。

以 Playwright sync API 啟動 Chromium,瀏覽博客來搜尋頁,
解析搜尋結果為結構化 dict。
"""
from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from typing import Iterable
from urllib.parse import quote

from flask import current_app

from ..extensions import db
from ..models.book_record import BookResult, SearchQuery
from ..repositories.book_repository import BookResultRepository, SearchQueryRepository


BOOKS_SEARCH_URL = "https://search.books.com.tw/search/query/key/{kw}/cat/all"


@dataclass
class ScrapedBook:
    title: str
    authors: str | None
    publisher: str | None
    published_at: str | None
    price: int | None
    image_url: str | None
    product_url: str | None
    description: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class BookSearchService:
    """以 Playwright 對博客來執行書名查詢並回傳結構化資料。"""

    def search(self, keyword: str) -> dict:
        keyword = (keyword or "").strip()
        if not keyword:
            raise ValueError("關鍵字不可為空")

        started_at = time.perf_counter()
        headless = current_app.config.get("PLAYWRIGHT_HEADLESS", True)
        timeout_ms = current_app.config.get("SCRAPE_TIMEOUT_MS", 20000)
        max_results = current_app.config.get("SCRAPE_MAX_RESULTS", 20)
        detail_limit = current_app.config.get("SCRAPE_DETAIL_LIMIT", 5)

        url = BOOKS_SEARCH_URL.format(kw=quote(keyword, safe=""))

        from playwright.sync_api import sync_playwright

        scraped: list[ScrapedBook] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                locale="zh-TW",
                ignore_https_errors=True,
            )
            page = context.new_page()
            page.set_default_timeout(timeout_ms)
            try:
                page.goto(url, wait_until="commit")
                page.wait_for_selector(
                    "ul.searchbook li, .table-td, .item, .mod_b", timeout=timeout_ms
                )
                items = page.query_selector_all(
                    "ul.searchbook > li.item, ul.searchbook > li, .table-td, .mod_b .item"
                )
                for el in items[:max_results]:
                    book = self._parse_item(el)
                    if book and book.title:
                        scraped.append(book)

                detail_page = context.new_page()
                detail_page.set_default_timeout(min(timeout_ms, 12000))
                for book in scraped[:detail_limit]:
                    if book.product_url:
                        try:
                            book.description = self._fetch_description(
                                detail_page, book.product_url
                            )
                        except Exception:
                            book.description = None
                detail_page.close()
            finally:
                context.close()
                browser.close()

        duration_ms = int((time.perf_counter() - started_at) * 1000)

        # 寫入 DB
        sq = SearchQuery(
            keyword=keyword,
            result_count=len(scraped),
            duration_ms=duration_ms,
            source="books.com.tw",
        )
        SearchQueryRepository.add(sq)

        rows = [
            BookResult(
                query_id=sq.id,
                title=b.title,
                authors=b.authors,
                publisher=b.publisher,
                published_at=b.published_at,
                price=b.price,
                image_url=b.image_url,
                product_url=b.product_url,
                description=b.description,
            )
            for b in scraped
        ]
        BookResultRepository.add_many(rows)

        return {
            "query": sq.to_dict(),
            "results": [r.to_dict() for r in rows],
        }

    def history(self, limit: int = 50) -> list[dict]:
        items = []
        for q in SearchQueryRepository.find_recent(limit=limit):
            items.append({**q.to_dict()})
        return items

    def detail(self, query_id: int) -> dict | None:
        q = SearchQueryRepository.find_by_id(query_id)
        if not q:
            return None
        return {
            "query": q.to_dict(),
            "results": [
                r.to_dict() for r in BookResultRepository.find_by_query_id(query_id)
            ],
        }

    def stats(self) -> dict:
        return {
            "top_keywords": [
                {"keyword": k, "count": c}
                for k, c in SearchQueryRepository.top_keywords(limit=10)
            ],
            "top_publishers": [
                {"publisher": p, "count": c}
                for p, c in BookResultRepository.top_publishers(limit=10)
            ],
        }

    # ---- helpers ----
    def _parse_item(self, el) -> ScrapedBook | None:
        try:
            title_el = el.query_selector("h3 a, .msg a, h4 a")
            title = (title_el.inner_text().strip() if title_el else "") or ""
            product_url = title_el.get_attribute("href") if title_el else None
            if product_url and product_url.startswith("//"):
                product_url = "https:" + product_url

            img_el = el.query_selector("img")
            image_url = None
            if img_el:
                image_url = (
                    img_el.get_attribute("data-original")
                    or img_el.get_attribute("data-src")
                    or img_el.get_attribute("src")
                )
                if image_url and image_url.startswith("//"):
                    image_url = "https:" + image_url

            authors = self._extract_text(
                el, [".author a", ".info a", ".type02_bd-a a"]
            )
            publisher = self._extract_text(
                el,
                [".publisher a", ".info .publish", ".type02_bd-a > a:nth-child(2)"],
            )
            published_at = self._extract_text(
                el, [".publish_date", ".type02_bd-a > span"]
            )
            price = self._parse_price(el)

            return ScrapedBook(
                title=title,
                authors=authors,
                publisher=publisher,
                published_at=published_at,
                price=price,
                image_url=image_url,
                product_url=product_url,
            )
        except Exception:
            return None

    @staticmethod
    def _extract_text(el, selectors: Iterable[str]) -> str | None:
        for sel in selectors:
            try:
                node = el.query_selector(sel)
                if node:
                    txt = node.inner_text().strip()
                    if txt:
                        return txt
            except Exception:
                continue
        return None

    @staticmethod
    def _parse_price(el) -> int | None:
        candidates: list[int] = []
        try:
            price_node = el.query_selector(".price, ul.price")
            if price_node:
                txt = price_node.inner_text()
                for m in re.finditer(r"(\d[\d,]*)\s*元", txt):
                    val = int(m.group(1).replace(",", ""))
                    if val >= 10:
                        candidates.append(val)
        except Exception:
            pass
        if candidates:
            return candidates[0]
        return None

    @staticmethod
    def _fetch_description(page, url: str) -> str | None:
        try:
            page.goto(url, wait_until="domcontentloaded")
        except Exception:
            return None
        selectors = [
            "div.content_a div.bd",
            "div.content_a",
            "section.bookIntro",
            "#content_1 .bd",
            "div[itemprop='description']",
        ]
        for sel in selectors:
            try:
                node = page.query_selector(sel)
                if node:
                    text = node.inner_text().strip()
                    if text and len(text) >= 30:
                        text = re.sub(r"\s+\n", "\n", text)
                        text = re.sub(r"\n{2,}", "\n\n", text)
                        return text[:4000]
            except Exception:
                continue
        return None
