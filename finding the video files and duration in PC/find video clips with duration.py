from moviepy.editor import VideoFileClip
import os
import os.path
import pandas as pd
lf=[]
ld=[]
for dirpath,dirnames,filenames in os.walk("folder location"):
    for filename in [f for f in filenames if f.endswith(".mp4")]:
        fv=os.path.join(dirpath,filename)
        print(fv)
        clip = VideoFileClip(fv)
        duration=round(clip.duration/60,2)
        lf.append(filename)
        ld.append(duration)
        print(filename,duration)

vd={'Video':lf,'Duration':ld}


df = pd.DataFrame(vd,columns=['Video','Duration'])
print(df)
df.to_csv('C:/Users/vvbr1/Desktop/Data science/videosduration.csv',index = None, header=True)

