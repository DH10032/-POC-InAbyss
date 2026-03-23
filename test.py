import sys
import json
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# ── 색상 ──────────────────────────────────────────────────
BG    = "#0a0806"
BG2   = "#12100d"
BG3   = "#1a1612"
BORDER= "#2e2820"
GOLD  = "#c9a84c"
GOLD2 = "#8b6914"
RED   = "#c0392b"
GREEN = "#27ae60"
TEXT  = "#d4c9b0"
DIM   = "#7a6e5a"
BRIGHT= "#ede0c4"

# ── API 설정 ───────────────────────────────────────────────
API_URL = "https://api.anthropic.com/v1/messages"
API_KEY = "여기에_API_키_입력"  # ← 본인 키 입력

SYSTEM_PROMPT = """너는 던전 속 텍스트 RPG의 게임 마스터야.
세계의 규칙을 따르고, 캐릭터를 살아있게 연기해.
플레이어의 자유 입력을 받아 판정하고, 결과를 묘사해.

규칙:
- 판정은 D20 + 관련 능력치 보정치로 결정한다.
- NPC는 자신의 values와 goal에 따라 행동한다.
- 관계 태그가 쌓일수록 NPC의 반응이 달라진다.
- 감정적으로 중요한 순간에는 묘사를 풍부하게 해라.
- 보정치 없이 20이 나오면 완벽한 성공, 1이 나오면 치명적 실수로 전장이 뒤집힌다.
- HP 변화는 hp_changes 필드에 반드시 반영해라. 피해는 음수, 회복은 양수.
- 몬스터도 공격하므로, 몬스터 공격 성공 시 player HP에 피해를 반영해라.

반드시 아래 JSON 형식으로만 응답해. JSON 외 다른 텍스트나 마크다운 코드블록은 절대 출력하지 마.
{
  "narration": "상황 묘사",
  "dice_roll": {
    "stat": "사용된 능력치",
    "difficulty": 난이도 숫자,
    "roll": 주사위 숫자,
    "bonus": 보정치 숫자,
    "total": 합계 숫자,
    "result": "성공 또는 실패"
  },
  "outcome": "행동 결과 묘사",
  "hp_changes": {
    "player": 0, "goren": 0, "sera": 0,
    "monster_101": 0, "monster_102": 0
  },
  "relationship_update": null,
  "npc_reaction": "NPC의 반응 대사"
}"""

# ── 게임 상태 ──────────────────────────────────────────────
game_state = {
    "player": {
        "hp": 100, "maxHp": 100,
        "inventory": ["포션", "플래시 포더", "응급 키트"],
        "relationship": {"고렌": {"친분": 0}, "세라": {"친분": 0}}
    },
    "npcs": {
        "고렌": {"hp": 100, "maxHp": 100},
        "세라": {"hp": 100, "maxHp": 100}
    },
    "monsters": {
        "monster_101": {"name": "던전 슬라임", "hp": 20, "maxHp": 20, "alive": True},
        "monster_102": {"name": "던전 박쥐",   "hp": 15, "maxHp": 15, "alive": True},
    },
    "history": []
}

def build_context(action):
    alive = "\n".join(
        f"- {m['name']}({mid}): HP {m['hp']}/{m['maxHp']}"
        for mid, m in game_state["monsters"].items() if m["alive"]
    ) or "없음"
    p = game_state["player"]
    n = game_state["npcs"]
    return (
        f"[현재 상태]\n"
        f"카빌: HP {p['hp']}/{p['maxHp']}, 무기:도검(물리+2 회피+2), 위치:2, 통찰보정:+5\n"
        f"인벤토리: {', '.join(p['inventory']) or '없음'}\n"
        f"고렌: HP {n['고렌']['hp']}/{n['고렌']['maxHp']}, 도끼, 근력+3, 위치:1, 친분:{p['relationship']['고렌']['친분']}\n"
        f"세라: HP {n['세라']['hp']}/{n['세라']['maxHp']}, 활, 민첩+3 통찰+2, 위치:3, 친분:{p['relationship']['세라']['친분']}\n"
        f"살아있는 적:\n{alive}\n\n[플레이어 행동] {action}"
    )

