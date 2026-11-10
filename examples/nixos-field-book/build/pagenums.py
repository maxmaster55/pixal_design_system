import json,subprocess,sys
from bs4 import BeautifulSoup
pdf,W=sys.argv[1],sys.argv[2]
txt=subprocess.run(['pdftotext',pdf,'-'],capture_output=True,text=True).stdout.split('\f')
norm=lambda s:''.join(s.split()).lower()
P=[norm(t) for t in txt]
soup=BeautifulSoup(open(W+'/book.html').read(),'html.parser')
out={}
start=2
for sec in soup.select('section.flow, section.partwrap'):
    sid=sec['id']
    if sid=='part-0': out[sid]=2; continue
    t=norm(sec.select_one('.partno').get_text()+sec.select_one('.chap-h').get_text())
    for i in range(start,len(P)):
        if t in P[i]: out[sid]=i+1; start=i+1; break
start=1
for h in soup.select('h2.chap'):
    t=norm(h.get_text(' '))[:40]
    for i in range(start,len(P)):
        if t in P[i]: out[h['id']]=i+1; start=i; break
    else:
        title=norm(h.get_text(' ')).split('chapter',1)[-1].lstrip('0123456789')[:30]
        openers=set(v-1 for k,v in out.items() if k.startswith('part-'))
        for i in range(start,len(P)):
            if i in openers: continue
            if title in P[i]: out[h['id']]=i+1; start=i; break
        else: print('miss',t)
json.dump(out,open(W+'/pagenums.json','w'),indent=0)
print(len(out))
