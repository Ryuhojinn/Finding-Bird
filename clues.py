"""Korean questions mapped to CUB annotation IDs in dataset order."""
from pathlib import Path
import re

# First alias is the display form. Remaining aliases are conversational stems.
PARTS = {
    'bill':'부리','wing':'날개','breast':'가슴','back':'등','belly':'배|복부',
    'tail':'꼬리','upper_tail':'꼬리윗면|꼬리위|꼬리윗','under_tail':'꼬리아랫면|꼬리아래|꼬리밑',
    'upperparts':'몸윗면|상체|몸위쪽','underparts':'몸아랫면|하체|몸아래쪽',
    'head':'머리','throat':'목앞|목구멍|목','eye':'눈','forehead':'이마',
    'nape':'뒷목|목덜미','leg':'다리','crown':'정수리|머리꼭대기','primary':'몸전체|전체|주된|주로|주색',
}
COLOR = dict(zip(
    'blue brown iridescent purple rufous grey yellow olive green pink orange black white red buff'.split(),
    '파란색|파래|파랗|파란|파랑|파랭|블루|푸른 갈색|갈빛 금속광택|무지갯빛|무지개빛 보라색|보랏|보라 적갈색|붉은갈색 회색|잿빛 노란색|노래|노랗|노랑|노란 올리브색|올리브 초록색|초록|녹색 분홍색|분홍|핑크 주황색|주황|오렌지색 검은색|검은|검정|검어|검다|까매|까만|까맣|까망|검게|블랙 흰색|흰|하얗|하얘|하얀|하양|하얌|화이트 빨간색|빨간|빨개|빨갛|빨강|레드|붉 베이지색|담황색|베이지'.split()))
PATTERN = {'solid':'민무늬|단색|무늬없|무늬가없','spotted':'점무늬|반점|얼룩점|점박|점이','striped':'줄무늬|줄이|줄이있|줄무','multi-colored':'여러색무늬|알록달록|다색'}
SPECIAL = {
'bill_shape': ['아래로굽은|아래로휘','단검형|단검','갈고리형|갈고리','바늘형|바늘','바닷새형갈고리','주걱형|주걱','일반형|다목적','원뿔형|원뿔|고깔','특수형'],
'tail_shape':['갈라진|갈라|두갈래','둥근|둥글|둥그','살짝패인|패인|패였','부채형|부채','뾰족한|뾰족','네모난|네모|각진'],
'head_pattern':['점무늬|점박','뺨선|수염무늬','깃관|볏','가면무늬|가면','독특한무늬|특이한무늬','눈썹선|눈썹','눈테|눈둘레','민무늬|밋밋','눈선|눈을지나는선','줄무늬','모자무늬|모자'],
'bill_length':['머리와비슷|머리만|머리랑비슷','머리보다긴|머리보다길|머리보다더길','머리보다짧'],
'wing_shape':['둥근|둥글|둥그','뾰족한|뾰족','넓은|넓','끝으로갈수록좁은|가늘어지|좁아지','긴|길'],
'size':['대형','소형','초대형|아주큰|매우큰|아주커','중형|중간','초소형|아주작|매우작'],
'shape':['직립형물새|직립물새','습지닭형|뜸부기','긴다리형|다리가길|다리가긴','오리형|오리','올빼미형|올빼미|부엉이','갈매기형|갈매기','벌새형|벌새','비둘기형|비둘기','나무줄기에매달리는형|나무줄기에붙','매형|매처럼','도요새형|도요새','땅새형|지상성닭','제비형|제비','횃대에앉는형|횃대'],
}
# Display strings use complete spoken Korean predicates. Attribute order follows CUB.
SPOKEN = {
    'bill_shape': ['부리가 아래로 휘어 있어','부리가 단검처럼 생겼어','부리가 갈고리 모양이야','부리가 바늘처럼 가늘고 뾰족해','부리 끝이 바닷새의 부리처럼 갈고리 모양으로 굽었어','부리 끝이 주걱처럼 넓적해','부리가 일반적인 모양이야','부리가 원뿔 모양이야','부리 모양이 특이해'],
    'tail_shape': ['꼬리 끝이 두 갈래로 갈라져 있어','꼬리 끝이 둥글어','꼬리 끝 가운데가 살짝 패여 있어','꼬리가 부채처럼 펼쳐진 모양이야','꼬리 끝이 뾰족해','꼬리 끝이 네모나'],
    'head_pattern': ['머리에 점무늬가 있어','뺨을 따라 수염처럼 보이는 선이 있어','머리에 볏처럼 솟은 깃털이 있어','얼굴에 가면 같은 무늬가 있어','머리에 독특한 무늬가 있어','눈 위에 눈썹처럼 보이는 선이 있어','눈 둘레에 고리 모양의 테가 있어','머리에 별다른 무늬가 없어','눈을 가로지르는 선이 있어','머리에 줄무늬가 있어','머리에 모자를 쓴 것 같은 무늬가 있어'],
    'bill_length': ['부리 길이가 머리 길이와 비슷해','부리가 머리보다 길어','부리가 머리보다 짧아'],
    'wing_shape': ['날개 끝이 둥글어','날개 끝이 뾰족해','날개 폭이 넓어','날개가 끝으로 갈수록 좁아져','날개가 길어'],
    'size': ['몸길이가 대형에 속해','몸길이가 소형에 속해','몸길이가 초대형에 속해','몸길이가 중간 크기야','몸길이가 초소형에 속해'],
    'shape': ['물새처럼 몸을 곧추세운 모습이야','체형이 뜸부기를 닮았어','다리가 긴 편이야','체형이 오리를 닮았어','체형이 올빼미를 닮았어','체형이 갈매기를 닮았어','체형이 벌새를 닮았어','체형이 비둘기를 닮았어','나무줄기에 붙는 새와 비슷한 체형이야','체형이 매를 닮았어','체형이 도요새를 닮았어','땅에서 지내는 닭과 비슷한 체형이야','체형이 제비를 닮았어','나뭇가지에 앉는 새와 비슷한 체형이야'],
}
def particle(word, closed, open_):
    """Attach a particle to a display label ending in a Hangul syllable."""
    return word + (closed if (ord(word[-1])-ord('가')) % 28 else open_)

