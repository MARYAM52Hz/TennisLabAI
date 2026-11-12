import sys,runpy,cv2
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
sys.argv=['x','plan']; g=runpy.run_path(SP+'/ana/build'+'2.py',run_name='lib'); S=g['START']; N=g['N']
print(S)
want=[('freezeB',N['freezeB']-170,'en'),('verdict',N['verdict']-40,'fa'),('sources',100,'en'),('model',200,'fa'),('freezeA',90,'fa')]
for seg,i,l in want:
    im=cv2.imread(f'{SP}/fin2_{l}/f{S[seg]+i:05d}.png'); cv2.imwrite(f'{SP}/chk/p_{seg}_{l}.png',im)
