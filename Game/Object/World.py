import random

LAYER_DATA = [
    {
        "name": "입구 층",
        "desc": "심연의 첫 번째 층. 빛이 아직 닿는 곳이다. 탐험가들이 자주 드나드는 상대적으로 안전한 구역.",
        "danger": 1,
    },
    {
        "name": "안개 층",
        "desc": "짙은 안개가 시야를 가린다. 방향 감각을 잃기 쉽고, 무언가 숨어있는 느낌이 든다.",
        "danger": 2,
    },
    {
        "name": "결정 층",
        "desc": "거대한 수정들이 빛을 반사한다. 아름답지만, 그 날카로운 결정들은 치명적이다.",
        "danger": 3,
    },
    {
        "name": "심연의 심장",
        "desc": "여기까지 내려온 탐험가는 거의 없다. 공기 자체가 다르고, 중력도 이상하게 느껴진다.",
        "danger": 5,
    },
]


class Layer:
    def __init__(self, depth):
        self.depth = depth
        data = LAYER_DATA[min(depth - 1, len(LAYER_DATA) - 1)]
        self.name = data['name']
        self.desc = data['desc']
        self.danger = data['danger']
        self.npcs = []

    def add_npc(self, npc):
        self.npcs.append(npc)

    def describe(self):
        print(f"\n{'='*42}")
        print(f"  [{self.depth}층] {self.name}")
        print(f"{'='*42}")
        print(f"  {self.desc}")
        print(f"  위험도: {'★' * self.danger}{'☆' * (5 - self.danger)}")
        if self.npcs:
            alive = [npc.name for npc in self.npcs if npc.is_alive()]
            if alive:
                print(f"  이 층의 탐험가: {', '.join(alive)}")
        print()


class World:
    def __init__(self, max_depth=4):
        self.max_depth = max_depth
        self.layers = {i: Layer(i) for i in range(1, max_depth + 1)}

    def get_layer(self, depth):
        return self.layers.get(depth)

    def add_npc_to_layer(self, npc, depth):
        layer = self.get_layer(depth)
        if layer:
            layer.add_npc(npc)
            npc.update_position(f"{depth}층 - {layer.name}")
