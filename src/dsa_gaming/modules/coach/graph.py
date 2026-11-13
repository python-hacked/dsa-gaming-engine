from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from dsa_gaming.modules.coach.gemini import complete
from dsa_gaming.modules.coach.lessons import wants_solution
from dsa_gaming.modules.coach.repository import nearest_bodies


class CoachState(TypedDict, total=False):
    message: str
    mode: str
    task: str
    language: str
    performance: str
    source: str
    target: str
    lessons: str
    history: str
    reply: str


def choose_mode(state: CoachState) -> CoachState:
    state["mode"] = "solution" if wants_solution(state.get("message", "")) else "hint"
    return state


async def retrieve(state: CoachState, config) -> CoachState:
    settings = config["configurable"]
    vector = None
    if settings["api_key"]:
        try:
            from dsa_gaming.modules.coach.gemini import embed_text

            vector = await embed_text(settings["api_key"], state["message"])
        except Exception:
            vector = None
    bodies = await nearest_bodies(settings["session"], settings["slug"], vector)
    state["lessons"] = "\n\n".join(bodies)
    return state


async def respond(state: CoachState, config) -> CoachState:
    mode = state.get("mode", "hint")
    if mode == "solution":
        ask = (
            "The player asked for the solution. Write one complete program in the selected language. "
            "It must read stdin and print the JSON shape from the lesson. Use the hidden target."
        )
    else:
        ask = (
            "Explain the logic for this task in a few short steps. "
            "Do not write the full program and do not reveal the hidden target."
        )
    prompt = "\n".join(
        [
            "You are the AI assistant for one DSA game.",
            "Reply in the same language as the player's latest message: Hindi, English, Chinese, Korean, or any other language.",
            "Lessons and task notes are English. Do not switch your reply to English because of them.",
            "If the player mixes languages, follow the language of the question.",
            f"Task: {state.get('task', '')}",
            f"Programming language: {state.get('language', 'Python')}. Any code you show uses only this language. Comments in that code follow the player's language.",
            f"Performance for this player only: {state.get('performance', '')}",
            f"Lesson:\n{state.get('lessons', '')}",
            f"Earlier messages from this player:\n{state.get('history', '')}",
            f"Code currently in the editor:\n{state.get('source', '')}",
            f"Hidden target, solution mode only:\n{state.get('target', '')}",
            ask,
            f"Player: {state.get('message', '')}",
        ]
    )
    state["reply"] = await complete(config["configurable"]["api_key"], prompt)
    return state


def build_graph():
    graph = StateGraph(CoachState)
    graph.add_node("mode", choose_mode)
    graph.add_node("retrieve", retrieve)
    graph.add_node("respond", respond)
    graph.add_edge(START, "mode")
    graph.add_edge("mode", "retrieve")
    graph.add_edge("retrieve", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


coach_graph = build_graph()
