"""Replay only the file-producing parts (heredoc writes, python patch heredocs, sed -i) of selected saved commands, in order."""
import json,re,subprocess,sys,os
NEW='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
OLDS=['/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad','/tmp/claude-0/-home-claude/813f700f-0243-50f8-b2f1-bbd385cfaf4f/scratchpad']
cmds=json.load(open(NEW+'/rest/cmds.json')); d={c[0]:c for c in cmds}
def fix(t):
    for o in OLDS: t=t.replace(o,NEW)
    return t.replace('/root/.claude/uploads/c5f26e6b-ec2e-54ad-a30c-648653015475/','/mnt/user-data/attachments/2a0f4416-55f7-5d66-babf-bfd62e72f7df/')
HD=re.compile(r"(?P<head>[^\n]*?)<<\s*'?(?P<tag>\w+)'?[^\n]*\n(?P<body>.*?)\n(?P=tag)\n?",re.S)
for a in sys.argv[1:]:
    i=int(a); n,inp=d[i][1],d[i][2]
    if n=='Write':
        p=fix(inp['file_path']); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w').write(fix(inp['content'])); print(i,'write',p); continue
    c=fix(inp['command'])
    for m in HD.finditer(c):
        head,body=m.group('head'),m.group('body'); mc=re.search(r"cat\s*>\s*(\S+)\s*$",head.strip())
        if mc:
            p=mc.group(1); p=p if p.startswith('/') else os.path.join(NEW,p); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w').write(body+'\n'); print(i,'cat >',p)
        elif re.search(r"python3?\b.*-\s*$",head.strip()) or head.strip().endswith('python3 -I -') or 'python3' in head:
            r=subprocess.run(['python3','-I','-'],input=body,text=True,capture_output=True,cwd=NEW); print(i,'py patch rc',r.returncode,(r.stdout+r.stderr)[-300:])
    for m in re.finditer(r"sed -i (\"[^\"]*\"|'[^']*') (\S+)",c):
        r=subprocess.run(f"sed -i {m.group(1)} {m.group(2)}",shell=True,capture_output=True,text=True,cwd=NEW); print(i,'sed',m.group(2),r.returncode,r.stderr[-200:])
