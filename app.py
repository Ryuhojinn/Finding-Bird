"""Finding Bird! Local two-round bird guessing game. Python 3.10+."""
import json
import os
import random
import re
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent
ROOT = BASE / "CUB_200_2011"
from clues import particle, PATTERN_SOURCES, overall_pattern, WATER_CLUE, CASUAL_QUESTIONS, ROWS, PARTS, normalize, bill_choice, GROUPS, QUESTIONS, TRAITS, spoken_answer, interpret, species_facts
VISUAL_GROUPS = ("primary_color", "wing_color", "breast_color", "belly_color",
                 "head_pattern", "bill_shape", "back_color", "wing_pattern")
VISUAL_PART = {k: group.split("_")[0] for group in VISUAL_GROUPS for k in GROUPS[group]}
PHOTO_SCORES = {}
QUESTION_COUNT = len(QUESTIONS)
NAMES = []
GUIDE = []
REFERENCE_POOL = []
REFERENCE_PATHS = {}
POOL = []
PHOTOS = {}
EVIDENCE = {}
PROFILES = []
GAMES = {}
from setup_cub import prepare

def table(file):
    return dict(line.split(maxsplit=1) for line in (ROOT/file).read_text().splitlines() if line.strip())

def load():
    classes, labels, paths, splits = map(table, ["classes.txt","image_class_labels.txt","images.txt","train_test_split.txt"])
    for i in range(1,len(classes)+1):
        NAMES.append(classes[str(i)].split(".",1)[-1].replace("_"," "))
        GUIDE.append(None)
        REFERENCE_POOL.append([])
        POOL.append([])
    counts = [[[1,2] for _ in range(QUESTION_COUNT)] for _ in NAMES]
    for img, label in labels.items():
        i = int(label)-1
        PHOTOS[img] = ROOT/"images"/paths[img]
        EVIDENCE[img] = [-1]*QUESTION_COUNT
        if splits[img]=="1":
            REFERENCE_POOL[i].append(img)
            REFERENCE_PATHS[img] = PHOTOS[img]
            if GUIDE[i] is None: GUIDE[i] = f"/guide/{i}"
        else: POOL[i].append(img)
    size_ids = {218, 219, 220, 221, 222}
    size_votes = {}
    with (ROOT/"attributes/image_attribute_labels.txt").open() as f:
        for line in f:
            img, attr, present, certainty, *_ = line.split()
            attr_id = int(attr)
            if attr_id in size_ids and present == "1" and int(certainty) >= 3:
                size_votes.setdefault(img, set()).add(attr_id)
            k = attr_id - 1
            if not 0 <= k < 312 or int(certainty)<3: continue
            val = int(present)
            EVIDENCE[img][k] = val
            if splits[img]=="1":
                pair = counts[int(labels[img])-1][k]
                pair[0] += val
                pair[1] += 1
    for img, sizes in size_votes.items():
        for k, group in zip(GROUPS["broad_size"], [(218,220), (219,222)]):
            answers = {size in group for size in sizes}
            if len(answers) != 1:
                continue
            val = int(answers.pop())
            EVIDENCE[img][k] = val
            if splits[img] == "1":
                pair = counts[int(labels[img])-1][k]
                pair[0] += val
                pair[1] += 1
    for img, row in EVIDENCE.items():
        for k, sources in PATTERN_SOURCES.items():
            row[k] = overall_pattern(row, sources)
            if row[k] >= 0 and splits[img] == "1":
                pair = counts[int(labels[img])-1][k]
                pair[0] += row[k]
                pair[1] += 1
    PROFILES.extend([[a/b for a,b in row] for row in counts])
    for img, species in labels.items():
        values = species_facts(NAMES[int(species)-1])
        for k, value in zip(GROUPS["species_fact"], values):
            EVIDENCE[img][k] = value
            PROFILES[int(species)-1][k] = {1:.98, 0:.02, -1:.5}[value]
    for i in range(len(NAMES)):
        img = next(j for j in labels if int(labels[j])==i+1 and splits[j]=="1")
        PHOTOS[f"guide{i}"] = PHOTOS[img]

def photo_score(photo):
    if photo not in PHOTO_SCORES:
        row = EVIDENCE[photo]
        PHOTO_SCORES[photo] = sum(any(row[k] == 1 for k in GROUPS[group])
                                 for group in VISUAL_GROUPS)
    return PHOTO_SCORES[photo]