DISPLAY_PARTS = {'upper_tail':'꼬리 윗면','under_tail':'꼬리 아랫면','upperparts':'몸 윗면','underparts':'몸 아랫면','throat':'목 앞쪽','primary':'몸 전체'}
ROWS = []
GROUPS = {}
NEGATIVE = []
TRAITS = []
# Each authored predicate has a formal statement ending. Questions share its stem.
FORMAL_ENDINGS = {
    '아니야':'아닙니다', '이야':'입니다', '크기야':'크기입니다',
    '있어':'있습니다', '없어':'없습니다', '같아':'같습니다',
    '생겼어':'생겼습니다', '굽었어':'굽었습니다', '닮았어':'닮았습니다',
    '둥글어':'둥급니다', '네모나':'네모납니다', '길어':'깁니다',
    '짧아':'짧습니다', '넓어':'넓습니다', '좁아져':'좁아집니다',
    '해':'합니다', '광택이 나':'광택이 납니다',
}

def formal_statement(sentence):
    for ending, replacement in FORMAL_ENDINGS.items():
        if sentence.endswith(ending):
            return sentence[:-len(ending)] + replacement
    raise ValueError(f"Unmapped predicate: {sentence}")

CASUAL_QUESTIONS = []
def add(group, aliases, text, negative="아니야."):
    GROUPS.setdefault(group, []).append(len(ROWS))
    CASUAL_QUESTIONS.append(text)
    statement = formal_statement(text.removesuffix('?'))
    question = statement.removesuffix('니다') + '니까?'
    ROWS.append((group, aliases.split('|'), question))
    NEGATIVE.append(negative)
    TRAITS.append(statement)

for line in (Path(__file__).parent/'data/cub_attributes.txt').read_text().splitlines():
    num, raw = line.split(maxsplit=1)
    group, value = raw[4:].split('::')
    negative = "아니야."
    if group in SPECIAL:
        index = len(GROUPS.get(group, []))
        alias = SPECIAL[group][index]
        sentence = SPOKEN[group][index]
        if group == 'shape' and sentence.startswith('체형이 ') and sentence.endswith(' 닮았어'):
            bird = sentence.split()[1][:-1]
            sentence = f"생김새가 {particle(bird,'을','를')} 닮았어"
    else:
        part, kind = group.rsplit('_',1)
        name = DISPLAY_PARTS.get(part, PARTS[part].split('|')[0])
        alias = (COLOR if kind=='color' else PATTERN)[value]
        feature = alias.split('|')[0]
        if kind=='color':
            if value=='iridescent':
                sentence = f"{name}에서 금속 같은 광택이 나"
                negative = f"아니야. {name}에서는 그런 광택이 안 보여."
            else:
                sentence = f"{particle(name,'이','가')} {feature}이야"
                negative = f"아니야. {particle(name,'은','는')} {particle(feature,'이','가')} 아니야."
        elif value=='multi-colored':
            sentence = f"{name}에 여러 색이 섞인 무늬가 있어"
        elif value=='solid':
            sentence = f"{particle(name,'은','는')} 무늬 없이 한 가지 색이야"
        else:
            sentence = f"{name}에 {particle(feature,'이','가')} 있어"
            negative = f"아니야. {name}에는 {particle(feature,'이','가')} 없어."
    add(group, alias, sentence+'?', negative)
    assert int(num)==len(ROWS)
