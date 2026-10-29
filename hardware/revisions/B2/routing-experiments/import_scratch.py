import argparse,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
p=Path(__file__).parent;ap=argparse.ArgumentParser();ap.add_argument('base');ap.add_argument('ses');ap.add_argument('out');a=ap.parse_args()
source=p/a.base;dest=p/a.out;b=k.LoadBoard(str(source));assert k.ImportSpecctraSES(b,str(p/a.ses));b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
print(dest)