def start(g, stage):
    candidates = [(i,[x for x in POOL[i] if x not in g["used"]]) for i in g["birds"]]
    choices = [(i,pool) for i,pool in candidates if pool]
    if not choices:
        g["used"].clear()
        choices = [(i, POOL[i]) for i in g["birds"]]
    i,pool = random.choice(choices)
    pool = sorted(pool, key=photo_score, reverse=True)
    pic = random.choice(pool[:max(1, (len(pool)+1)//2)])
    g["used"].add(pic)
    g.update(stage=stage,target=i,pic=pic,count=0,logs=[],prev=None,asked=set(),wrong=set(),
             hidden_parts=set(), clues={}, mixed=set(), remaining=g["birds"][:], weights=[1/len(g["birds"])]*len(g["birds"]),pending=None,ended=False,won=False)
    if stage==2: ai_turn(g)

def log(g,who,msg): g["logs"].append([who,msg])

def finish(g, won):
    g.update(ended=True,won=won)
    g["scores"][g["stage"]-1] = g["count"] if won else 21
    log(g,"결과",f"정답은 {NAMES[g['target']]}입니다. · {g['count']}회 사용")

def guess_cost(masses, turns):
    """Expected match score contribution, weighted by this answer's probability."""
    spent = 20 - turns
    return sum(mass * min(spent + rank, 21)
               for rank, mass in enumerate(sorted(masses, reverse=True), 1))


def next_clue(g, active):
    turns = 20 - g["count"]
    if len(active) <= 2 or turns <= 1:
        return None

    weights = [g["weights"][i] for i in active]
    profiles = [PROFILES[g["birds"][i]] for i in active]
    # Compare guessing in probability order with asking once, then guessing.
    best_cost = guess_cost(weights, turns)
    best_question = None
    for k, part in VISUAL_PART.items():
        if k in g["asked"] or part in g["hidden_parts"]:
            continue
        yes = [w * row[k] for w, row in zip(weights, profiles)]
        no = [w - y for w, y in zip(weights, yes)]
        cost = guess_cost(yes, turns - 1) + guess_cost(no, turns - 1)
        if cost < best_cost - 1e-9:
            best_question, best_cost = k, cost
    return best_question


def ai_turn(g):
    while not g["ended"]:
        active = [i for i in range(len(g["birds"])) if i not in g["wrong"]]
        k = next_clue(g, active)
        g["count"] += 1
        g["pending"] = k
        if k is not None:
            g["asked"].add(k)
            log(g, "삐오", CASUAL_QUESTIONS[k])
            return

        weights = g["weights"]
        best = max(active, key=weights.__getitem__)
        species = g["birds"][best]
        log(g, "삐오", f"내가 고른 새는… {NAMES[species]}!")
        if species == g["target"] or g["count"] == 20:
            finish(g, species == g["target"])
            return
        g["wrong"].add(best)
        weights[best] = 0
        total = sum(weights)
        g["weights"] = [w / total for w in weights]

def filter_guide(g, clue, value):
    if value < 0 or clue in g["clues"]:
        return
    g["clues"][clue] = value
    # A single possible puzzle photo must support all observed answers.
    g["remaining"] = [
        species for species in g["remaining"]
        if any(all(EVIDENCE[photo][k] == v for k, v in g["clues"].items())
               for photo in POOL[species])
    ]


def stated_colors(text, group):
    # Accept a bare colour or a short declaration about the requested body part.
    part = group.removesuffix("_color")
    text = normalize(text)
    text = re.sub(r"^(?:네|응|아니요|아니)", "", text)
    for prefix in PARTS[part].split("|"):
        if text.startswith(prefix):
            text = re.sub(r"^(?:의)?(?:색깔|색)?(?:이|가|은|는)?", "", text[len(prefix):])
            break
    mentions = []
    for segment in re.split(r"하고|이랑|랑|와|과|,", text):
        for k in GROUPS[group]:
            if any(re.fullmatch(re.escape(alias) + r"(?:색)?(?:이야|입니다|이에요|이다|이네|이라고|이래|야)?", segment)
                   for alias in ROWS[k][1]):
                mentions.append(k)
                break
        else:
            return []
    return list(dict.fromkeys(mentions))


def message(g, raw):
    msg=raw.strip()
    if not msg or g["ended"]: return
    if g["stage"]==2:
        k=g["pending"]
        group=ROWS[k][0]
        colors = stated_colors(msg, group) if group.endswith("_color") else []
        if colors: val = k in colors
        elif re.search(r"모르|안\s*보|몰라|가려|애매|보이지\s*않|확인.{0,4}(어렵|불가)|잘못보겠",msg): val=None
        elif re.match("아니|아닙|아냐|없|ㄴ|아닌|그렇지 않",msg): val=False
        elif re.match("예|네|응|어|맞|보여|있|ㅇ|그래|그렇습니다",msg): val=True
        else:
            log(g,"안내","“그렇습니다”, “아닙니다”, “잘 모르겠습니다” 중 어느 쪽입니까?"); return
        log(g,"나",msg)
        if colors or (val and group.endswith("_color")):
            g["asked"].update(GROUPS[group])
        evidence = [(k, val)] if not colors else [(j, True) for j in colors]
        for k, val in evidence:
            if val is None:
                continue
            ws=[w*(PROFILES[i][k] if val else 1-PROFILES[i][k]) for w,i in zip(g["weights"],g["birds"])]
            g["weights"]=[w/sum(ws) for w in ws]
        if val is None:
            g["count"]-=1
            g["hidden_parts"].add(VISUAL_PART[k])
        ai_turn(g); return
    log(g,"나",msg)
    species = next((i for i,n in enumerate(NAMES) if msg.casefold() in (n.casefold(),f"정답 {n}".casefold())),None)
    if species is not None:
        if species not in g["birds"]:
            log(g,"삐오","이번 도감에는 없는 새야. 도감에 있는 친구 중에서 골라 볼까?")
            return
        g["count"]+=1
        if species==g["target"] or g["count"]==20: finish(g,species==g["target"])
        else:
            if species in g["remaining"]:
                g["remaining"].remove(species)
            log(g,"삐오","아쉽다, 내가 고른 새는 다른 친구야!")
        return
    if bill_choice(msg):
        known = [j for j in GROUPS["bill_length"] if EVIDENCE[g["pic"]][j] == 1]
        if len(known) != 1:
            log(g, "삐오", "부리 길이는 잘 모르겠어. 이번 질문은 횟수에서 빼 줄게!")
            return
        k = known[0]
    else:
        k = interpret(msg, g["prev"])
    if k is None:
        log(g,"삐오","앗, 그 질문은 잘 이해하지 못했어. 단서 사전에서 궁금한 부위를 찾아볼까? 이번 질문은 횟수에서 빼 줄게!")
        return
    g["prev"] = k
    if EVIDENCE[g["pic"]][k] < 0:
        reply = "음, 그 특징은 사진에서 잘 안 보여. 이번 질문은 횟수에서 빼 줄게!"
        if k == WATER_CLUE:
            reply = "이 친구는 도감에 물가 생활 정보가 없어. 이번 질문은 횟수에서 빼 줄게!"
        # Suggest an answerable question without displaying its answer.
        options = [j for j in VISUAL_PART if j not in g["clues"] and EVIDENCE[g["pic"]][j] >= 0]
        if options:
            def split_score(j):
                probs = [PROFILES[i][j] for i in g["remaining"]]
                return max(probs) - min(probs)
            suggestion = max(options, key=split_score)
            reply += f" 이렇게 물어보면 어때? “{CASUAL_QUESTIONS[suggestion]}”"
        log(g,"삐오",reply)
        return
    g["count"]+=1
    value=EVIDENCE[g["pic"]][k]
    filter_guide(g, k, value)
    reply = spoken_answer(k, value)
    group = ROWS[k][0]
    if group == "bill_length" and not value:
        lengths = [j for j in GROUPS[group] if EVIDENCE[g["pic"]][j] == 1]
        if len(lengths) == 1:
            reply = "아니야. " + CASUAL_QUESTIONS[lengths[0]].removesuffix("?") + "."
            filter_guide(g, lengths[0], 1)
    if group.endswith("_color"):
        colors = [j for j in GROUPS[group] if EVIDENCE[g["pic"]][j] == 1
                  and ROWS[j][1][0] != "금속광택"]
        feature = ROWS[k][1][0]
        if not value and feature != "금속광택":
            label = "검정색" if feature == "검은색" else feature
            reply = f"아니, {particle(label, '은', '는')} 없어."
        elif value and k in colors and len(colors) >= 2:
            g["mixed"].add(group)
            reply = "응! 다른 색이랑 섞여 있어."
    log(g,"삐오",reply)
    if g["count"]==20: finish(g,False)

def reference_rank(photo, clues):
    row = EVIDENCE[photo]
    matches = sum(row[k] == v for k, v in clues)
    conflicts = sum(row[k] >= 0 and row[k] != v for k, v in clues)
    return matches, -conflicts


def reference_info(photo, clues):
    row = EVIDENCE[photo]
    return dict(image=f"/reference/{photo}", stripe=row[GROUPS["overall_pattern"][0]],
                complete=all(row[k] == v for k, v in clues))


def reference_cards(g):
    cards = {}
    clues = tuple(g["clues"].items())
    for species in g["remaining"]:
        pool = REFERENCE_POOL[species]
        photo = max(pool, key=lambda p: reference_rank(p, clues)) if clues else pool[0]
        cards[species] = reference_info(photo, clues)
    return cards


def public_notes(g):
    notes = []
    for k, value in g["clues"].items():
        group, aliases, question = ROWS[k]
        if group == "overall_pattern":
            notes.append(aliases[0] + (" 있음" if value else " 없음"))
        else:
            notes.append(question + (" 예" if value else " 아니오"))
        if group in g["mixed"]:
            part = PARTS[group.removesuffix("_color")].split("|")[0]
            note = part + "에 여러 색이 섞임"
            if note not in notes:
                notes.append(note)
    return notes


def state(g):
    return dict(references=reference_cards(g), publicNotes=public_notes(g), birds=g["birds"],remaining=g["remaining"],stage=g["stage"],count=g["count"],logs=g["logs"],ended=g["ended"],scores=g["scores"],
        notes=[f"{QUESTIONS[k]} → {('아니요','예')[v] if v >= 0 else '기록 없음'}"
               for k,v in zip(GROUPS["species_fact"],species_facts(NAMES[g["target"]]))] if g["stage"]==2 else [],
        photo=f"/secret/{g['id']}/{g['stage']}" if g["stage"]==2 or g["ended"] else None)

class Handler(BaseHTTPRequestHandler):
    def send(self, data, mime):
        self.send_response(200)
        self.send_header("Content-Type",mime)
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=="/catalog":
            traits = []
            for i, row in enumerate(PROFILES):
                ranked = sorted((k for k in range(312) if row[k] >= .65), key=row.__getitem__, reverse=True)
                traits.append([TRAITS[k] for k in ranked[:6]])
            data={"names":NAMES,"images":GUIDE,"questions":QUESTIONS,"traits":traits}
            return self.send(json.dumps(data).encode(),"application/json")
        if path in ("/","/ui.js","/style.css"):
            name,mime={"/":("index.html","text/html; charset=utf-8"),"/ui.js":("ui.js","application/javascript"),"/style.css":("style.css","text/css")}[path]
            return self.send((BASE/"static"/name).read_bytes(),mime)
        gallery = re.fullmatch(r"/gallery/([a-f0-9]{32})/(\d{1,3})", path)
        if gallery:
            g = GAMES.get(gallery[1])
            species = int(gallery[2])
            if not g or species not in g["remaining"]:
                return self.send_error(404)
            clues = tuple(g["clues"].items())
            photos = sorted(REFERENCE_POOL[species], key=lambda p: reference_rank(p, clues), reverse=True)
            return self.send(json.dumps([reference_info(p, clues) for p in photos]).encode(), "application/json")
        if re.fullmatch(r"/reference/\d+",path):
            photo = REFERENCE_PATHS.get(path.split("/")[-1])
            if photo: return self.send(photo.read_bytes(),"image/jpeg")
        if re.fullmatch(r"/guide/\d+",path):
            photo=PHOTOS.get("guide"+path.split("/")[-1])
            if photo: return self.send(photo.read_bytes(),"image/jpeg")
        m=re.fullmatch(r"/secret/([a-f0-9]+)/([12])",path)
        if m and (g:=GAMES.get(m[1])) and int(m[2])==g["stage"] and (g["ended"] or g["stage"]==2):
            photo=PHOTOS[g["pic"]]
            return self.send(photo.read_bytes(),"image/jpeg")
        if re.fullmatch(r"/art/[0-5]",path):
            return self.send((BASE/"static"/("bird"+path[-1]+".png")).read_bytes(),"image/png")
        self.send_error(404)
    def do_POST(self):
        if self.path!="/action": return self.send_error(404)
        try:
            data=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if data["op"]=="start":
                count = data.get("size", 10)
                if type(count) is not int or not 2 <= count <= len(NAMES):
                    return self.send_error(400)
                birds = sorted(random.sample(range(len(NAMES)), count))
                token=uuid.uuid4().hex
                g=GAMES[token]={"id":token,"birds":birds,"used":set(),"scores":[None,None]}
                start(g,1)
            else:
                g=GAMES[data["id"]]
                if data["op"]=="message": message(g,data["text"][:256])
                elif data["op"]=="next" and g["ended"]:
                    if g["stage"]==2: g["scores"]=[None,None]
                    start(g,3-g["stage"])
            self.send(json.dumps(dict(id=g["id"],**state(g))).encode(),"application/json")
        except (ValueError,KeyError,TypeError): self.send_error(400)

if __name__=="__main__":
    prepare()
    load()
    with ThreadingHTTPServer(("127.0.0.1",0),Handler) as server:
        url=f"http://127.0.0.1:{server.server_port}"
        print("Finding Bird!  "+url,flush=True)
        if not os.environ.get("BIRD_HEADLESS"): threading.Timer(.4,webbrowser.open,args=[url]).start()
        server.serve_forever()
