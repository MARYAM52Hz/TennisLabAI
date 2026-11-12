import json,sys,subprocess,os
NEW='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
OLD='/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
UP_OLD='/root/.claude/uploads/c5f26e6b-ec2e-54ad-a30c-648653015475/'
UP_NEW='/mnt/user-data/attachments/2a0f4416-55f7-5d66-babf-bfd62e72f7df/'
cmds=json.load(open(NEW+'/rest/cmds.json'))
d={i:inp.get('command') for i,n,inp in cmds if n=='Bash'}
STRIP=('(setsid nohup python3 -I lab2/ball_lab.py','python3 -I lab2/ball_lab.py')
for a in sys.argv[1:]:
    i=int(a); c=d[i].replace(OLD,NEW).replace(UP_OLD,UP_NEW)
    c='\n'.join(l for l in c.split('\n') if not any(l.strip().startswith(s) for s in STRIP))
    print('##### replay',i,flush=True)
    r=subprocess.run(['bash','-c',c],capture_output=True,text=True,cwd=NEW)
    print((r.stdout+r.stderr)[-2500:],flush=True)
    print('rc',r.returncode,flush=True)
