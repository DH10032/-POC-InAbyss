import json
import anthropic

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def generate_npc_dialogue(npc_context: dict, player_action: str, player_name: str) -> str:
    """NPC 성격·목표·기억·신뢰도를 바탕으로 대사를 생성한다."""
    trust = npc_context['trust_in_player']
    if trust > 30:
        attitude = "우호적"
    elif trust < -30:
        attitude = "적대적·경계"
    else:
        attitude = "중립·조심스러운"

    system = f"""당신은 텍스트 어드벤처 게임 '심연의 탐험자'의 NPC입니다.

[NPC 정보]
이름: {npc_context['name']}
성격: {npc_context['personality']}
목표: {npc_context['goal']} — {npc_context['goal_desc']}
현재 위치: {npc_context['location']}
{player_name}에 대한 태도: {attitude} (신뢰도 {trust:+d})
최근 기억:
{npc_context['recent_memory']}
현재 HP: {npc_context['hp']}

규칙:
- 위 정보에 충실하게 캐릭터를 연기하세요.
- 대화는 2~3문장 이내로 짧고 자연스럽게 작성하세요.
- 신뢰도와 성격에 따라 말투·태도를 조절하세요.
- 게임 내 세계관 외 언급은 하지 마세요."""

    message = _get_client().messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        system=system,
        messages=[{"role": "user", "content": f"[{player_name}의 행동] {player_action}"}],
    )
    return message.content[0].text


def decide_npc_action(npc_context: dict, situation: str) -> dict:
    """상황에 따라 NPC가 취할 행동을 결정한다. JSON 반환."""
    system = f"""당신은 NPC 행동 결정 엔진입니다.

[NPC 정보]
이름: {npc_context['name']}
성격: {npc_context['personality']}
목표: {npc_context['goal']}
신뢰도: {npc_context['trust_in_player']:+d}

다음 중 하나를 선택해 JSON으로만 응답하세요 (설명 없이):
{{"action": "협력", "reason": "한 줄 이유"}}
{{"action": "중립", "reason": "한 줄 이유"}}
{{"action": "배신", "reason": "한 줄 이유"}}
{{"action": "공격", "reason": "한 줄 이유"}}"""

    message = _get_client().messages.create(
        model="claude-opus-4-6",
        max_tokens=128,
        system=system,
        messages=[{"role": "user", "content": f"상황: {situation}"}],
    )
    try:
        return json.loads(message.content[0].text)
    except Exception:
        return {"action": "중립", "reason": "판단 불가"}