def apply_changes(parsed):
    hc = parsed.get("hp_changes", {})
    p  = game_state["player"]
    n  = game_state["npcs"]
    if hc.get("player"):
        p["hp"] = max(0, min(p["maxHp"], p["hp"] + hc["player"]))
    if hc.get("goren"):
        n["고렌"]["hp"] = max(0, min(n["고렌"]["maxHp"], n["고렌"]["hp"] + hc["goren"]))
    if hc.get("sera"):
        n["세라"]["hp"] = max(0, min(n["세라"]["maxHp"], n["세라"]["hp"] + hc["sera"]))
    for mid in ["monster_101", "monster_102"]:
        dmg = hc.get(mid, 0)
        if dmg < 0:
            m = game_state["monsters"][mid]
            m["hp"] = max(0, m["hp"] + dmg)
            if m["hp"] <= 0:
                m["alive"] = False
    rel = parsed.get("relationship_update")
    if rel and rel.get("npc") in p["relationship"]:
        npc = rel["npc"]
        if rel.get("type") == "은혜":
            p["relationship"][npc]["친분"] = min(10, p["relationship"][npc]["친분"] + 1)
        elif rel.get("type") == "원한":
            p["relationship"][npc]["친분"] = max(-5, p["relationship"][npc]["친분"] - 1)

# ── API 스레드 ─────────────────────────────────────────────
class ApiThread(QThread):
    result = pyqtSignal(dict, str)
    error  = pyqtSignal(str)

    def __init__(self, action):
        super().__init__()
        self.action = action

    def run(self):
        ctx = build_context(self.action)
        game_state["history"].append({"role": "user", "content": ctx})
        try:
            resp = requests.post(API_URL, headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01"
            }, json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1000,
                "system": SYSTEM_PROMPT,
                "messages": game_state["history"]
            }, timeout=30)
            raw = "".join(c.get("text", "") for c in resp.json().get("content", []))
            parsed = json.loads(raw.replace("```json", "").replace("```", "").strip())
            game_state["history"].append({"role": "assistant", "content": raw})
            self.result.emit(parsed, self.action)
        except Exception as e:
            game_state["history"].pop()
            self.error.emit(str(e))

# ── 헬퍼 ──────────────────────────────────────────────────
def hline():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{BORDER}; background:{BORDER};")
    f.setFixedHeight(1)
    return f

def make_hp_bar(value, maximum, color=RED):
    bar = QProgressBar()
    bar.setRange(0, maximum)
    bar.setValue(value)
    bar.setTextVisible(False)
    bar.setFixedHeight(5)
    bar.setStyleSheet(f"QProgressBar{{background:{BORDER};border:none;}} QProgressBar::chunk{{background:{color};}}")
    return bar

