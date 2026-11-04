'use strict';
const words=['Tasse','Tasche','Kanne','Katze','Teller','Topf','Stuhl','Schrank'];
const ipa=['ˈtasə','ˈtaʃə','ˈkanə','ˈkatsə','ˈtɛlɐ','tɔpf','ʃtuːl','ʃʁaŋk'];
const $=id=>document.getElementById(id);
let task='perception', selected='Kanne', result=null, busy=false, playing=false, frame=null, lastTime=0, position=0;
const ablation = {};
const componentNames = {};
let neighbourData = null;
const RECORDED = document.body.dataset.mode === 'recorded';
const productionPresets = [
  {id:'reference', name:'Reference', remaining:[100,100,100], note:'Kanne: with all neurons available, mean phonological target activation is 0.94 and the word is retrieved. This is the reference for the four damage cases.'},
  {id:'buffers', name:'Two buffers reduced', remaining:[50,100,50], note:'Kanne: with 50% of concept and lemma neurons remaining, phonological target activation falls from 0.94 to 0.52. The word is still retrieved, despite the weaker representation.'},
  {id:'memory90', name:'Memory at 90%', remaining:[50,90,50], note:'Kanne: reducing the concept-to-lemma memory to 90% remaining neurons lowers phonological target activation further, to 0.43. Retrieval still succeeds.'},
  {id:'memory80', name:'Memory at 80%', remaining:[50,80,50], note:'Kanne: with 80% of memory neurons remaining and both buffers still at 50%, phonological target activation is nearly zero (0.001). The model no longer retrieves a word.'},
  {id:'lemma75', name:'Lemma restored to 75%', remaining:[50,80,75], note:'Kanne: restoring the lemma buffer from 50% to 75% remaining neurons brings phonological target activation back to 0.41 and restores retrieval. The concept buffer stays at 50% and the memory at 80%.'},
];
if (!RECORDED) {
  Object.assign(productionPresets[2], {id:'memory70', name:'Memory at 70%', remaining:[50,70,50]});
  Object.assign(productionPresets[3], {id:'memory55', name:'Memory at 55%', remaining:[50,55,50]});
  Object.assign(productionPresets[4], {id:'lemma75-memory55', remaining:[50,55,75]});
  const liveNotes = [
    'Kanne: in the 613-entry lexicon, undamaged mean phonological target activation is 0.973. The word is retrieved against all 613 candidates.',
    'Kanne: with 50% of concept and lemma neurons remaining, mean phonological target activation falls from 0.973 to 0.528. Retrieval still succeeds.',
    'Kanne: with both buffers at 50% and the concept-to-lemma memory at 70%, mean phonological target activation is 0.298. Kanne remains the strongest candidate, but lies just below the 0.30 retrieval threshold. This is a borderline case, not a formally successful retrieval.',
    'Kanne: with both buffers at 50% and the concept-to-lemma memory at 55%, mean phonological target activation is approximately 0.001. No word is retrieved.',
    'Kanne: restoring the lemma buffer from 50% to 75%, with the concept buffer at 50% and the memory at 55%, brings mean phonological target activation to 0.325. Kanne is correctly retrieved, although the target value is only 0.025 above the 0.30 threshold.'
  ];
  productionPresets.forEach((preset, i) => { preset.note = liveNotes[i]; });
}
function renderPresets() {
  const host=$('production-presets');if(!host)return;
  host.replaceChildren(...productionPresets.map((preset,i)=>{
    const button=document.createElement('button');button.type='button';button.className='preset';button.dataset.preset=preset.id;
    button.innerHTML=`<span class="preset-number">${i===0?'BASELINE':'CASE '+i}</span><strong>${preset.name}</strong><span>${preset.remaining.join('% / ')}%</span>`;
    button.onclick=()=>{
      if(busy)return;
      for(const key of Object.keys(ablation))if(key.startsWith('production_'))ablation[key]=0;
      ['concept','c2l','lemma'].forEach((part,j)=>ablation['production_'+part]=100-preset.remaining[j]);
      setTask('production');
      $('status').textContent=preset.name+' selected for '+selected+'. Press '+(RECORDED?'Play':'Start')+' production.';
    };
    return button;
  }));
}
function updatePresets() {
  if(!$('production-presets'))return;
  let matched=null;
  document.querySelectorAll('[data-preset]').forEach((button,i)=>{
    const preset=productionPresets[i];
    const active=task==='production' && ['concept','c2l','lemma'].every((part,j)=>ablation['production_'+part]===100-preset.remaining[j]) && ablation.production_l2p===0 && ablation.production_phonology===0;
    button.disabled=busy;button.classList.toggle('selected',active);button.setAttribute('aria-pressed',String(active));
    if(active)matched=preset;
  });
  $('preset-description').textContent=matched ? matched.note : (RECORDED?'Select a case, then press Play production above. The diagram shows the recorded settings.':'Select a case to set the sliders and switch to production. Then press Start production above. Your selected word is retained.');
}
const levels={phonology:['Phonology','The sound form of the word'],lemma:['Lemma','The lexical entry'],concept:['Concept','The meaning of the word']};
function stop(){playing=false;cancelAnimationFrame(frame);$('play').textContent='▶';$('play').setAttribute('aria-label','Start playback');}
function reset(){stop();result=null;position=0;$('timeline').value=0;$('timeline').disabled=true;$('play').disabled=true;$('time').textContent='0.00 s';$('state').textContent='Ready';$('transfer').hidden=true;$('code-box').hidden=true;$('code').value='';$('result-tag').textContent='TASK GOAL';$('result-title').textContent=task==='perception'?'Which concept does this sound form represent?':'Which sound form belongs to this concept?';$('result-text').textContent=task==='perception'?'The perception pathway stops here. Word production starts only when you choose to continue.':'The production pathway starts from meaning and retrieves a phonological word form of its own.';}
function choose(word){selected=word;reset();updateDamage();renderChoices();renderFlow();$('status').textContent=task==='perception'?'Sound form selected. Ready for the perception pathway.':'Concept selected. Ready for the production pathway.';}
function renderChoices(){$('choices').replaceChildren(...words.map((word,i)=>{const b=document.createElement('button');b.className='choice'+(word===selected?' selected':'');b.textContent=task==='perception'?'/'+ipa[i]+'/':word;b.setAttribute('aria-pressed',String(word===selected));b.disabled=busy;b.onclick=()=>choose(word);return b;}));}
function renderFlow(){const order=task==='perception'?['phonology','lemma','concept']:['concept','lemma','phonology'];$('flow').innerHTML=order.map((level,i)=>`<article class="level" data-level="${level}"><span class="level-number">0${i+1}</span><h3>${levels[level][0]}</h3><span class="level-sub">${levels[level][1]}</span>${words.map((w,j)=>`<div class="row" data-index="${j}"><div class="row-label"><b>${w}</b><output>0.00</output></div><div class="bar"><span></span></div></div>`).join('')}</article>`).join('');}
function setTask(next, word=selected){if(busy)return;task=next;selected=word;reset();for(const t of ['perception','production']){$(t).classList.toggle('selected',t===task);$(t).setAttribute('aria-pressed',String(t===task));}const p=task==='perception';$('input-title').textContent=p?'Choose a sound form':'Activate a concept';$('input-help').textContent=p?'Select a phonological transcription. The model retrieves its meaning.':'Choose the meaning you want to express. The model retrieves the corresponding word form.';$('input-note').textContent=p?'The selected sound form is supplied as a complete phonological pointer.':'The word label is a selection button: only the concept pointer is supplied as input.';$('run').innerHTML=(RECORDED?(p?'Play perception':'Play production'):(p?'Start perception':'Start production'))+' <span>↗</span>';$('model-title').textContent=p?'How sounds become meaning':'How meaning becomes a word';$('status').textContent=p?'Choose a sound form and start the perception pathway.':'Choose a concept and start the production pathway.';renderChoices();renderFlow();updateDamage();}
function draw(index){if(!result)return;index=Math.max(0,Math.min(result.time.length-1,index));$('timeline').value=index;$('time').textContent=result.time[index].toFixed(2)+' s';for(const card of document.querySelectorAll('.level')){const level=card.dataset.level, values=result.levels[level][index];const max=Math.max(...values);const selection=result.selections[level+'_entries']?.[index];card.querySelectorAll('.row').forEach((row,j)=>{row.querySelector('output').textContent=values[j].toFixed(2);row.querySelector('.bar span').style.width=Math.max(0,Math.min(100,values[j]/1.2*100))+'%';row.classList.toggle('winner',values[j]===max&&max>.3);row.classList.toggle('chosen',!!selection&&selection[j]>.3);});}}
function showResult(){position=60;draw(60);const p=task==='perception';$('state').textContent='Completed';$('result-tag').textContent=p?'STOP AT THE CONCEPT LEVEL':'INDEPENDENT WORD OUTPUT';$('result-title').textContent=result.winner?(p?'Concept found: ':'Word form retrieved: ')+result.winner:'No unambiguous retrieval';$('result-text').textContent=result.winner?(p?'The sound form has been mapped to a meaning. This completes the perception task. You can now explicitly choose this concept as the starting point for a new production task.':'A phonological word form was retrieved from the activated concept via its lemma entry. Microphone input and an articulation model will be added at a later stage.'):'The neural output does not meet the retrieval criteria. No output code is generated.';$('transfer').hidden=!(p&&result.winner&&words.includes(result.winner));$('code-box').hidden=p||!result.winner||!result.code;if(!p&&result.winner&&result.code){$('code').value=result.code;$('pointer').textContent='Word-form pointer: '+result.pointer+' · IPA display; not yet a Dynart control code.';}$('status').textContent=(result.cached?'Previously computed run from this session':'Neural simulation completed')+' · '+result.neurons.toLocaleString('en-US')+' LIF neurons · Snapshot at 0.60 s; result from 0.45–0.70 s.';}
function damageDescription(values, direction=task) {
  const changed=Object.entries(values).filter(([key,value])=>key.startsWith(direction+'_') && value>0);
  return changed.length ? changed.map(([key,value])=>componentNames[key]+': '+value+'% ablation').join(' · ') : 'No ablation';
}
function renderDamage() {
  if (!$('lexicon-schema')) return;
  const paths={production:[['concept','Concept level'],['c2l','Concept → Lemma'],['lemma','Lemma level'],['l2p','Lemma → Phonology'],['phonology','Phonology level']],perception:[['concept','Concept level'],['l2c','Lemma → Concept'],['lemma','Lemma level'],['p2l','Phonology → Lemma'],['phonology','Phonology level']]};
  $('lexicon-schema').innerHTML=Object.entries(paths).map(([direction,items])=>`<section class="schema-path ${direction}" data-path="${direction}" aria-label="${direction} pathway"><h3>${direction==='production'?'Production ↓':'Perception ↑'}<small class="path-state"></small></h3>${items.map(([part,name],i)=>{
    const key=direction+'_'+part;ablation[key]=0;componentNames[key]=name;
    const memory=i%2===1;
    return `<div class="${memory?'memory-link':'buffer-link'}"><article class="damage-node ${memory?'memory-node':'buffer-node'}" data-component="${key}"><div class="node-heading"><span>${memory?'ASSOCIATIVE MEMORY':'STATE BUFFER'}</span><strong>${name}</strong></div><label for="remaining-${key}">Remaining neurons <output id="value-${key}" for="remaining-${key}">100%</output></label><input id="remaining-${key}" data-damage="${key}" type="range" min="0" max="100" step="1" value="100" aria-label="${direction} ${name}: remaining neurons" aria-describedby="ablated-${key}"><div class="node-scale"><span>0%</span><span id="ablated-${key}">0% ablation</span><span>100%</span></div></article></div>`;
  }).join('')}</section>`).join('');
  document.querySelectorAll('[data-damage]').forEach(input=>input.addEventListener('input',()=>{
    ablation[input.dataset.damage]=100-Number(input.value);
    reset();renderFlow();updateDamage();
    $('status').textContent='Damage settings changed. Start a new '+task+' run to see the effect.';
  }));
  $('restore-neurons').onclick=()=>{if(busy)return;for(const key of Object.keys(ablation))ablation[key]=0;reset();renderFlow();updateDamage();$('status').textContent=(RECORDED?'Undamaged reference selected. Press Play to view the recording.':'All neurons restored. Start a new run for the undamaged model.');};
  updateDamage();
}
function updateDamage() {
  renderNeighbours();
  if (!$('lexicon-schema')) return;
  for(const [key,value] of Object.entries(ablation)) {
    const input=$('remaining-'+key);input.value=100-value;input.disabled=busy || RECORDED;
    input.setAttribute('aria-valuetext',(100-value)+'% remaining, '+value+'% ablation');
    $('value-'+key).textContent=(100-value)+'%';$('ablated-'+key).textContent=value+'% ablation';
    input.closest('.damage-node').classList.toggle('damaged',value>0);
  }
  document.querySelectorAll('[data-path]').forEach(path=>{const active=path.dataset.path===task;path.classList.toggle('active-path',active);path.querySelector('.path-state').textContent=active?'CURRENT TASK':'AVAILABLE FOR NEXT TASK';});
  updatePresets();
  $('restore-neurons').disabled=busy;
  $('damage-summary').textContent=(RECORDED?'Selected recording · ':'Next '+task+' run · ')+damageDescription(ablation);
  $('damage-run').textContent=result ? 'Displayed run · '+damageDescription(result.ablation,result.task)+' · '+Object.values(result.damage).reduce((n,d)=>n+d.ablated,0).toLocaleString('en-US')+' neurons silenced (seed '+result.ablation_seed+').' : (RECORDED?'The diagram displays the selected recording settings. Perception uses the undamaged reference; production offers five cases for each of the eight words.':'Settings apply to the next run. Each task simulates its own pathway; settings on the other side are retained for that task.');
}
function tick(now){if(!playing)return;position+=(now-lastTime)/1000/Number($('speed').value)*100;lastTime=now;draw(Math.floor(position));if(position>=result.time.length-1){stop();showResult();return;}frame=requestAnimationFrame(tick);}
function play(){if(!result)return;if(playing){stop();return;}if(position>=result.time.length-1)position=0;playing=true;lastTime=performance.now();$('play').textContent='Ⅱ';$('play').setAttribute('aria-label','Pause playback');frame=requestAnimationFrame(tick);}
async function jsonFetch(url,options){const r=await fetch(url,options);const data=await r.json();if(!r.ok)throw new Error(data.error||'The request failed.');return data;}
async function run(){if(busy)return;reset();renderFlow();busy=true;calculationFeedback.show('Das neuronale Lexikon-Modell wird aufgebaut und simuliert. Bitte einen Moment warten.');renderChoices();updateDamage();$('run').disabled=true;$('perception').disabled=true;$('production').disabled=true;$('state').textContent='Computing …';$('status').textContent='The neural model is being built and simulated. The 613-entry lexicon may take about a minute per run.';try{const job=await jsonFetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task,word:selected,ablation:{...ablation}})});let data;do{await new Promise(r=>setTimeout(r,600));data=await jsonFetch('/api/jobs/'+job.id);}while(data.status==='running');if(data.status==='error')throw new Error(data.error||'Simulation failed.');result=data.result;updateDamage();$('timeline').max=result.time.length-1;$('timeline').disabled=false;$('play').disabled=false;$('state').textContent='Playback';$('status').textContent='Slow-motion playback of a computed neural run. You can pause and move through model time.';position=0;play();}catch(e){$('state').textContent='Error';$('status').textContent=e.message;}finally{calculationFeedback.hide();busy=false;renderChoices();updateDamage();$('run').disabled=false;$('perception').disabled=false;$('production').disabled=false;}}
$('perception').onclick=()=>setTask('perception');$('production').onclick=()=>setTask('production');$('run').onclick=run;$('play').onclick=play;$('timeline').oninput=()=>{stop();position=Number($('timeline').value);draw(position);};$('transfer').onclick=()=>{if(result?.winner){const word=result.winner;setTask('production',word);$('status').textContent='Transferred concept: '+word+'. Start production when you are ready.';}};$('copy').onclick=async()=>{try{await navigator.clipboard.writeText($('code').value);$('copy').textContent='Copied';setTimeout(()=>{$('copy').textContent='Copy';},1500);}catch{$('code').select();$('status').textContent='Code selected — press ⌘C or Ctrl+C to copy.';}};
renderPresets();
renderDamage();
setTask('perception');

