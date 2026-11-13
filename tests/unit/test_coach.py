from fastapi.testclient import TestClient

from dsa_gaming.main import create_app
from dsa_gaming.modules.coach.lessons import wants_solution


def test_solution_requests_are_detected():
    assert wants_solution("give the full code")
    assert wants_solution("poora code dedo")
    assert wants_solution("पूरा कोड दो")
    assert wants_solution("给我完整代码")
    assert wants_solution("전체 코드 줘")
    assert not wants_solution("what is the logic")
    assert not wants_solution("इसका logic बताओ")


def test_coach_requires_a_signed_in_player():
    with TestClient(create_app()) as client:
        response = client.post("/api/coach/stack-brackets", json={"message": "logic", "round_id": 1})
    assert response.status_code == 401
