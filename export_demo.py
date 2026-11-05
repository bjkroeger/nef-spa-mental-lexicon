"""Build public recorded edition: baseline perception + five production cases."""
import argparse
import subprocess
import sys
from pathlib import Path
import shutil
import json
import hashlib
import re
from demo_server import neighbours, LEXICON
from syllabification import for_live_result

ROOT=Path(__file__).parent
OUT=ROOT/'website/deploy/perception-production-model'
VERSION='613-syllabification-20261105'
NEURAL_VERSION='613-20261104'


def export_readouts():
    """Attach lexical graph readouts without altering any neural observations.

    Original run dates, model versions and source fingerprints remain intact.
    The separate readout fingerprint identifies the added lexical interpretation.
    """
    source=OUT/('runs-'+NEURAL_VERSION)
    target=OUT/('runs-'+VERSION)
    manifest=json.loads((OUT/('manifest-'+NEURAL_VERSION+'.json')).read_text())
    assert len(manifest['recordings']) == 48
    graph_data={key:LEXICON[key] for key in ('entries','phonology_network')}
    fingerprint=hashlib.sha256((ROOT/'syllabification.py').read_bytes()+
        json.dumps(graph_data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    target.mkdir(parents=True,exist_ok=True)
    for item in manifest['recordings']:
        original=(source/item['file']).read_bytes()
        result=json.loads(original)
        assert result['task']==item['task'] and result['input']==item['word']
        assert result['case_id']==item['case'] and result['winner']==item['winner']
        assert result['recorded'] and result['model_version']==NEURAL_VERSION
        result.update(syllabification=for_live_result(LEXICON,result),
                      syllabification_fingerprint=fingerprint,
                      presentation_version=VERSION,
                      neural_recording_sha256=hashlib.sha256(original).hexdigest())
        destination=target/item['file']
        destination.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
        item['bytes']=destination.stat().st_size
        item['neural_recording_sha256']=result['neural_recording_sha256']
    manifest.update(presentation_version=VERSION,syllabification_fingerprint=fingerprint,
        readout_date='2026-11-05',
        readout_method='Stored graph of the accepted winner; no neural recomputation or timing inference.')
    (OUT/('manifest-'+VERSION+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    export_readouts()
    html=(ROOT/'demo/index.html').read_text()
    html=html.replace('<body>', '<body data-mode="recorded">')
    html=html.replace('href="/style.css"','href="./style-613-20261104.css"').replace('src="/app.js"','src="./app-613-20261104.js"').replace('href="/" aria-label','href="./" aria-label')
    html=html.replace('Nengo · live local simulation','Nengo · recorded simulations')
    html=html.replace('<title>Lexicon Lab · Live local simulation</title>','<title>Lexicon Lab · From sound to meaning</title>')
    html=html.replace('<p class="live-label">LIVE SIMULATION <span>Runs on this computer</span></p>','')
    html=re.sub(r'<script>/\* Visible calculation feedback;.*?</script>', '', html, flags=re.S)
    html=html.replace('<!-- LIVE-ONLY SYLLABIFICATION START -->','').replace('<!-- LIVE-ONLY SYLLABIFICATION END -->','')
    html=html.replace('This is the endpoint of the local production pathway.', 'This is the endpoint of the production pathway. Graph and syllable readouts are stored with each recording; there is no automatic connection to the separate Phono-to-Gesture demonstration.')
    html=html.replace('Run production to inspect the retrieved word.', 'Play production to inspect the retrieved word.')
    html=html.replace('<!-- LIVE-ONLY ABLATION START -->','').replace('<!-- LIVE-ONLY ABLATION END -->','')
    html=html.replace('Reduce the remaining neurons in any buffer or associative memory, individually or together. Then start the perception or production test above.', 'Choose one of five production cases below. The sliders display the recorded neuron percentages and cannot be moved. Then press Play production above.')
    html=html.replace('<button id="restore-neurons"', '<button hidden id="restore-neurons"')
    html=html.replace('Select a case to set the sliders and switch to production. Then press Start production above. Your selected word is retained.', 'Select a case, then press Play production above. Your selected word is retained.')
    html=html.replace('The traces are generated in Nengo with 199,400 spiking LIF neurons per task. Each simulation covers 1.1 seconds of model time; playback can be slowed down. Repeated identical runs reuse the result already computed in this session.', 'The traces replay 48 precomputed Nengo runs: eight undamaged perception runs and five production cases for each of eight test words, with all 613 lexical entries participating in each run. Each model has 199,400 LIF neurons before ablation and covers 1.1 seconds. Only the selected recording is downloaded; no simulation runs on the web server. Vector seed: 10; neural seed: 11; ablation seed: 2026.')
    html=html.replace('<footer>','<p class="fine"><a href="../nef-spa-lexical-model.htm">← Model documentation and scientific background</a></p><footer>')
    html=html.replace(NEURAL_VERSION,VERSION)
    (OUT/'index.html').write_text(html)
    css=(ROOT/'demo/style.css').read_text().replace('body[data-mode="recorded"] .neighbours-panel{display:none}', '')
    (OUT/f'style-{VERSION}.css').write_text(css)
    (OUT/f'neighbours-{VERSION}.json').write_text(json.dumps(neighbours(),ensure_ascii=False,separators=(',',':'))+'\n')
    js=(ROOT/'demo/app.js').read_text()
    js=js.replace('if (!RECORDED) {', '{', 1)
    js=js.replace('if (!neighbourData || RECORDED) return;', 'if (!neighbourData) return;')
    js=js.replace("if (RECORDED || !$('neighbours')) return;", "if (!$('neighbours')) return;")
    js=js.replace("jsonFetch('/api/neighbours')", "jsonFetch('./neighbours-613-20261104.json')")
    js=js.replace("panel.hidden = RECORDED || task !== 'production';", "panel.hidden = task !== 'production';")
    js=js.replace('Run production to inspect the retrieved word.', 'Play production to inspect the retrieved word.')
    js=js.replace("(result.cached?'Previously computed run from this session':'Neural simulation completed')", "'Recorded Nengo simulation'")
    start=js.index('async function run()')
    end=js.index("$('perception').onclick",start)
    js=js[:start]+'''async function run(){
 if(busy)return;
 const preset=task==='production' ? productionPresets.find(p=>
   ['concept','c2l','lemma'].every((part,j)=>ablation['production_'+part]===100-p.remaining[j]) && ablation.production_l2p===0 && ablation.production_phonology===0) : productionPresets[0];
 if(!preset){$('status').textContent='Please choose one of the five recorded cases.';return;}
 reset();renderFlow();busy=true;renderChoices();updateDamage();
 $('run').disabled=true;$('perception').disabled=true;$('production').disabled=true;
 $('state').textContent='Loading …';$('status').textContent='Loading the selected recorded Nengo simulation.';
 try{
  const suffix=preset.id==='reference'?'':'-'+preset.id;
  const loaded=await jsonFetch('./runs-613-20261104/'+task+'-'+encodeURIComponent(selected)+suffix+'.json?v=613-20261104');
  if(loaded.task!==task||loaded.input!==selected||!loaded.recorded||loaded.case_id!==preset.id||loaded.lexicon_size!==613||loaded.vector_seed!==10||loaded.neural_seed!==11||loaded.ablation_seed!==2026||loaded.model_version!=='613-20261104')throw new Error('The recording does not match the selected task and case.');
  const relevant=Object.keys(ablation).filter(k=>k.startsWith(task+'_'));
  if(relevant.some(k=>loaded.ablation[k]!==ablation[k]))throw new Error('The recording has different damage settings.');
  result=loaded;updateDamage();
  $('timeline').max=result.time.length-1;$('timeline').disabled=false;$('play').disabled=false;
  $('state').textContent='Playback';$('status').textContent='Playback of the selected recorded neural run. Pause or move through model time to inspect it.';
  position=0;play();
 }catch(e){$('state').textContent='Error';$('status').textContent='Could not load the recording. '+e.message;}
 finally{busy=false;renderChoices();updateDamage();$('run').disabled=false;$('perception').disabled=false;$('production').disabled=false;}
}
''' +js[end:]
    js=js.replace('./runs-613-20261104/',f'./runs-{VERSION}/')
    js=js.replace('./neighbours-613-20261104.json',f'./neighbours-{VERSION}.json')
    js=js.replace('?v=613-20261104',f'?v={VERSION}')
    js=js.replace("||loaded.model_version!=='613-20261104'", "||loaded.model_version!=='613-20261104'||loaded.presentation_version!=="+repr(VERSION)+"||!Object.hasOwn(loaded,'syllabification')")
    assert '/api/' not in js and 'calculationFeedback' not in js
    assert 'calculationFeedback' not in html and 'LIVE-ONLY' not in html
    (OUT/f'app-{VERSION}.js').write_text(js)
    print('Public replay UI ready:',OUT)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--ui-only',action='store_true',help='Rebuild UI without computing recordings')
    args=parser.parse_args()
    if not args.ui_only:
        subprocess.run([sys.executable,str(ROOT/'export_ablation_runs.py')],check=True)
    build()