// Static template geometry: task changes and ablation never alter these values.

function renderNeighbours() {
  if (!neighbourData || RECORDED) return;
  const selectedOnly = $('neighbours-selected-only').checked;
  const tables = ['concept', 'phonology'].map(level => {
    const wrapper = document.createElement('div'); wrapper.className = 'neighbours-table-wrap';
    const table = document.createElement('table'); table.className = 'neighbours-table';
    const caption = table.createCaption(); caption.textContent = level === 'concept' ? 'Semantic neighbours' : 'Phonological neighbours';
    const head = table.createTHead().insertRow();
    ['Word', '1st', '2nd', '3rd', '4th', '5th'].forEach(label => { const th = document.createElement('th'); th.scope = 'col'; th.textContent = label; head.append(th); });
    const body = table.createTBody();
    neighbourData.words.forEach((word, i) => {
      if (selectedOnly && word !== selected) return;
      const row = body.insertRow(); row.classList.toggle('selected-neighbour', word === selected);
      const th = document.createElement('th'); th.scope = 'row'; th.textContent = word; if(word === selected) th.setAttribute('aria-label', word + ', selected input'); row.append(th);
      neighbourData.levels[level][i].forEach(item => {
        const cell = row.insertCell(), name = document.createElement(words.includes(item.word) ? 'strong' : 'span'), score = document.createElement('span');
        name.textContent = item.word; score.textContent = item.similarity.toFixed(3); score.className = 'neighbour-score';
        const strength = Math.max(0, Math.min(1, item.similarity));
        cell.style.backgroundColor = `hsl(174 36% ${97-strength*66}%)`;
        cell.style.color = strength > .7 ? '#fff' : '#173d36';
        cell.append(name, score); row.append(cell);
      });
    });
    wrapper.append(table); return wrapper;
  });
  $('neighbours-tables').replaceChildren(...tables);
  $('neighbours-status').textContent = 'Selected input: ' + selected + ' · ' + neighbourData.lexicon_size + ' entries · 512 dimensions · vector seed 10';
}
async function loadNeighbours() {
  if (RECORDED || !$('neighbours')) return;
  $('neighbours').hidden = false;
  $('neighbours-selected-only').onchange = renderNeighbours;
  try { neighbourData = await jsonFetch('/api/neighbours'); renderNeighbours(); }
  catch(e) { $('neighbours-status').textContent = 'Lexical neighbours could not be loaded. ' + e.message; }
}
loadNeighbours();
