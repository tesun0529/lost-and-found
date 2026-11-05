
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import requests

app = FastAPI(title="경찰청 유실물 검색")

POLICE_URL = "https://minwon24.police.go.kr/wisenut/search.do"

class SearchRequest(BaseModel):
    query: str
    page: int = 1

@app.get("/")
def home():
    return {"message": "유실물 검색 서버가 실행 중입니다."}

@app.post("/search")
def search_lost_items(data: SearchRequest):
    today = datetime.now()
    start = today - timedelta(days=7)

    payload = {
        "query": data.query,
        "searchFields": ["_ALL_"],
        "resultFields": ["_ALL_"],
        "collections": ["FOUND"],
        "pageStart": data.page,
        "pageCount": "10",
        "orderBys": ["DATE/DESC"],
        "subQueries": {
            "MODE": "DETAIL",
            "SNIPPET_SIZE": "200",
            "HL_TERM": "",
            "FOUND_FILTER_QUERY": "",
            "FOUND_COLLECTION_QUERY": "",
            "START_DATE": start.strftime("%Y%m%d000000"),
            "END_DATE": today.strftime("%Y%m%d235959")
        }
    }

    try:
        response = requests.post(
            POLICE_URL,
            json=payload,
            timeout=20
        )
        response.raise_for_status()
        result = response.json()

        documents = (
            result.get("result", {})
            .get("outputs", {})
            .get("FOUND", {})
            .get("documents", [])
        )

        items = []
        for doc in documents:
            fields = doc.get("fields", {})
            items.append({
                "item": fields.get("ITEM_CN"),
                "title": fields.get("PSTG_TTL"),
                "date": fields.get("LOST_CMDTY_PKUP_YMD"),
                "region": fields.get("SGG_NM"),
                "place": fields.get("KPNG_PLC_NM")
            })

        return {
            "total": result.get("result", {}).get("totalCount", 0),
            "items": items
        }

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"경찰청 검색 요청 실패: {str(e)}"
        )
