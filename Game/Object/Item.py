class Item:
    def __init__(self, name, item_type, desc, effects):
        self.name = name
        self.type = item_type
        self.desc = desc
        self.effects = effects  # dict e.g. {"HP": 20}, {"STR": 2}

    def use(self, person):
        """소모품 사용. 성공 시 True 반환."""
        if self.type == 'consumable':
            for stat, value in self.effects.items():
                if stat in person.stat:
                    person.stat[stat] = min(
                        person.stat[stat] + value,
                        person.max_hp if stat == 'HP' else person.stat[stat] + value
                    )
            return True
        return False

    def __repr__(self):
        return f"[{self.type}] {self.name}: {self.desc}"
