"""博客來網路書店爬蟲服務 (Playwright)。

> 設計備註:本服務以 Playwright 同步 API 啟動 Chromium,瀏覽博客來搜尋頁,
> 解析搜尋結果為 dict 清單。Service 僅負責產生領域資料,不直接接觸 DB。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Iterable
from urllib.parse import quote

from flask import current_app


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

    def __init__(self, headless: bool | None = None, timeout_ms: int | None = None):
        self._headless = headless
        self._timeout_ms = timeout_ms

    # ---- public ----
    def search(self, keyword: str, max_results: int | None = None) -> list[ScrapedBook]:
        keyword = (keyword or "").strip()
        if not keyword:
            raise ValueError("Keyword must not be empty")

        headless = (
            self._headless
            if self._headless is not None
            else current_app.config.get("PLAYWRIGHT_HEADLESS", True)
        )
        timeout_ms = self._timeout_ms or current_app.config.get(
            "SCRAPE_TIMEOUT_MS", 20000
        )
        max_results = max_results or current_app.config.get("SCRAPE_MAX_RESULTS", 20)

        url = BOOKS_SEARCH_URL.format(kw=quote(keyword, safe=""))

        # 對前 N 本抓詳情頁簡介(避免整批進入詳情頁過慢)
        detail_limit = current_app.config.get("SCRAPE_DETAIL_LIMIT", 8)

        # Lazy import:避免測試環境在未安裝 playwright 時 import 失敗。
        from playwright.sync_api import sync_playwright

        results: list[ScrapedBook] = []
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
                # 不同版型容器:嘗試多個選擇器
                page.wait_for_selector(
                    "ul.searchbook li, .table-td, .item, .mod_b", timeout=timeout_ms
                )
                items = page.query_selector_all(
                    "ul.searchbook > li.item, ul.searchbook > li, .table-td, .mod_b .item"
                )
                for el in items[:max_results]:
                    book = self._parse_item(el)
                    if book and book.title:
                        results.append(book)

                # 對前 detail_limit 本抓詳情頁簡介
                detail_page = context.new_page()
                # Detail pages are optional; keep this short so one slow product
                # page doesn't block the whole search request.
                detail_page.set_default_timeout(min(timeout_ms, 7000))
                for book in results[:detail_limit]:
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
        return results

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
                el, [".publisher a", ".info .publish", ".type02_bd-a > a:nth-child(2)"]
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
        # 博客來搜尋頁 .price 結構常見為:
        #   <ul class="price">
        #     <li><strong><b>79</b></strong>折</li>     <- 折扣數
        #     <li><strong><b>869</b></strong>元</li>    <- 售價
        #     <li>...定價:<b>1100</b>元...</li>         <- 定價
        #   </ul>
        # 因此第一個 <b> 取到的是 79(折扣數),必須改用「<數字>元」的型態判斷。

        # 1) 走訪 .price 內所有文字,抓出全部「<數字>元」候選
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
            # 第一個通常是「優惠價/特價」,取它即可
            return candidates[0]

        # 2) 後備:嘗試各個只含金額的精準節點,但要排除「折」字附近的數字
        for sel in [".set2 b", ".price strong b", ".price b"]:
            try:
                nodes = el.query_selector_all(sel)
                for node in nodes:
                    raw = node.inner_text()
                    # 取得父節點文字以判斷是否為折扣數
                    parent_txt = ""
                    try:
                        parent = node.evaluate_handle(
                            "n => n.parentElement && n.parentElement.parentElement"
                        )
                        if parent:
                            parent_txt = parent.evaluate("n => n ? n.textContent : ''") or ""
                    except Exception:
                        parent_txt = ""
                    if "折" in parent_txt and "元" not in parent_txt:
                        continue
                    m = re.search(r"(\d[\d,]{1,})", raw)
                    if m:
                        val = int(m.group(1).replace(",", ""))
                        if val >= 10:
                            return val
            except Exception:
                continue
        return None

    @staticmethod
    def _fetch_description(page, url: str) -> str | None:
        """進入商品詳情頁取「內容簡介」段落。"""
        try:
            page.goto(url, wait_until="domcontentloaded")
        except Exception:
            return None
        # 博客來常見的內容簡介容器
        selectors = [
            "div.content_a div.bd",          # 新版
            "div.content_a",                 # 退而求其次
            "section.bookIntro",             # 部分書籍
            "#content_1 .bd",
            "div[itemprop='description']",
        ]
        for sel in selectors:
            try:
                node = page.query_selector(sel)
                if node:
                    text = node.inner_text().strip()
                    # 過濾過短或純導覽
                    if text and len(text) >= 30:
                        # 壓縮空白
                        text = re.sub(r"\s+\n", "\n", text)
                        text = re.sub(r"\n{2,}", "\n\n", text)
                        return text[:4000]
            except Exception:
                continue
        return None
