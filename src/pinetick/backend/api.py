from fastapi import APIRouter, Request

from pinetick.backend.orm import TickerLog

router = APIRouter(prefix="/api")

@router.get("/")
def get(request: Request):
    db = request.state.db
    return db.query(TickerLog).all()