add('broad_size','큰편|크다|크니|큰|커|클까','몸집이 큰 편이야?')
add('broad_size','작은편|작|조그|쪼그','몸집이 작은 편이야?')
add('species_fact','물갈퀴','발가락 사이에 물갈퀴가 이어져 있어?')
add('species_fact','물새','주로 물이나 물가에서 생활해?')
add('species_fact','통통|다부진|다부져','이 종은 보통 통통하고 다부진 체형이야?')
PATTERN_SOURCES = {}
for pattern, aliases in (("줄무늬", "줄무늬|줄무늬새|줄이"),
                         ("점무늬", "점무늬|점박이|반점")):
    sources = [k for k, (group, names, _) in enumerate(ROWS)
               if group.endswith("_pattern") and pattern in names]
    add("overall_pattern", aliases, f"몸에 {particle(pattern,'이','가')} 있어?")
    PATTERN_SOURCES[len(ROWS)-1] = sources

def overall_pattern(row, sources):
    values = [row[k] for k in sources]
    if 1 in values:
        return 1
    return 0 if all(value == 0 for value in values) else -1

QUESTIONS=[row[2] for row in ROWS]

def spoken_answer(index, value):
    if index == WATER_CLUE and value >= 0:
        return ("응! 도감에 따르면 주로 물이나 물가에서 지내는 새야." if value
                else "아니야. 도감에서는 물가를 주로 찾는 새로 분류하지 않아.")
    if value < 0:
        return "사진만 봐서는 잘 모르겠어."
    if not value:
        return NEGATIVE[index]
    return "응, " + CASUAL_QUESTIONS[index].removesuffix("?") + "!"

def normalize(text):
    return re.sub(r"[\s?!？‘’.,]", "", text.lower())
EXACT = {normalize(q): i for forms in (CASUAL_QUESTIONS, QUESTIONS) for i, q in enumerate(forms)}

# Compose location, habitat verb and conversational ending independently.
WATER_PLACE = r"(?:물가쪽|물가근방|강변|물가근처|바닷가|바다|바닷물|해안가?|해변|연안|갯벌|강가?|하천|계곡|냇가|개울|민물|담수|호숫가|호수|연못|저수지|늪지?|습지|물가|물속|수변|물)"
WATER_LOCATION = WATER_PLACE + r"(?:근처|가까이|주변|인근|부근|가운데|쪽|속)?(?:에서|에|에도|에서도|가|이|인가|입니까|야|예요|이에요|인가요|는|은|도)?"
PREFIX = r"(?:(?:그럼|그러면|혹시|이새는|이새가|이새|그새는|얘는|얘가|얘|보통|주로|평소에|평소|원래|주서식지가|서식지가|서식지는|사는곳이|사는곳은))*"
HABITAT_VERB = r"(?:살(?:아|아요|까|까요|지|죠|고있|고있어|고있나요|고있습니까|기도해|기도하나요|아가는|아가는편|던)?|사(?:니|나요|는|는편|는거|는건가|는건지|는지|는곳)|삽니까|산다|서식(?:해|해요|하니|하나요|합니까|하는|하는편|하는지)|생활(?:해|해요|하니|하나요|합니까|하는|하는편)|지내(?:니|나요|는|는편)?|지냅니까)"
ENDING = r"(?:새|종|편|거|것|곳|환경)?(?:야|니|요|인가|인가요|일까|일까요|맞아|맞나요|예요|이에요|입니까|하니|하나요)?"
WATER_QUESTION = re.compile(PREFIX + WATER_LOCATION + r"(?:주로|보통|자주)?" + HABITAT_VERB + ENDING)
WATER_NOUN = re.compile(PREFIX + r"(?:물태그가있는새|물태그|물새|바닷새|바다새|해양성조류|수생조류|수조류)" + ENDING)
WATER_CLUE = GROUPS['species_fact'][1]

BILL_LONG = r"(?:긴|길어|길다|길지|깁|기니|길)"
BILL_SHORT = r"(?:짧|작|작은)"
def bill_choice(text):
    text = normalize(text)
    return bool(re.fullmatch(r"(?:혹시)?부리(?:가|는|길이가)?"+BILL_LONG+
                             r"(?:편)?(?:이냐|가요|가|지|야)?"+BILL_SHORT+
                             r".{0,2}(?:편)?(?:이냐|인가요|인가|이야|야|나요)?", text))