# ── 사이드바 ───────────────────────────────────────────────
class SidePanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(205)
        self.setStyleSheet(f"background:{BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._player_card())
        layout.addWidget(self._npc_card("고렌", "베테랑 용병 / 근력+3", "goren"))
        layout.addWidget(self._npc_card("세라", "레인저 / 민첩+3 통찰+2", "sera"))
        layout.addWidget(self._inv_card())
        layout.addWidget(self._monster_card())
        layout.addStretch()

    def _panel(self, title_text):
        w = QWidget()
        w.setStyleSheet(f"background:{BG2}; border:1px solid {BORDER};")
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 8, 10, 10)
        v.setSpacing(3)
        t = QLabel(title_text.upper())
        t.setStyleSheet(f"color:{GOLD2}; font-size:9px; letter-spacing:2px; border:none; background:transparent;")
        v.addWidget(t)
        v.addWidget(hline())
        return w, v

    def _lbl(self, text, color=TEXT, size=11, bold=False):
        l = QLabel(text)
        l.setStyleSheet(f"color:{color}; font-size:{size}px; {'font-weight:bold;' if bold else ''} background:transparent; border:none;")
        l.setWordWrap(True)
        return l

    def _player_card(self):
        w, v = self._panel("플레이어")
        v.addWidget(self._lbl("카빌", BRIGHT, 14, True))
        v.addWidget(self._lbl("도검 / 통찰 특화", DIM, 10))
        self.player_hp_bar = make_hp_bar(100, 100)
        self.player_hp_lbl = self._lbl("HP  100 / 100", DIM, 10)
        v.addWidget(self.player_hp_lbl)
        v.addWidget(self.player_hp_bar)
        # 스탯 그리드
        grid = QHBoxLayout()
        grid.setSpacing(2)
        self._stat_vals = {}
        for stat, val, hi in [("체력","0",False),("근력","0",False),("민첩","0",False),
                               ("신앙","0",False),("지능","0",False),("통찰","5",True)]:
            col = QVBoxLayout()
            col.setSpacing(1)
            sl = QLabel(stat)
            sl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sl.setStyleSheet(f"color:{DIM}; font-size:8px; background:{BG3}; border:1px solid {BORDER}; padding:1px;")
            vl = QLabel(val)
            vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl.setStyleSheet(f"color:{GOLD if hi else BRIGHT}; font-size:12px; background:{BG3}; border:1px solid {BORDER}; padding:1px;")
            col.addWidget(sl); col.addWidget(vl)
            grid.addLayout(col)
        v.addLayout(grid)
        v.addWidget(self._lbl("⚔ 도검  ✦ 선제대응", DIM, 10))
        return w

    def _npc_card(self, name, role, key):
        w, v = self._panel(f"동료 — {name}")
        v.addWidget(self._lbl(name, BRIGHT, 13, True))
        v.addWidget(self._lbl(role, DIM, 10))
        bar = make_hp_bar(100, 100)
        lbl = self._lbl(f"HP  100 / 100", DIM, 10)
        setattr(self, f"{key}_hp_bar", bar)
        setattr(self, f"{key}_hp_lbl", lbl)
        v.addWidget(lbl); v.addWidget(bar)
        v.addWidget(self._lbl("친분", DIM, 10))
        dot_row = QHBoxLayout()
        dot_row.setSpacing(3)
        dots = []
        for _ in range(5):
            d = QLabel("●")
            d.setStyleSheet(f"color:{BORDER}; font-size:10px; background:transparent; border:none;")
            dot_row.addWidget(d)
            dots.append(d)
        dot_row.addStretch()
        setattr(self, f"{key}_dots", dots)
        v.addLayout(dot_row)
        return w

    def _inv_card(self):
        w, v = self._panel("인벤토리")
        self._inv_v = v
        self._inv_w = w
        self._draw_inv()
        return w

    def _draw_inv(self):
        # 타이틀+구분선(인덱스 0,1) 이후 제거
        while self._inv_v.count() > 2:
            item = self._inv_v.takeAt(2)
            if item.widget():
                item.widget().deleteLater()
        items = game_state["player"]["inventory"]
        for it in items:
            self._inv_v.addWidget(self._lbl(f"◆  {it}", DIM, 11))
        if not items:
            self._inv_v.addWidget(self._lbl("없음", DIM, 11))

    def _monster_card(self):
        w, v = self._panel("현재 적")
        self.m101_lbl = self._lbl("슬라임  HP 20/20", DIM, 10)
        self.m101_bar = make_hp_bar(20, 20, "#8b0000")
        self.m102_lbl = self._lbl("박쥐  HP 15/15", DIM, 10)
        self.m102_bar = make_hp_bar(15, 15, "#8b0000")
        v.addWidget(self._lbl("던전 슬라임", BRIGHT, 11))
        v.addWidget(self.m101_lbl); v.addWidget(self.m101_bar)
        v.addWidget(self._lbl("던전 박쥐", BRIGHT, 11))
        v.addWidget(self.m102_lbl); v.addWidget(self.m102_bar)
        return w

    def refresh(self):
        p  = game_state["player"]
        n  = game_state["npcs"]
        m1 = game_state["monsters"]["monster_101"]
        m2 = game_state["monsters"]["monster_102"]

        self.player_hp_bar.setValue(p["hp"])
        self.player_hp_lbl.setText(f"HP  {p['hp']} / {p['maxHp']}")

        self.goren_hp_bar.setValue(n["고렌"]["hp"])
        self.goren_hp_lbl.setText(f"HP  {n['고렌']['hp']} / {n['고렌']['maxHp']}")
        self.sera_hp_bar.setValue(n["세라"]["hp"])
        self.sera_hp_lbl.setText(f"HP  {n['세라']['hp']} / {n['세라']['maxHp']}")

        for key, npc in [("goren","고렌"), ("sera","세라")]:
            친분 = max(0, min(5, p["relationship"][npc]["친분"]))
            for i, d in enumerate(getattr(self, f"{key}_dots")):
                d.setStyleSheet(f"color:{GOLD if i < 친분 else BORDER}; font-size:10px; background:transparent; border:none;")

        dead1 = "" if m1["alive"] else "  [사망]"
        dead2 = "" if m2["alive"] else "  [사망]"
        self.m101_bar.setValue(m1["hp"])
        self.m101_lbl.setText(f"슬라임  HP {m1['hp']}/{m1['maxHp']}{dead1}")
        self.m102_bar.setValue(m2["hp"])
        self.m102_lbl.setText(f"박쥐  HP {m2['hp']}/{m2['maxHp']}{dead2}")

        self._draw_inv()

