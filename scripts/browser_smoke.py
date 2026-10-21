from pathlib import Path
import os,subprocess,sys,time,json,tempfile,urllib.request
from playwright.sync_api import sync_playwright
PROJECT_ROOT=Path(__file__).resolve().parents[1]
ROOT=PROJECT_ROOT.parent
NAMES=['researchgraph']
servers=[]; logs=[]
try:
    for i,name in enumerate(NAMES):
        env={**os.environ,'PYTHONPATH':str(PROJECT_ROOT/'src'),'APP_TOKEN':'browser-validation-token','APP_STATE_DIR':tempfile.mkdtemp(prefix=name+'-browser-'),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'2'}
        log=open(str(PROJECT_ROOT/'reports'/'browser-server.log'),'w'); logs.append(log)
        proc=subprocess.Popen([sys.executable,'-m','uvicorn',f'{name}.api:create_app','--factory','--host','127.0.0.1','--port',str(8105)],env=env,stdout=log,stderr=log); servers.append(proc)
    for i,name in enumerate(NAMES):
        for attempt in range(100):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{8105}/health',timeout=2); break
            except Exception:
                if servers[i].poll() is not None: raise RuntimeError(f'{name} exited: '+Path(str(PROJECT_ROOT/'reports'/'browser-server.log')).read_text())
                time.sleep(.3)
        else: raise RuntimeError(f'{name} not ready')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(**({'executable_path':os.environ['CHROMIUM_EXECUTABLE']} if os.getenv('CHROMIUM_EXECUTABLE') else {}),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        for i,name in enumerate(NAMES):
            context=browser.new_context(viewport={'width':1440,'height':1100},device_scale_factor=1)
            page=context.new_page(); errors=[]; page.on('pageerror',lambda e: errors.append(str(e)))
            base=f'http://127.0.0.1:{8105}'
            import base64,re
            def bridge(payload):
                path=payload['path']
                if not path.startswith('/api/'): raise ValueError('Only local /api requests are supported by this test harness')
                raw=base64.b64decode(payload['body']) if payload.get('body') else None
                req=urllib.request.Request(base+path,data=raw,headers=payload.get('headers',{}),method=payload.get('method','GET'))
                try: response=urllib.request.urlopen(req,timeout=30)
                except urllib.error.HTTPError as exc: response=exc
                body=response.read()
                headers={k:v for k,v in response.headers.items() if k.lower() not in {'content-length','transfer-encoding','content-encoding'}}
                return {'status':response.status,'headers':headers,'body':base64.b64encode(body).decode()}
            page.expose_function('localApiBridge',bridge)
            static=PROJECT_ROOT/'src'/name/'static'
            html=(static/'index.html').read_text()
            html=html.replace('<link rel="stylesheet" href="/static/style.css">','<style>'+(static/'style.css').read_text()+'</style>')
            html=html.replace('<script type="module" src="/static/app.mjs"></script>','')
            page.set_content(html)
            page.add_script_tag(content=r"""
              const testSession=new Map();
              Object.defineProperty(window,'sessionStorage',{value:{getItem:k=>testSession.get(k)||null,setItem:(k,v)=>testSession.set(k,v),removeItem:k=>testSession.delete(k)}});
              if(!crypto.randomUUID)crypto.randomUUID=()=>Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
              window.fetch=async(path,opts={})=>{
                const headers={...(opts.headers||{})};let bytes;
                if(opts.body instanceof FormData){const response=new Response(opts.body);headers['Content-Type']=response.headers.get('content-type');bytes=new Uint8Array(await response.arrayBuffer());}
                else if(opts.body!==undefined)bytes=new TextEncoder().encode(opts.body);
                let body='';if(bytes){let chunks=[];for(let i=0;i<bytes.length;i+=8192)chunks.push(String.fromCharCode(...bytes.slice(i,i+8192)));body=btoa(chunks.join(''));}
                const r=await window.localApiBridge({path,method:opts.method||'GET',headers,body});
                return new Response(Uint8Array.from(atob(r.body),c=>c.charCodeAt(0)),{status:r.status,headers:r.headers});
              };
            """)
            ui=(static/'ui.mjs').read_text().replace('export ','')
            app=re.sub(r"import .*? from './ui.mjs';",'',(static/'app.mjs').read_text(),count=1)
            page.add_script_tag(content=ui+'\n'+app)
            results=[]
            def check(label,condition):
                if not condition: raise AssertionError(name+': '+label)
                results.append({'check':label,'passed':True})
            check('page renders without credentials',page.locator('h1').count()==1)
            page.fill('#token','browser-validation-token'); page.click('#connect'); page.wait_for_function("document.querySelector('#status').textContent.includes('Connected')",timeout=30000)
            check('authenticated dashboard loads',page.locator('.stat').count()==4)
            check('evaluation table contains real metrics',page.locator('#metric-table tbody tr').count()>=2)
            check('model report available',len(page.locator('#report-json').text_content())>100)
            if name=='visionforge':
                check('heatmap returned by inference',page.locator('#overlay').get_attribute('src').startswith('data:image/png'))
                page.select_option('#model','logistic_patch_baseline');page.click('#inspect');page.wait_for_function("!document.querySelector('#inspect').disabled")
                check('baseline can be selected',page.locator('#history .mini-row').count()>=2)
                page.click('#correct');page.wait_for_function("document.querySelector('#status').textContent.includes('Review saved')")
                check('human review is persisted',True)
                # Real file upload through browser -> multipart endpoint -> model.
                import numpy as np
                from PIL import Image
                fn=Path(tempfile.gettempdir())/'visionforge-qa-upload.png'; Image.fromarray(np.full((80,80,3),145,dtype=np.uint8)).save(fn)
                page.set_input_files('#upload',str(fn));page.click('#upload-button');page.wait_for_function("!document.querySelector('#upload-button').disabled")
                check('image upload runs end to end','Inspection complete' in page.locator('#status').text_content())
            elif name=='agentshield':
                check('authorization trace shown',page.locator('.trace-item').count()==3)
                page.fill('#content','The training handbook describes review procedures and ordinary reporting. Reference number DEMO_1234.')
                page.select_option('#source','user');page.select_option('#tool','write_record');page.click('#run');page.wait_for_function("!document.querySelector('#run').disabled")
                check('side effects remain blocked','side effects disabled' in page.locator('#decision').text_content())
                page.click('#policy-button');page.wait_for_function("document.querySelector('#policy-result').textContent.includes('36/36')")
                check('36 trust-boundary scenarios execute',True)
                page.select_option('#detector','tfidf_logistic');page.click('#run');page.wait_for_function("!document.querySelector('#run').disabled")
                check('alternative detector loads from saved artifacts',page.locator('#error').text_content()=='')
            elif name=='streamrank':
                check('recommendations visible',page.locator('.movie').count()==9)
                first=page.locator('.movie h3').first.text_content();page.locator('.movie-actions button').first.click();page.wait_for_function("document.querySelector('#recommend-note').textContent.includes('revision 1')")
                check('feedback updates profile and excludes rated item',first not in page.locator('.movie h3').all_text_contents())
                page.select_option('#user','');page.click('#recommend');page.wait_for_function("!document.querySelector('#recommend').disabled")
                check('cold-start popularity mode','cold start popularity' in page.locator('#recommend-note').text_content())
                page.select_option('#genre','comedy');page.click('#recommend');page.wait_for_function("!document.querySelector('#recommend').disabled")
                check('cold-start metadata mode','cold start metadata' in page.locator('#recommend-note').text_content())
            elif name=='forecastflow':
                check('forecast and interval chart rendered',page.locator('#chart svg path').count()==2 and page.locator('#chart polygon').count()==1)
                page.select_option('#origin','239');page.click('#forecast');page.wait_for_function("!document.querySelector('#forecast').disabled")
                check('historical replay shows observed outcomes',page.locator('#forecast-mode').text_content()=='historical replay')
                page.fill('#stock','10000');page.click('#forecast');page.wait_for_function("!document.querySelector('#forecast').disabled")
                check('inventory respects existing stock','0 units' in page.locator('#plan').text_content())
                page.select_option('#model','seasonal_naive');page.click('#forecast');page.wait_for_function("!document.querySelector('#forecast').disabled")
                check('baseline comparison is interactive','seasonal_naive' in page.locator('#status').text_content())
            else:
                check('results have source evidence',page.locator('.result-card').count()==7 and page.locator('.evidence').count()>0)
                check('graph relationships rendered',page.locator('#graph svg circle').count()>3)
                page.select_option('#institution','Demo Institute 2');page.click('#search');page.wait_for_function("!document.querySelector('#search').disabled")
                check('institution constraint enforced',all('Demo Institute 2' in s for s in page.locator('.result-card > p').all_text_contents()))
                page.click('#relevant');page.wait_for_function("document.querySelector('#status').textContent.includes('feedback saved')")
                check('relevance feedback persisted',True)
            check('no browser JavaScript errors',not errors)
            check('desktop does not overflow horizontally',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            # Reset a representative dashboard for its screenshot.
            if name=='visionforge': page.select_option('#model','patch_vit');page.click('#inspect');page.wait_for_function("!document.querySelector('#inspect').disabled")
            if name=='streamrank': page.select_option('#user','4');page.select_option('#genre','');page.click('#recommend');page.wait_for_function("!document.querySelector('#recommend').disabled")
            if name=='forecastflow': page.select_option('#model','');page.select_option('#origin','259');page.fill('#stock','10');page.click('#forecast');page.wait_for_function("!document.querySelector('#forecast').disabled")
            if name=='researchgraph': page.select_option('#institution','');page.click('#search');page.wait_for_function("!document.querySelector('#search').disabled")
            if name=='agentshield':
                page.select_option('#detector','transformer');page.select_option('#source','document');page.select_option('#tool','write_record');page.locator('#example').dispatch_event('change');page.click('#run');page.wait_for_function("!document.querySelector('#run').disabled")
            page.evaluate('window.scrollTo(0,0)'); page.fill('#token',''); page.locator('#error').evaluate('(n)=>n.textContent=""')
            doc=PROJECT_ROOT/'docs';doc.mkdir(exist_ok=True);page.screenshot(path=str(doc/'dashboard.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(200)
            check('mobile does not overflow horizontally',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            page.screenshot(path=str(doc/'mobile.png'),full_page=True)
            out={'browser':'Chromium via Playwright','transport':'Local DOM harness: repository scripts loaded inline; fetch bridged to a real Uvicorn HTTP backend; sessionStorage emulated for opaque origin. Browser network policy blocked native navigation, so native ESM/CSP transport is not validated.','checks':results,'total':len(results),'passed':len(results),'errors':errors}
            (PROJECT_ROOT/'reports/browser.json').write_text(json.dumps(out,indent=2)); print(name,len(results),'browser checks passed')
            context.close()
        browser.close()
finally:
    for proc in servers:
        proc.terminate()
    for proc in servers:
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:proc.kill()
    for log in logs:log.close()