def interpret(text, previous=None):
    text=normalize(text)
    # Keep negation and compounds from becoming positive habitat evidence.
    if re.search(r"(?:안|못)(?:살|사니|사나|삽|서식|지내|생활)|(?:살지|서식하지|생활하지)않", text):
        return None
    if text in EXACT: return EXACT[text]
    if re.search('아니|않|거나|그리고|또는',text): return None
    text = re.sub(r"발가락사이(?:가|에)?(?:막으로이어|막이(?:있|연결)|막으로연결).*", "물갈퀴", text)
    text = text.replace("통실통실", "통통").replace("포동포동", "통통")
    if WATER_QUESTION.fullmatch(text) or WATER_NOUN.fullmatch(text):
        return WATER_CLUE
    if (previous == WATER_CLUE or re.search("서식지|사는곳",text)) and re.fullmatch(PREFIX + WATER_LOCATION + ENDING,text):
        return WATER_CLUE
    for k in PATTERN_SOURCES:
        aliases = "|".join(ROWS[k][1])
        if re.fullmatch(PREFIX + r"(?:몸전체에|몸에|깃털에|몸통에)?(?:" + aliases +
                        r")(?:가|이|도|는)?(?:있어|있을까|있는지|있을까요|있어요|있나요|있니|있나|있습니까|있는편|인가요|야|야해)?", text):
            return k
    # Match the longest part first: 꼬리윗면 is more specific than 꼬리.
    parts=set()
    rest=text
    for token,part in sorted(((t,p) for p,aliases in PARTS.items() for t in aliases.split('|')),key=lambda v:-len(v[0])):
        if token in rest:
            parts.add(part)
            rest=rest.replace(token,'')
    if parts == {'bill'}:
        descriptor = re.sub(r"^(?:혹시)?(?:가|는|길이가)?", "", rest)
        ending = r"(?:은|아|나요|습니까|냐|니|다|지)?(?:편)?(?:이냐|인가요|인가|이야|이니|이에요|입니까|야)?"
        for pattern, k in ((BILL_LONG, GROUPS['bill_length'][1]), (BILL_SHORT, GROUPS['bill_length'][2])):
            if re.fullmatch(pattern + ending, descriptor):
                return k
    if len(parts) == 1:
        # A one-syllable colour shorthand is meaningful only as the whole descriptor.
        shorthand = {'검':'검정', '흑':'검정', '백':'흰색', '빨':'빨강', '파':'파랑', '노':'노랑'}
        if rest in shorthand:
            part = next(iter(parts))
            return next((k for k in GROUPS.get(part+'_color', [])
                         if shorthand[rest] in ROWS[k][1]), None)
    if previous is not None and len(parts)==1 and rest in ('은','는','도','그럼은','그럼는','그럼도','그러면은','그러면는'):
        group,aliases,_=ROWS[previous]
        if group.endswith(('_color','_pattern')):
            sibling=next(iter(parts))+'_'+group.rsplit('_',1)[1]
            return next((k for k in GROUPS.get(sibling,[]) if ROWS[k][1][0]==aliases[0]),None)
    candidates=[]
    for group, indices in GROUPS.items():
        if group == "overall_pattern": continue
        part=group.rsplit('_',1)[0]
        if part in PARTS:
            if part not in parts and not (part=='primary' and not parts and group.endswith('_color')): continue
            if group.endswith('_color') and re.search('무늬|줄|반점',text): continue
        if group in ('size','broad_size') and (parts or '보다' in text): continue
        if group=='shape' and re.search('서식|살아|먹|사냥',text): continue
        matches=[(len(alias),k) for k in indices if k != WATER_CLUE for alias in ROWS[k][1] if alias in text]
        if matches:
            # Ignore a shorter synonym contained in a more specific one.
            hits={k for _,k in matches}
            for k in list(hits):
                short=[a for a in ROWS[k][1] if a in text]
                if all(any(a in b and a!=b for j in hits-{k} for b in ROWS[j][1] if b in text) for a in short):
                    hits.discard(k)
            candidates.extend(hits)
    if any(i in GROUPS['size'] for i in candidates):
        candidates=[i for i in candidates if i not in GROUPS['broad_size']]
    if len(parts)>1 and not (parts=={'head','bill'} and all(i in GROUPS['bill_length'] for i in candidates)): return None
    return candidates[0] if len(candidates)==1 else None

# Species-level notes; missing observations stay unknown.
def species_facts(name):
    name=name.lower()
    if name.endswith('albatross'): return (1,1,-1)
    if name.endswith('grebe'): return (0,1,-1)
    if name=='horned puffin': return (-1,1,1)
    return (-1,-1,-1)