# ── 메인 윈도우 ───────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("미궁의 수호자 — Dungeon RPG")
        self.resize(920, 700)
        self.setStyleSheet(f"background:{BG}; color:{TEXT};")
        self.api_thread = None

        root = QWidget()
        rl = QVBoxLayout(root)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(8)
        self.setCentralWidget(root)

        # 헤더
        title = QLabel("미궁의 수호자")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color:{GOLD}; font-size:20px; font-weight:bold; letter-spacing:6px; background:transparent;")
        sub = QLabel("던전 1층  |  Dungeon Text RPG")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color:{DIM}; font-size:10px; letter-spacing:3px; background:transparent;")
        rl.addWidget(title)
        rl.addWidget(sub)
        rl.addWidget(hline())

        # 본문
        body = QHBoxLayout()
        body.setSpacing(10)

        # 사이드바 스크롤
        self.side = SidePanel()
        scroll = QScrollArea()
        scroll.setWidget(self.side)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(222)
        scroll.setStyleSheet(f"background:{BG}; border:none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body.addWidget(scroll)

        # 우측
        right = QVBoxLayout()
        right.setSpacing(8)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet(f"""
            QTextEdit {{
                background:{BG2}; color:{TEXT};
                border:1px solid {BORDER};
                font-size:13px; padding:10px;
            }}
        """)
        right.addWidget(self.log, stretch=1)

        # 입력행
        irow = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("행동을 입력하세요... (Enter로 전송)")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background:{BG}; color:{BRIGHT};
                border:1px solid {BORDER};
                padding:8px 10px; font-size:13px;
            }}
            QLineEdit:focus {{ border:1px solid {GOLD2}; }}
        """)
        self.input.returnPressed.connect(self.submit)
        self.btn = QPushButton("행동 ▶")
        self.btn.setFixedWidth(90)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; color:{GOLD};
                border:1px solid {GOLD2};
                padding:8px; font-size:13px;
            }}
            QPushButton:hover {{ background:{GOLD2}; color:{BG}; }}
            QPushButton:disabled {{ color:{DIM}; border-color:{BORDER}; }}
        """)
        self.btn.clicked.connect(self.submit)
        irow.addWidget(self.input)
        irow.addWidget(self.btn)
        right.addLayout(irow)

        # 퀵버튼
        qrow = QHBoxLayout()
        qrow.setSpacing(5)
        for label_text, action in [
            ("⚔ 슬라임", "슬라임을 도검으로 공격한다"),
            ("⚔ 박쥐",   "박쥐를 도검으로 베어낸다"),
            ("🧪 포션",   "포션을 마셔 HP를 회복한다"),
            ("👁 분석",   "통찰로 적의 패턴을 읽는다"),
            ("🤝 고렌",   "고렌에게 협공을 지시한다"),
            ("🏹 세라",   "세라에게 원거리 지원을 요청한다"),
        ]:
            b = QPushButton(label_text)
            b.setStyleSheet(f"""
                QPushButton {{
                    background:transparent; color:{DIM};
                    border:1px solid {BORDER};
                    padding:5px 8px; font-size:11px;
                }}
                QPushButton:hover {{ border-color:{GOLD2}; color:{GOLD}; }}
            """)
            b.clicked.connect(lambda _, a=action: self.quick(a))
            qrow.addWidget(b)
        right.addLayout(qrow)

        body.addLayout(right)
        rl.addLayout(body)

        # 오프닝 텍스트
        self.append_log(
            f'<span style="color:{GOLD}; font-size:14px;"><b>던전 1층.</b></span> '
            f'차갑고 습한 공기가 폐를 채운다. 횃불 하나가 통로를 가늘게 밝히고 있다.<br><br>'
            f'<b style="color:{BRIGHT};">던전 슬라임</b>이 통로 끝에서 모습을 드러낸다. '
            f'천장 균열 사이로 <b style="color:{BRIGHT};">던전 박쥐</b>가 날카로운 눈을 번뜩인다.<br><br>'
            f'<span style="color:{GOLD2};">고렌 ▸</span> '
            f'<i style="color:{DIM};">슬라임은 내가 맡는다. 박쥐 — 네가 신경 써.</i><br>'
            f'<span style="color:{GOLD2};">세라 ▸</span> '
            f'<i style="color:{DIM};">카빌, 박쥐 첫 번에 잡아야 해요. 기습 당하면 골치 아파요.</i>'
        )

    def append_log(self, html):
        self.log.append(html)
        self.log.append(f"<hr style='border:none; border-top:1px solid {BORDER};'>")
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def quick(self, action):
        self.input.setText(action)
        self.submit()

    def submit(self):
        action = self.input.text().strip()
        if not action or self.api_thread:
            return
        self.input.clear()
        self.btn.setEnabled(False)
        self.log.append(f'<span style="color:{DIM}; font-style:italic;">▸ {action}</span><br>')

        self.api_thread = ApiThread(action)
        self.api_thread.result.connect(self.on_result)
        self.api_thread.error.connect(self.on_error)
        self.api_thread.finished.connect(self.on_done)
        self.api_thread.start()

    def on_result(self, parsed, action):
        apply_changes(parsed)
        self.side.refresh()

        dr     = parsed.get("dice_roll", {})
        roll   = dr.get("roll", 0)
        bonus  = dr.get("bonus", 0)
        total  = dr.get("total", 0)
        diff   = dr.get("difficulty", 0)
        stat   = dr.get("stat", "")
        result = dr.get("result", "")
        nat20  = (roll == 20 and bonus == 0)
        nat1   = (roll == 1  and bonus == 0)

        roll_color = GOLD if nat20 else (RED if nat1 else BRIGHT)
        res_color  = GREEN if result == "성공" else RED
        special    = (f' <b style="color:{GOLD};">✦ 완벽한 성공</b>' if nat20
                      else f' <b style="color:{RED};">✦ 치명적 실수</b>' if nat1 else "")

        html = (
            f'<span style="color:{BRIGHT};">{parsed.get("narration","")}</span><br><br>'
            f'<span style="color:{DIM}; background:{BG3};">'
            f'  D20: <b style="color:{roll_color}; font-size:15px;">{roll}</b>&nbsp;&nbsp;'
            f'[{stat}] +{bonus} = <b style="color:{BRIGHT};">{total}</b>&nbsp;&nbsp;'
            f'난이도 {diff}&nbsp;&nbsp;'
            f'<b style="color:{res_color};">{result}</b>{special}'
            f'</span><br><br>'
            f'<span style="color:{TEXT};">{parsed.get("outcome","")}</span><br>'
        )
        if parsed.get("npc_reaction"):
            html += (f'<br><span style="color:{GOLD2};">NPC ▸</span> '
                     f'<i style="color:{DIM};">{parsed["npc_reaction"]}</i><br>')
        rel = parsed.get("relationship_update")
        if rel:
            html += (f'<br><span style="color:{GOLD2};">◆ {rel["npc"]}와의 관계 — '
                     f'{rel["type"]}: {rel["reason"]}</span><br>')

        self.append_log(html)

    def on_error(self, msg):
        self.append_log(f'<span style="color:{RED};">⚠ 오류: {msg}</span>')

    def on_done(self):
        self.btn.setEnabled(True)
        self.api_thread = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("맑은 고딕", 10))
    win = MainWindow()
    win.resize(1280, 720)
    win.show()
    sys.exit(app.exec())