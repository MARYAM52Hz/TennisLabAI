import sys,os,runpy
sys.argv=['x','plan']; sys.path.insert(0,'/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad/ana')
g=runpy.run_path('/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad/ana/'+'build'+'2.py',run_name='lib')
START,N=g['START'],g['N']; SP=g['SP']; n=0
for seg in ('long','stype'):
    for i in range(N[seg]):
        for l in ('fa','en'):
            p=f'{SP}/fin2_{l}/f{START[seg]+i:05d}.png'
            if os.path.exists(p): os.remove(p); n+=1
print('removed',n)
