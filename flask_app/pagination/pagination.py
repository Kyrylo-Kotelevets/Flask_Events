from flask_sqlalchemy import Pagination
from marshmallow import Schema


def create_pagination(*, items: Pagination, schema: Schema,
                      page: int = 1, limit: int = 20,
                      query_params=None, base_url: str):
    if items.total == 0:
        return {"message": "Nothing to show", "status": 200}

    if page > items.pages or page < 1:
        return {"message": "Invalid page number", "status": 404}

    response = {
        "page": f"page {page} of {items.pages}",
        "status": 200
    }

    if query_params is None:
        query_params = dict()

    # Add query parameters
    query_params = ''.join([f'&{key}={value}' for key, value in query_params.items()])

    # Add next page link if exists
    next_page_num = items.next_num
    response["next"] = f"{base_url}?page={next_page_num}&limit={limit}{query_params}" if next_page_num else None

    # Add prev page link if exists
    prev_page_num = items.prev_num
    response["prev"] = f"{base_url}?page={prev_page_num}&limit={limit}{query_params}" if prev_page_num else None

    # Add total number of items
    response["total"] = items.total

    # Add results
    response["results"] = schema.dump(items.items)

    return response
