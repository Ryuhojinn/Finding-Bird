"""Simulate Pio's turns with recorded answers from held-out CUB photos."""
import random
from statistics import mean

import app


def measure(size, games):
    scores, skips, guesses, wins, questions = [], [], [], [], []
    for _ in range(games):
        g = dict(birds=random.sample(range(len(app.NAMES)), size),
                 used=set(), scores=[None, None])
        app.start(g, 2)
        unknown = 0
        while not g["ended"]:
            value = app.EVIDENCE[g["pic"]][g["pending"]]
            if value < 0:
                unknown += 1
            app.message(g, {-1: "잘 모르겠어", 0: "아니", 1: "응"}[value])
        questions.append(len(g["asked"]))
        guesses.append(len(g["wrong"]) + 1)
        wins.append(g["won"])
        scores.append(g["count"])
        skips.append(unknown)
    print(f"{size}종 · {games}경기 · 정답률 {mean(wins):.0%} · 평균 질문 {mean(questions):.1f}회"
          f" (확인 불가 {mean(skips):.1f}회 포함) · 평균 추측 {mean(guesses):.1f}회"
          f" · 평균 사용 횟수 {mean(scores):.1f}회")


if __name__ == "__main__":
    app.prepare()
    app.load()
    random.seed(2026)
    for size in (10, 30, 100):
        measure(size, 50)
