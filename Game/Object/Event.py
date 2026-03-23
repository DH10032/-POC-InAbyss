import random


class Event:
    def __init__(self, name, desc, effect_fn=None):
        self.name = name
        self.desc = desc
        self.effect_fn = effect_fn

    def trigger(self, player):
        print(f"\n[이벤트] {self.name}")
        print(f"  {self.desc}")
        if self.effect_fn:
            self.effect_fn(player)


def _trap(player):
    damage = random.randint(5, 15) + player.layer * 2
    player.stat['HP'] = max(0, player.stat['HP'] - damage)
    print(f"  함정에 걸려 {damage} 데미지! (HP: {player.stat['HP']}/{player.max_hp})")


def _treasure(player):
    gold = random.randint(10, 30) * player.layer
    player.gold += gold
    print(f"  보물 발견! {gold} 골드 획득. (총 골드: {player.gold})")


def _monster(player):
    base = random.randint(8, 20)
    damage = max(0, base + player.layer * 3 - player.stat['STR'])
    player.stat['HP'] = max(0, player.stat['HP'] - damage)
    print(f"  몬스터와 격전! {damage} 데미지. (HP: {player.stat['HP']}/{player.max_hp})")


def _rest(player):
    heal = random.randint(5, 15)
    player.stat['HP'] = min(player.max_hp, player.stat['HP'] + heal)
    print(f"  아늑한 장소를 발견해 잠시 쉬었다. HP +{heal} (HP: {player.stat['HP']}/{player.max_hp})")


def _nothing(player):
    print("  조용히 탐험했다. 아무 일도 일어나지 않았다.")


EVENTS = [
    Event("함정", "바닥이 무너집니다!", _trap),
    Event("보물 상자", "먼지 쌓인 상자를 발견했습니다.", _treasure),
    Event("몬스터 조우", "어둠 속에서 무언가가 달려듭니다!", _monster),
    Event("은신처 발견", "작은 안전지대를 발견했습니다.", _rest),
    Event("평온한 탐험", "이번엔 별다른 일이 없었습니다.", _nothing),
]


def get_random_event(danger=1):
    """위험도에 따라 위험한 이벤트 확률 조정."""
    weights = [danger * 2, 1, danger * 3, max(1, 3 - danger), 2]
    return random.choices(EVENTS, weights=weights, k=1)[0]
