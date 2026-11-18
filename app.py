"""Finding Bird! Local two-round bird guessing game. Python 3.10+."""
import json
import math
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
from clues import GROUPS, QUESTIONS, TRAITS, spoken_answer, interpret, species_facts
QUESTION_COUNT = len(QUESTIONS)
NAMES = []
GUIDE = []
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
        POOL.append([])
    counts = [[[1,2] for _ in range(QUESTION_COUNT)] for _ in NAMES]
    for img, label in labels.items():
        i = int(label)-1
        PHOTOS[img] = ROOT/"images"/paths[img]
        EVIDENCE[img] = [-1]*QUESTION_COUNT
        if splits[img]=="1":
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
    PROFILES.extend([[a/b for a,b in row] for row in counts])
    for img, species in labels.items():
        values = species_facts(NAMES[int(species)-1])
        for k, value in zip(GROUPS["species_fact"], values):
            EVIDENCE[img][k] = value
            PROFILES[int(species)-1][k] = {1:.98, 0:.02, -1:.5}[value]
    for i in range(len(NAMES)):
        img = next(j for j in labels if int(labels[j])==i+1 and splits[j]=="1")
        PHOTOS[f"guide{i}"] = PHOTOS[img]

def start(g, stage):
    candidates = [(i,[x for x in pool if x not in g["used"]]) for i,pool in enumerate(POOL)]
    choices = [(i,pool) for i,pool in candidates if pool]
    if not choices:
        g["used"].clear()
        choices = list(enumerate(POOL))
    i,pool = random.choice(choices)
    pic = random.choice(pool)
    g["used"].add(pic)
    g.update(stage=stage,target=i,pic=pic,count=0,logs=[],prev=None,asked=set(),wrong=set(),
             weights=[1/len(NAMES)]*len(NAMES),pending=None,ended=False,won=False)
    if stage==2: ai_turn(g)

def log(g,who,msg): g["logs"].append([who,msg])

def finish(g, won):
    g.update(ended=True,won=won)
    g["scores"][g["stage"]-1] = g["count"] if won else 21
    log(g,"결과",f"정답은 {NAMES[g['target']]}입니다. · {g['count']}회 사용")

def ai_turn(g):
    weights=g["weights"]
    best=max(range(len(weights)),key=weights.__getitem__)
    available=set(range(QUESTION_COUNT))-g["asked"]
    if weights[best]>.80 or len(g["wrong"])+1>=len(weights) or g["count"]>=19 or not available:
        g["count"]+=1
        log(g,"삐오",f"제 추측은 {NAMES[best]}입니다.")
        if best==g["target"] or g["count"]==20:
            finish(g,best==g["target"]); return
        g["wrong"].add(best)
        weights[best]=0
        norm=sum(weights)
        g["weights"]=[w/norm for w in weights]
        return ai_turn(g)
    def entropy(x): return -x*math.log2(x)-(1-x)*math.log2(1-x)
    def gain(k):
        ps=[row[k] for row in PROFILES]
        return entropy(sum(w*p for w,p in zip(weights,ps)))-sum(w*entropy(p) for w,p in zip(weights,ps))
    k=max(sorted(available),key=gain)
    g["asked"].add(k)
    g["pending"]=k
    g["count"]+=1
    log(g,"삐오",QUESTIONS[k])

def message(g, raw):
    msg=raw.strip()
    if not msg or g["ended"]: return
    if g["stage"]==2:
        if re.search("모르|안 보|안보|몰라|가려|애매|보이지 않|확인하기 어렵",msg): val=None
        elif re.match("아니|아닙|아냐|없|ㄴ|아닌|그렇지 않",msg): val=False
        elif re.match("예|네|응|어|맞|보여|있|ㅇ|그래|그렇습니다",msg): val=True
        else:
            log(g,"안내","“그렇습니다”, “아닙니다”, “잘 모르겠습니다” 중 어느 쪽입니까?"); return
        log(g,"나",msg)
        k=g["pending"]
        if val is not None:
            ws=[w*(row[k] if val else 1-row[k]) for w,row in zip(g["weights"],PROFILES)]
            g["weights"]=[w/sum(ws) for w in ws]
        if val is None and k in GROUPS["species_fact"]:
            g["count"]-=1
        ai_turn(g); return
    log(g,"나",msg)
    species = next((i for i,n in enumerate(NAMES) if msg.casefold() in (n.casefold(),f"정답 {n}".casefold())),None)
    if species is not None:
        g["count"]+=1
        if species==g["target"] or g["count"]==20: finish(g,species==g["target"])
        else: log(g,"삐오","다른 새입니다. 도감에서 다른 후보를 살펴볼 수 있습니다.")
        return
    k = interpret(msg, g["prev"])
    if k is None:
        log(g,"삐오","질문의 뜻을 파악하기 어렵습니다. 단서 사전에서 부위나 특징을 검색할 수 있습니다. 이번 질문은 횟수에 포함되지 않습니다.")
        return
    g["prev"] = k
    if k in GROUPS["species_fact"] and EVIDENCE[g["pic"]][k] < 0:
        log(g,"삐오","이 새의 도감에는 해당 정보가 없습니다. 이번 질문은 횟수에 포함되지 않습니다.")
        return
    g["count"]+=1
    value=EVIDENCE[g["pic"]][k]
    log(g,"삐오",spoken_answer(k,value))
    if g["count"]==20: finish(g,False)

def state(g):
    return dict(stage=g["stage"],count=g["count"],logs=g["logs"],ended=g["ended"],scores=g["scores"],
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
                token=uuid.uuid4().hex
                g=GAMES[token]={"id":token,"used":set(),"scores":[None,None]}
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
