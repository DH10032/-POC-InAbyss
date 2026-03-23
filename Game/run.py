import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from Object.Character import Player, NPC
from Object.World import World
from Object.Event import get_random_event
from Features import UI, API


# ── 캐릭터 생성 ────────────────────────────────────────────────
def create_player() -> Player:
    UI.print_title()
    print("  탐험가를 만들어 봅시다.\n")
    name = UI.get_input("  이름을 입력하세요: ")
    player = Player(name)
    player.create_personality()

    traits = ', '.join([p['name'] for p in player.personality])
    print(f"\n  당신의 성격: {traits}")

    BACKGROUNDS = [
        ("전사",   {'STR': 3, 'VIT': 2}),
        ("탐험가", {'DEX': 3, 'INT': 2}),
        ("학자",   {'INT': 4, 'DEX': 1}),
    ]
    print("\n  배경을 선택하세요:")
    labels = []
    for bg_name, stats in BACKGROUNDS:
        parts = [f"{k}+{v}" for k, v in stats.items()]
        labels.append(f"{bg_name}  ({', '.join(parts)})")
    UI.print_menu(labels)
    choice = UI.get_choice(labels)

    bg_name, bg_stats = BACKGROUNDS[choice - 1]
    for stat, val in bg_stats.items():
        player.stat[stat] += val
    print(f"\n  '{bg_name}' 배경을 선택했습니다.")
    return player


# ── NPC와 대화 ─────────────────────────────────────────────────
def talk_to_npc(player: Player, layer):
    alive_npcs = [npc for npc in layer.npcs if npc.is_alive()]
    if not alive_npcs:
        print("\n  이 층에는 대화할 탐험가가 없습니다.")
        return

    print("\n  누구와 대화하시겠습니까?")
    UI.print_menu([npc.name for npc in alive_npcs])
    npc = alive_npcs[UI.get_choice(alive_npcs) - 1]

    action = UI.get_input(f"\n  {npc.name}에게: ")
    if not action:
        return

    npc_ctx = npc.get_context(player.name)
    print()
    try:
        response = API.generate_npc_dialogue(npc_ctx, action, player.name)
        print(f"  {npc.name}: {response}")
        npc.update_trust(player.name, 2)
        player.update_relationship(npc.name, 2)
        npc.add_memory(f"{player.name}이(가) \"{action}\"라고 말했다")
        player.add_memory(f"{npc.name}과(와) 대화했다")
    except Exception as e:
        print(f"  {npc.name}: ... (통신 오류: {e})")


# ── 게임 루프 ──────────────────────────────────────────────────
def game_loop(player: Player, world: World):
    print(f"\n  탐험을 시작합니다. 행운을 빕니다, {player.name}.\n")

    while player.is_alive():
        layer = world.get_layer(player.layer)
        layer.describe()
        UI.show_status(player)

        options = ["탐험하기", "NPC와 대화", "내 정보 보기", "더 깊이 내려가기"]
        if player.layer > 1:
            options.append("위로 올라가기")
        options.append("게임 종료")

        if player.layer >= world.max_depth:
            options.remove("더 깊이 내려가기")

        UI.print_menu(options)
        chosen = options[UI.get_choice(options) - 1]

        if chosen == "탐험하기":
            event = get_random_event(danger=layer.danger)
            event.trigger(player)
            player.add_memory(f"{layer.name}에서 '{event.name}' 발생")

        elif chosen == "NPC와 대화":
            talk_to_npc(player, layer)

        elif chosen == "내 정보 보기":
            player.show_info()

        elif chosen == "더 깊이 내려가기":
            player.layer += 1
            next_layer = world.get_layer(player.layer)
            print(f"\n  어둠 속으로 더 내려갑니다... [{player.layer}층] {next_layer.name}")
            player.add_memory(f"{player.layer}층에 도달했다")

        elif chosen == "위로 올라가기":
            player.layer -= 1
            prev_layer = world.get_layer(player.layer)
            print(f"\n  위로 올라갑니다... [{player.layer}층] {prev_layer.name}")

        elif chosen == "게임 종료":
            print(f"\n  {player.name}은(는) 탐험을 마칩니다.")
            break

        if not player.is_alive():
            print(f"\n  {player.name}은(는) 심연에서 쓰러졌습니다...")

    print(f"\n  ─ 최종 결과 ─")
    print(f"  도달 층: {player.layer}층  │  획득 골드: {player.gold}")
    print(f"  탐험 횟수: {len(player.memory)}회\n")


# ── 엔트리포인트 ───────────────────────────────────────────────
def main():
    player = create_player()

    world = World(max_depth=4)

    npc_roster = [
        ("카이",  1),
        ("루나",  1),
        ("드락",  2),
        ("시아",  3),
        ("오르",  4),
    ]
    for npc_name, depth in npc_roster:
        npc = NPC(npc_name)
        world.add_npc_to_layer(npc, depth)

    player.update_position(f"1층 - {world.get_layer(1).name}")

    game_loop(player, world)


if __name__ == '__main__':
    main()
