import os
import sys

class Person:
    def __init__(self, name):
        self.name = name
        self.stat = {'STR': 0, 'DEX': 0, 'HP':0, 'VIT': 0, 'INT':0}
        self.inven = []
        self.Personality = []
        self.goal = ''
        self.local = ''
        return

    def UpdateStat(self, stat_name):
        self.stat[stat_name] = self.stat[stat_name] + 1

    def UpdateInven(self, item, ty):
        if ty == '+':
            self.inven.append(item)

        elif ty == '-':
            try:
                self.inven.pop(item)
            except:
                print('존재하지 않는 아이템입니다.')
        return item

    def CreatePesrsonality(self):
        # 성격 랜덤 생성
        return

    def CreateGoal(self):
        # 캐릭터의 목표
        return

    def UpdatePostion(self, local):
        self.local = local
        return

    def CreateMemory(self):
        # 위에서 생성된 정보들을 바탕으로 기억 생성 (성격 및 가치관 등등과 연관)

        return

    def UpdatePesonMemory(self, Memory, VectorMeomory):
        # 클로드에서 주는 임베딩 기억과 일반 기억을 같이 저장


        return

    def ImportMemory(self):
        # 기억 연관성 비교

        # 신뢰성
        return

class Player(Person):
    def __init__(self, name):
        super().__init__(name)
        super().InputStat()

    def showInfo(self):
        print(self.stat)
        print(self.inven)

class NPC(Person):
    def __init__(self, name):
        super().__init__(name)
        super().InputStat()

    def showInfo(self):
        print(self.stat)
        print(self.inven)


class Relationship:
    def __init__(self, lst):
        return
