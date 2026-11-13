import json

from sqlalchemy.ext.asyncio import AsyncSession

from dsa_gaming.modules.catalog.data import LANGUAGES
from dsa_gaming.modules.coach.graph import coach_graph
from dsa_gaming.modules.coach.repository import (
    add_message,
    ensure_lesson_rows,
    performance_line,
    recent_messages,
    save_embedding,
)
from dsa_gaming.modules.coach.gemini import embed_text
from dsa_gaming.modules.gameplay.service import public_payload


def language_name(code: str) -> str:
    for item, name in LANGUAGES:
        if item == code:
            return name
    return "Python"


async def index_lessons(session: AsyncSession, api_key: str) -> None:
    rows = await ensure_lesson_rows(session)
    if not api_key:
        return
    for row in rows:
        if row.embedding is not None:
            continue
        vector = await embed_text(api_key, row.body)
        await save_embedding(session, row, vector)


async def coach_reply(
    session: AsyncSession,
    *,
    api_key: str,
    user_id: int,
    slug: str,
    task: str,
    language: str,
    message: str,
    source: str,
    payload: dict,
) -> dict:
    await index_lessons(session, api_key)
    stats = await performance_line(session, user_id, slug)
    history_rows = await recent_messages(session, user_id, slug)
    history = "\n".join(f"{row.role}: {row.content}" for row in history_rows)
    shown = public_payload(payload)
    result = await coach_graph.ainvoke(
        {
            "message": message,
            "task": task,
            "language": language_name(language),
            "performance": stats,
            "source": source[:4000],
            "target": json.dumps(payload),
            "history": history,
            "lessons": json.dumps(shown),
        },
        config={"configurable": {"session": session, "slug": slug, "api_key": api_key}},
    )
    reply = result["reply"]
    await add_message(session, user_id, slug, "player", message)
    await add_message(session, user_id, slug, "assistant", reply)
    return {"reply": reply, "language": language_name(language), "performance": stats}
