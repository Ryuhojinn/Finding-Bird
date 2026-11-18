const el = id => document.getElementById(id);
let catalog, game, selection, busy = false;
function drawCards() {
  const cards = el('cards'); cards.replaceChildren();
  catalog.names.forEach((name,i) => {
    if (!name.toLowerCase().includes(el('search').value.trim().toLowerCase())) return;
    const button = document.createElement('button'), img = new Image();
    button.className='card'; img.src=catalog.images[i]; img.loading='lazy'; img.alt='';
    button.append(img,document.createTextNode(name));
    button.onclick=()=>{selection=i;el('portrait').src=catalog.images[i];el('birdname').textContent=name;el('traits').textContent=catalog.traits[i].join(' / ');
      el('guess').hidden=!game || game.stage!==1 || game.ended; el('detail').showModal();};
    cards.append(button);
  });
  if(!cards.children.length) cards.textContent='검색 결과가 없습니다.';
}
async function action(op,text=''){
  if(busy)return;
  busy=true;
  try {
    const r=await fetch('/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op,text,id:game?.id})});
    if(!r.ok)throw Error(); game=await r.json(); render();
  }catch{el('hint').textContent='페이지를 다시 열면 연결을 재시도합니다.';}
  finally{busy=false;}
}
function render(){
  const first=game.stage===1;
  el('role').textContent=first?'1라운드 · 플레이어가 추리합니다':'2라운드 · 삐오가 추리합니다';
  el('count').textContent=game.count+' / 20회';
  el('hint').textContent=first?'색이나 생김새를 질문한 뒤 도감에서 정답을 선택합니다.':'사진을 보고 삐오의 질문에 답합니다.';
  el('notes').textContent=(game.notes||[]).join(' · '); el('secret').hidden=!game.photo;if(game.photo)el('secret').src=game.photo;
  el('logs').replaceChildren();
  for(const [who,msg] of game.logs){const b=document.createElement('div'),s=document.createElement('small');
    b.className='bubble'+(who==='나'?' mine':'');s.textContent=who;b.append(s,document.createTextNode(msg));el('logs').append(b);}
  if(!game.logs.length)el('logs').textContent='새 한 마리를 골랐습니다. 어떤 특징이 궁금하십니까?';
  el('logs').scrollTop=el('logs').scrollHeight;
  el('msg').placeholder=first?'배가 노란색입니까?':'그렇습니다 / 아닙니다 / 잘 모르겠습니다';
  el('form').hidden=game.ended;el('next').hidden=!game.ended;el('score').textContent='';
  el('next').textContent=first?'공수 교대 →':'새 경기 시작';
  if(!first&&game.ended){const [a,b]=game.scores, fmt=x=>x===21?'실패':x+'회';
    el('score').textContent=(a===b?'무승부입니다.':a<b?'플레이어가 승리했습니다!':'삐오가 승리했습니다!')+' · 나 '+fmt(a)+' / 삐오 '+fmt(b);
    if(a===b)el('next').textContent='새 사진으로 재경기';}
}
el('form').onsubmit=e=>{e.preventDefault();const t=el('msg').value.trim();if(t&&!busy){el('msg').value='';action('message',t);}};
el('next').onclick=()=>action('next');el('search').oninput=drawCards;
el('openHelp').onclick=()=>el('help').showModal();
el('close').onclick=()=>el('detail').close();
el('guess').onclick=()=>{el('detail').close();action('message','정답 '+catalog.names[selection]);};
function showClues(){
  const box=el('clues');box.replaceChildren();
  const filter=el('clueFilter').value.trim();
  for(const question of catalog.questions.filter(q=>q.includes(filter))){
    const b=document.createElement('button');
    b.type='button';b.textContent=question;
    b.onclick=()=>{if(game.stage===1&&!game.ended){el('msg').value=question;el('msg').focus();}};
    box.append(b);
  }
}
el('clueFilter').oninput=showClues;
(async()=>{catalog=await(await fetch('/catalog')).json();
el('total').textContent=catalog.names.length+'종';drawCards();showClues();await action('start');})();
