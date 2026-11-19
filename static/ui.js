const el = id => document.getElementById(id);
let catalog, game, selection, busy = false;
// Draw on a 32-pixel grid so the mascot stays crisp at every display size.
function drawPio(canvas, mood='idle', pose=null){
  const ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,32,32);
  const variant=canvas.dataset.bird;
  const rose=variant==='rose', blue=variant==='blue';
  const ink='#553949', honey=rose?'#ee9698':blue?'#91c3df':'#ffcf60';
  const cream=rose?'#ffddd0':blue?'#e1f3f4':'#fff1af';
  function box(x,y,w,h,color){ctx.fillStyle=color;ctx.fillRect(x,y,w,h);}
  const body=[[5,11,20],[6,9,22],[7,7,24],[8,6,25],[9,5,26],[10,5,26],
    [11,4,27],[12,4,27],[13,3,28],[14,3,28],[15,3,28],[16,3,28],
    [17,3,28],[18,3,28],[19,3,28],[20,4,27],[21,4,27],[22,5,26],
    [23,6,25],[24,7,24],[25,9,22],[26,11,20]];
  if(pose){ctx.save();ctx.translate(0,-pose.lift);}
  for(const [y,l,r] of body) box(l,y,r-l+1,1,ink);
  for(const [y,l,r] of body.slice(1,-1)) box(l+1,y,r-l-1,1,honey);
  box(12,3,3,3,ink);box(13,3,1,3,honey);box(16,2,3,4,ink);box(17,3,1,3,honey);
  box(9,17,14,5,cream);box(11,16,10,8,cream);box(13,23,6,2,cream);
  box(6,16,4,2,'#fa9792');box(22,16,4,2,'#fa9792');
  for(const x of [9,20]){
    if(mood==='win'){box(x,12,4,1,ink);box(x,13,1,1,ink);box(x+3,13,1,1,ink);}
    else {box(x,12,3,4,ink);box(x,12,1,1,'#fff');}
  }
  box(14,15,4,2,'#c66a37');box(15,15,2,1,'#ffad51');
  if(pose?.talk) box(15,17,2,1,'#a85442');
  if(rose){
    // Tiny daisy tucked just above the right eye.
    box(21,5,2,6,'#fff0df');box(19,7,6,2,'#fff0df');box(21,7,2,2,'#e6a040');
  }else if(blue){
    box(5,6,18,2,'#526586');box(7,3,14,3,'#8095b3');box(12,1,4,2,'#526586');
    box(17,6,9,2,'#526586');
  }else{
    box(8,24,16,2,'#509484');box(11,26,4,3,'#387b71');
  }
  box(9,28,4,2,'#c87742');box(19,28,4,2,'#c87742');
  const wingY=pose?.wing ?? (mood==='win'?14:18);
  for(const x of [2,25]){box(x,wingY,5,4,ink);box(x+1,wingY,3,3,rose?'#c87283':blue?'#6795bd':'#eeb354');}
  if(pose){
    for(const x of [0,29]) box(x,wingY+pose.tip,3,2,'#d8a24f');
    if(pose.drop){
      box(28,pose.drop,1,2,'#589cb9');
      box(27,pose.drop+2,3,2,'#84cee0');
      box(28,pose.drop+2,1,1,'#dcfaff');
    }
    ctx.restore();
  }
  if(mood==='loss'){box(22,16,2,3,'#77b9e2');box(22,18,1,1,'#daf6ff');}
  if(mood==='draw'){box(20,11,4,1,ink);box(16,3,2,1,'#fff3af');}
}
document.querySelectorAll('.pio').forEach(canvas=>drawPio(canvas));
function welcomePio(){
  const poses=[
    {wing:18,tip:3,lift:0,drop:0}, {wing:15,tip:0,lift:0,drop:0,talk:true},
    {wing:12,tip:-2,lift:1,drop:8,talk:true}, {wing:10,tip:-2,lift:2,drop:9},
    {wing:13,tip:0,lift:2,drop:11,talk:true}, {wing:16,tip:2,lift:1,drop:13},
    {wing:19,tip:3,lift:0,drop:15,talk:true}, {wing:18,tip:2,lift:0,drop:0}
  ];
  const tile=document.createElement('canvas');
  tile.width=tile.height=32;
  const strip=el('greetingFrames').getContext('2d');
  poses.forEach((pose,index)=>{
    drawPio(tile,'idle',pose);
    strip.drawImage(tile,index*32,0);
  });
  el('welcome').addEventListener('close',()=>el('size').focus(),{once:true});
  el('welcome').showModal();
}
welcomePio();
function resultScene(outcome){
  drawPio(el('resultIcon'),outcome);
  const field=el('particles');field.replaceChildren();
  const colors={win:['#f5b034','#74b89e','#ee879e'],loss:['#749abc','#a1c2dc'],draw:['#bc99cc','#8e81b4','#edb6bd']}[outcome];
  for(let i=0;i<24;i++){
    const bit=document.createElement('i');
    bit.style.left=((i*37+3)%100)+'%';
    bit.style.top=((i*43+7)%84)+'%';
    bit.style.background=colors[i%colors.length];
    bit.style.setProperty('--delay',-(i%11)*.12+'s');
    field.append(bit);
  }
}
let galleryPhotos=[], photoIndex=0, galleryRequest=0;
function showPhoto(){
  const ref=galleryPhotos[photoIndex];
  const label={1:'줄무늬 있음',0:'줄무늬 없음','-1':'줄무늬 확인 어려움'}[ref.stripe];
  el('portrait').src=ref.image;
  el('portrait').alt=catalog.names[selection]+' 참고 사진 '+(photoIndex+1);
  el('photoNote').textContent='이 참고 사진 · '+label+(ref.complete?'':' · 일부 단서만 일치하거나 기록이 부족합니다.');
  el('photoCount').textContent=(photoIndex+1)+' / '+galleryPhotos.length;
  el('prevPhoto').disabled=photoIndex===0;
  el('nextPhoto').disabled=photoIndex===galleryPhotos.length-1;
}
async function openBird(i){
  const request=++galleryRequest;
  selection=i;
  galleryPhotos=[game.references[i]];
  photoIndex=0;
  showPhoto();
  el('photoCount').textContent='사진 목록을 불러오는 중';
  el('birdname').textContent=catalog.names[i];
  el('traits').textContent=catalog.traits[i].join(' / ');
  el('guess').hidden=game.stage!==1 || game.ended;
  el('detail').showModal();
  try{
    const response=await fetch('/gallery/'+game.id+'/'+i);
    if(!response.ok) throw Error();
    const photos=await response.json();
    if(request!==galleryRequest || !el('detail').open) return;
    galleryPhotos=photos;
    showPhoto();
  }catch{
    if(request===galleryRequest) el('photoCount').textContent='다른 사진을 불러오지 못했습니다.';
  }
}
el('prevPhoto').onclick=()=>{if(photoIndex>0){photoIndex--;showPhoto();}};
el('nextPhoto').onclick=()=>{if(photoIndex+1<galleryPhotos.length){photoIndex++;showPhoto();}};
function drawCards() {
  const cards = el('cards'); cards.replaceChildren();
  game.remaining.forEach(i => {
    const name = catalog.names[i];
    if (!name.toLowerCase().includes(el('search').value.trim().toLowerCase())) return;
    const button = document.createElement('button'), img = new Image();
    const ref=game.references[i];
    button.className='card'; img.src=ref.image; img.loading='lazy'; img.alt='';
    button.append(img,document.createTextNode(name));
    button.onclick=()=>openBird(i);
    cards.append(button);
  });
  if(!cards.children.length) cards.textContent='검색 결과가 없습니다.';
}
async function action(op,text=''){
  if(busy)return;
  busy=true;
  try {
    const r=await fetch('/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op,text,id:game?.id,size:Number(el('size').value)})});
    if(!r.ok)throw Error(); game=await r.json();
    if(op==='start'){
      el('setup').hidden=true;
      el('search').disabled=false;
      el('search').value='';

    }
    if(op!=='message') el('search').value='';
    drawCards();
    render();
  }catch{el('hint').textContent='페이지를 다시 열면 연결을 재시도합니다.';}
  finally{busy=false;}
}
function render(){
  const first=game.stage===1;
  el('foundNotes').hidden=!game.publicNotes.length;
  el('foundNotes').textContent='알아낸 단서 · '+game.publicNotes.join(' / ');
  el('total').textContent='후보 '+game.remaining.length+' / '+game.birds.length+'종';
  el('role').textContent=first?'1라운드 · 플레이어가 추리합니다':'2라운드 · 삐오가 추리합니다';
  el('count').textContent=game.count+' / 20회';
  el('hint').textContent=first?'색이나 생김새를 질문한 뒤 도감에서 정답을 선택합니다.':'사진을 보고 삐오의 질문에 답합니다.';
  el('notes').textContent=(game.notes||[]).join(' · '); el('secret').hidden=!game.photo;if(game.photo)el('secret').src=game.photo;
  el('logs').replaceChildren();
  const lines=first?[['삐오',`도감 속 ${game.birds.length}종 중에서 한 마리를 골랐어. 내가 어떤 새를 골랐게? 궁금한 특징부터 물어봐!`],...game.logs]:game.logs;
  for(const [who,msg] of lines){const b=document.createElement('div'),s=document.createElement('small');
    b.className='bubble'+(who==='나'?' mine':'');s.textContent=who;b.append(s,document.createTextNode(msg));el('logs').append(b);}
  el('logs').scrollTop=el('logs').scrollHeight;
  el('msg').placeholder=first?'배가 노란색입니까?':'그렇습니다 / 아닙니다 / 잘 모르겠습니다';
  el('skip').hidden=first || game.ended;
  el('form').hidden=game.ended;el('next').hidden=!game.ended;el('score').textContent='';
  el('next').textContent=first?'공수 교대 →':'새 경기 시작';
  if(!first&&game.ended){const [a,b]=game.scores, fmt=x=>x===21?'실패':x+'회';
    el('score').textContent=(a===b?'무승부입니다.':a<b?'플레이어가 승리했습니다!':'삐오가 승리했습니다!')+' · 나 '+fmt(a)+' / 삐오 '+fmt(b);
    if(a===b)el('next').textContent='새 사진으로 재경기';
    const outcome=a===b?'draw':a<b?'win':'loss';
    el('result').dataset.outcome=outcome;
    resultScene(outcome);
    el('resultTitle').textContent={win:'승리했습니다!',loss:'패배했습니다.',draw:'무승부입니다.'}[outcome];
    el('resultScores').textContent='나 '+fmt(a)+' · 삐오 '+fmt(b);
    el('result').showModal();}
}
el('skip').onclick=()=>action('message','사진에서 확인하기 어렵습니다.');
el('form').onsubmit=e=>{e.preventDefault();const t=el('msg').value.trim();if(t&&!busy){el('msg').value='';action('message',t);}};
el('next').onclick=()=>{
  if(game.stage===2 && game.scores[0]!==game.scores[1]) {
    el('setup').hidden=false;
    el('next').hidden=true;
    el('size').focus();
  } else action('next');
};
el('setup').onsubmit=e=>{e.preventDefault();action('start');};el('search').oninput=drawCards;
el('openHelp').onclick=()=>el('help').showModal();
el('close').onclick=()=>el('detail').close();
el('guess').onclick=()=>{el('detail').close();action('message','정답 '+catalog.names[selection]);};
function showClues(){
  const box=el('clues');box.replaceChildren();
  const filter=el('clueFilter').value.trim();
  for(const question of catalog.questions.filter(q=>q.includes(filter))){
    const b=document.createElement('button');
    b.type='button';b.textContent=question;
    b.onclick=()=>{if(game?.stage===1&&!game.ended){el('msg').value=question;el('msg').focus();}};
    box.append(b);
  }
}
el('clueFilter').oninput=showClues;
(async()=>{catalog=await(await fetch('/catalog')).json();
el('size').max=catalog.names.length;el('begin').disabled=false;showClues();})();
