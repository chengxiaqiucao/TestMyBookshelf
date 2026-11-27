"""WebSocket 实时推送（需求 1.4；注入 S2-F09 靶点）。

S2-F09：推送的完成率使用未取整原始比例，与 HTTP 接口 round() 后的值不一致。
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

from .services import statistics as stats_service

router = APIRouter()


@router.websocket("/ws/stats")
async def stats_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            overview = stats_service.get_overview()
            total_tasks = overview["total_plans"] or 1
            # S2-F09：未取整的比例，与 HTTP 的 completion_rate 不同
            raw_rate = overview["completed_plans"] / total_tasks * 100
            await websocket.send_json({"type": "stats", "completion_rate": raw_rate, **overview})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
