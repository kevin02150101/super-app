from app.services.summary_service import BookLike, SummaryService


def test_classify_python_book():
    s = SummaryService()
    cat = s.classify(BookLike(title="Python 入門", publisher="碁峰"))
    assert cat == "程式設計"


def test_classify_fallback_keyword_when_book_blank():
    s = SummaryService()
    cat = s.classify(BookLike(title="某某書"), fallback_keyword="深度學習")
    assert cat == "AI / 資料科學"


def test_classify_unknown_returns_default():
    s = SummaryService()
    assert s.classify(BookLike(title="不知名的東西")) == "其他"


def test_summarize_combines_stats():
    s = SummaryService()
    books = [
        BookLike(title="Python A", authors="王小明", publisher="碁峰"),
        BookLike(title="Java B", authors="李四/張三", publisher="碁峰"),
        BookLike(title="深度學習導論", authors="Goodfellow", publisher="天瓏"),
    ]
    # 模擬 price 屬性(BookLike 沒有 price,使用 setattr)
    for b, p in zip(books, [320, 480, 900]):
        setattr(b, "price", p)
    cats = s.classify_many(books)
    out = s.summarize("python", books, cats)
    assert out["stats"]["total"] == 3
    assert out["stats"]["avg_price"] == round((320 + 480 + 900) / 3)
    assert out["stats"]["primary_category"] in {"程式設計", "AI / 資料科學"}
    assert "找到 3 本書" in out["text"]
    assert any(c["category"] == "程式設計" for c in out["stats"]["category_distribution"])


def test_summarize_empty():
    out = SummaryService().summarize("xx", [], [])
    assert out["stats"]["total"] == 0
    assert "沒有找到" in out["text"]


def test_summarize_text_truncates_to_first_sentences():
    s = SummaryService()
    text = (
        "內容簡介:本書介紹 Python 的各種應用。從基礎語法到進階主題,作者帶你一步步深入。"
        "此外,書中包含大量範例程式碼。最後,提供完整的專案實作。"
    )
    out = s.summarize_text(text, max_sentences=2, max_chars=100)
    assert out is not None
    # 不再有「內容簡介」前綴
    assert not out.startswith("內容簡介")
    assert "本書介紹" in out
    # 不會超過 max_chars
    assert len(out) <= 100


def test_summarize_text_handles_blank():
    assert SummaryService().summarize_text(None) is None
    assert SummaryService().summarize_text("   ") is None


def test_search_record_writes_summary_per_book(app):
    from app.services.book_search_service import ScrapedBook
    from app.services.search_record_service import SearchRecordService

    class FakeScraper:
        def search(self, keyword, max_results=None):
            b = ScrapedBook(
                title="Python 進階",
                authors="某作者",
                publisher="碁峰",
                published_at="2024",
                price=520,
                image_url=None,
                product_url="http://x/p",
            )
            b.description = (
                "本書深入介紹 Python 進階技巧。包含 metaclass、descriptor、async 等主題。"
                "適合中階以上工程師閱讀。"
            )
            return [b]

    out = SearchRecordService(scraper=FakeScraper()).search_and_store("python")
    r = out["results"][0]
    assert r["description"]
    assert r["summary"]
    assert "Python 進階" in r["description"]
