import os
import sys

class Person:
    def __init__(self, name):
        self.name = name
        self.stat = {'STR': 0, 'DEX': 0, 'HP':0, 'VIT': 0, 'INT':0}
        self.inven = []
        return

    def InputStat(self):
        for key in self.stat:
            self.stat[key] = input(f"{key} 능력치를 입력해주세요.\n")
        sys.os('clear')

class NPC(Person):
    def __init__(self, name):
        super().__init__(name)
        super().InputStat()

    def showInfo(self):
        print(self.stat)
        print(self.inven)

NPC_lst = {}
name = input('NPC 이름\n')
NPC_lst[name] = NPC(name)
