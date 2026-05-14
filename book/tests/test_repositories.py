from app.models.book_result import BookResult
from app.models.search_query import SearchQuery
from app.repositories.book_result_repository import BookResultRepository
from app.repositories.search_query_repository import SearchQueryRepository


def test_search_query_crud_and_stats(app):
    repo = SearchQueryRepository()
    book_repo = BookResultRepository()

    q1 = repo.add(SearchQuery(keyword="python", result_count=3, duration_ms=120))
    q2 = repo.add(SearchQuery(keyword="python", result_count=5, duration_ms=130))
    q3 = repo.add(SearchQuery(keyword="flask", result_count=2, duration_ms=110))

    assert repo.count_total() == 3
    assert repo.count_distinct_keywords() == 2
    top = repo.top_keywords(limit=5)
    assert top[0] == ("python", 2)

    book_repo.add_many([
        BookResult(query_id=q1.id, title="Python A", publisher="O'Reilly", price=500),
        BookResult(query_id=q2.id, title="Python B", publisher="O'Reilly", price=400),
        BookResult(query_id=q3.id, title="Flask C", publisher="天瓏", price=600),
    ])
    assert book_repo.count_total() == 3
    assert round(book_repo.avg_price()) == 500
    pubs = book_repo.top_publishers()
    assert pubs[0][0] == "O'Reilly"

    # search by keyword
    found = repo.search_by_keyword("py")
    assert {x.id for x in found} == {q1.id, q2.id}

    # delete cascades
    assert repo.delete(q1.id) is True
    assert book_repo.find_by_query_id(q1.id) == []
