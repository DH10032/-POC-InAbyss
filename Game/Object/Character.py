import json
import os
import random

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data')


class Person:
    def __init__(self, name):
        self.name = name
        self.stat = {'STR': 5, 'DEX': 5, 'HP': 50, 'VIT': 5, 'INT': 5}
        self.max_hp = 50
        self.inven = []
        self.personality = []
        self.goal = None
        self.local = ''
        self.memory = []

    def update_stat(self, stat_name, value=1):
        if stat_name in self.stat:
            self.stat[stat_name] += value

    def update_inven(self, item, action):
        if action == '+':
            self.inven.append(item)
        elif action == '-':
            if item in self.inven:
                self.inven.remove(item)
            else:
                print('존재하지 않는 아이템입니다.')
        return item

    def create_personality(self):
        with open(os.path.join(DATA_PATH, 'Personality.json'), 'r', encoding='utf-8') as f:
            traits = json.load(f)
        count = random.randint(1, 3)
        self.personality = random.sample(traits, min(count, len(traits)))
        for trait in self.personality:
            for stat, val in trait.get('effects', {}).items():
                if stat in self.stat:
                    self.stat[stat] += val

    def create_goal(self):
        with open(os.path.join(DATA_PATH, 'Goal.json'), 'r', encoding='utf-8') as f:
            goals = json.load(f)
        self.goal = random.choice(goals)

    def update_position(self, local):
        self.local = local

    def add_memory(self, memory_text):
        self.memory.append(memory_text)
        if len(self.memory) > 20:
            self.memory = self.memory[-20:]

    def get_memory_summary(self):
        return '\n'.join(self.memory[-5:]) if self.memory else '없음'

    def is_alive(self):
        return self.stat['HP'] > 0

    def show_info(self):
        print(f"\n=== {self.name} ===")
        print(f"위치: {self.local}")
        print(f"HP: {self.stat['HP']}/{self.max_hp}")
        print(f"스탯 - STR:{self.stat['STR']} DEX:{self.stat['DEX']} VIT:{self.stat['VIT']} INT:{self.stat['INT']}")
        print(f"성격: {', '.join([p['name'] for p in self.personality]) or '없음'}")
        if self.goal:
            print(f"목표: {self.goal['name']} - {self.goal['desc']}")
        print(f"인벤토리: {[str(i) for i in self.inven] or '비어있음'}")


class Player(Person):
    def __init__(self, name):
        super().__init__(name)
        self.relationships = {}  # {npc_name: trust (-100 ~ 100)}
        self.layer = 1
        self.gold = 0

    def get_relationship(self, npc_name):
        return self.relationships.get(npc_name, 0)

    def update_relationship(self, npc_name, delta):
        current = self.relationships.get(npc_name, 0)
        self.relationships[npc_name] = max(-100, min(100, current + delta))

    def show_info(self):
        super().show_info()
        print(f"현재 층: {self.layer}층 | 골드: {self.gold}")
        if self.relationships:
            print("관계:")
            for npc_name, trust in self.relationships.items():
                if trust > 30:
                    status = "우호적"
                elif trust < -30:
                    status = "적대적"
                else:
                    status = "중립"
                print(f"  {npc_name}: {trust:+d} ({status})")


class NPC(Person):
    def __init__(self, name):
        super().__init__(name)
        self.create_personality()
        self.create_goal()
        self.trust = {}  # {name: trust}
        self.is_hostile = False

    def get_personality_desc(self):
        return ', '.join([p['name'] for p in self.personality])

    def get_context(self, player_name):
        return {
            'name': self.name,
            'personality': self.get_personality_desc(),
            'goal': self.goal['name'] if self.goal else '없음',
            'goal_desc': self.goal['desc'] if self.goal else '',
            'location': self.local,
            'trust_in_player': self.trust.get(player_name, 0),
            'recent_memory': self.get_memory_summary(),
            'hp': self.stat['HP'],
        }

    def update_trust(self, name, delta):
        current = self.trust.get(name, 0)
        self.trust[name] = max(-100, min(100, current + delta))


class Relationship:
    def __init__(self):
        self.relations = {}  # {(p1, p2): trust}

    def get(self, p1, p2):
        key = tuple(sorted([p1, p2]))
        return self.relations.get(key, 0)

    def update(self, p1, p2, delta):
        key = tuple(sorted([p1, p2]))
        current = self.relations.get(key, 0)
        self.relations[key] = max(-100, min(100, current + delta))
