def print_title():
    print("""
╔══════════════════════════════════════════╗
║         심  연  의  탐  험  자           ║
║            - In Abyss POC -              ║
╚══════════════════════════════════════════╝
""")


def print_separator(char='─', length=42):
    print(char * length)


def print_menu(options):
    print()
    for i, option in enumerate(options, 1):
        print(f"  [{i}] {option}")
    print()


def get_choice(options):
    while True:
        try:
            raw = input("선택 > ").strip()
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice
        except (ValueError, EOFError):
            pass
        print(f"  1 ~ {len(options)} 사이의 숫자를 입력하세요.")


def get_input(prompt):
    return input(prompt).strip()


def show_status(player):
    hp_bar_len = 20
    hp_ratio = player.stat['HP'] / player.max_hp
    filled = int(hp_bar_len * hp_ratio)
    hp_bar = '█' * filled + '░' * (hp_bar_len - filled)

    print(f"\n  {player.name} │ HP [{hp_bar}] {player.stat['HP']}/{player.max_hp}")
    print(f"  STR:{player.stat['STR']:>3}  DEX:{player.stat['DEX']:>3}  "
          f"VIT:{player.stat['VIT']:>3}  INT:{player.stat['INT']:>3}  │  "
          f"층:{player.layer}  골드:{player.gold}")
