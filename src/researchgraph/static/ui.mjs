export const $ = id => document.getElementById(id);
export const fmt = (value,digits=2) => Number.isFinite(Number(value)) ? Number(value).toLocaleString('en-US',{maximumFractionDigits:digits}) : '—';
export const percent = value => `${fmt(100*value,1)}%`;
export const shortId = text => String(text).slice(0,12);
export function el(tag, text='', cls='') { const node=document.createElement(tag); node.textContent=String(text); if(cls)node.className=cls; return node; }
export function clear(id){ const node=typeof id==='string'?$(id):id; node.replaceChildren(); return node; }
export function option(select,value,text){const node=el('option',text); node.value=String(value); select.append(node);return node;}
export function state(message,error=false){$('status').textContent=message;$('status').classList.toggle('error',error);}
export async function api(path,body,method){
 const token=sessionStorage.getItem('demoToken')||$('token').value.trim();
 const headers={Authorization:`Bearer ${token}`}; const options={headers};
 if(body!==undefined){options.method=method||'POST'; if(body instanceof FormData)options.body=body; else{headers['Content-Type']='application/json';options.body=JSON.stringify(body);}}
 const response=await fetch(path,options);
 const data=await response.json(); if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail||data)); return data;
}
export async function busy(button,operation){button.disabled=true;try{await operation();}catch(e){state(e.message,true);$('error').textContent=e.message;}finally{button.disabled=false;}}
export function wireConnect(load){
 $('connect').onclick=()=>busy($('connect'),async()=>{sessionStorage.setItem('demoToken',$('token').value.trim());await load();state('Connected · local model ready');$('error').textContent='';});
 $('disconnect').onclick=()=>{sessionStorage.removeItem('demoToken');$('token').value='';state('Session cleared');};
 const saved=sessionStorage.getItem('demoToken'); if(saved){$('token').value=saved;$('connect').click();}
}
export function stats(values){const root=clear('stats'); for(const [label,value,detail]of values){const card=el('div','','stat');card.append(el('div',label,'label'),el('div',value,'value'),el('div',detail||'','detail'));root.append(card);}}
export function report(data){$('report-json').textContent=JSON.stringify(data,null,2);}
export function metricTable(rows,headers){const root=clear('metric-table');const table=el('table');const head=el('tr');headers.forEach(h=>head.append(el('th',h)));const thead=el('thead');thead.append(head);table.append(thead);const tbody=el('tbody');rows.forEach(row=>{const tr=el('tr');row.forEach(v=>tr.append(el('td',v)));tbody.append(tr);});table.append(tbody);root.append(table);}
export function svg(tag,attrs={}){const n=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));return n;}
export function seriesPath(points,x,y){let drawing=false;return points.map((v,i)=>{if(v===null||v===undefined||!Number.isFinite(v)){drawing=false;return '';}const out=`${drawing?'L':'M'}${x(i).toFixed(2)},${y(v).toFixed(2)}`;drawing=true;return out;}).join(' ');}
export function lineChart(target,series,{band=null,labels=[]}={}){
 const root=clear(target);const W=760,H=280,left=42,right=20,top=18,bottom=35;
 const all=series.flatMap(s=>s.values.filter(v=>v!==null&&Number.isFinite(v))).concat(band?band.flat():[]);const max=Math.max(...all,1)*1.1;const n=Math.max(...series.map(s=>s.values.length),2);
 const x=i=>left+i/(n-1)*(W-left-right),y=v=>H-bottom-v/max*(H-top-bottom);const chart=svg('svg',{viewBox:`0 0 ${W} ${H}`,class:'chart',role:'img','aria-label':'Forecast chart with history and prediction interval'});
 for(let j=0;j<=4;j++){const value=max*j/4;chart.append(svg('line',{x1:left,x2:W-right,y1:y(value),y2:y(value),stroke:'#2a374b','stroke-width':1}));const text=svg('text',{x:left-6,y:y(value)+4,'text-anchor':'end'});text.textContent=fmt(value,0);chart.append(text);}
 if(band){const a=band[0].map((v,i)=>v===null?null:[x(i),y(v)]).filter(Boolean);const b=band[1].map((v,i)=>v===null?null:[x(i),y(v)]).filter(Boolean).reverse();chart.append(svg('polygon',{points:[...a,...b].map(p=>p.join(',')).join(' '),fill:'#47788c',opacity:.32}));}
 for(const s of series)chart.append(svg('path',{d:seriesPath(s.values,x,y),fill:'none',stroke:s.color||'var(--accent)','stroke-width':2.5,'stroke-dasharray':s.dash?'5 4':''}));
 for(let i=0;i<labels.length;i+=Math.max(1,Math.ceil(labels.length/6))){const text=svg('text',{x:x(i),y:H-10,'text-anchor':'middle'});text.textContent=labels[i];chart.append(text);}
 root.append(chart);
}
export function graphChart(target,graph){const root=clear(target);const chart=svg('svg',{viewBox:'0 0 440 280',class:'graph',role:'img','aria-label':'Publication and author relationship graph'});const positions=new Map();graph.nodes.forEach((n,i)=>{const angle=i/(graph.nodes.length||1)*Math.PI*2;positions.set(n.id,[220+Math.cos(angle)*160,140+Math.sin(angle)*105]);});for(const edge of graph.edges){const a=positions.get(edge.source),b=positions.get(edge.target);if(a&&b)chart.append(svg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'#3b4d62','stroke-width':1}));}for(const node of graph.nodes){const [x,y]=positions.get(node.id);const circle=svg('circle',{cx:x,cy:y,r:node.kind==='author'?7:4,opacity:node.kind==='work'?.6:1});const title=svg('title');title.textContent=node.label;circle.append(title);chart.append(circle);if(node.kind==='author'||node.kind==='institution'){const label=svg('text',{x,y:y+16,'text-anchor':'middle'});label.textContent=node.label.slice(0,24);chart.append(label);}}root.append(chart);}
