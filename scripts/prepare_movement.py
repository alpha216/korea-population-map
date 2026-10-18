"""Export Movement.xlsx totals without interpolation; validate inflow-outflow=net."""
import json,math
from pathlib import Path
from openpyxl import load_workbook
root=Path(__file__).resolve().parents[1];source=root/'Movement.xlsx'
w=load_workbook(source,read_only=True,data_only=True);s=w['데이터'];s.reset_dimensions();rows=list(s.values)
base=json.load(open(root/'dist/data/population.json'));lookup={r[0]:r for r in rows[2:]};years={}
def num(v):return None if v is None or str(v).strip() in ('','-') else int(v)
for j in range(1,len(rows[0]),3):
 year=str(rows[0][j]);regions=[]
 for region in base['regions']:
  row=lookup[region['kr']];values=[num(v) for v in row[j:j+3]]
  assert all(v is None for v in values) or all(v is not None for v in values)
  if values[0] is not None:assert values[0]-values[1]==values[2]
  regions.append(values)
 national=[num(v) for v in lookup['전국'][j:j+3]]
 assert sum(v[0] or 0 for v in regions)==national[0]
 assert sum(v[1] or 0 for v in regions)==national[1]
 assert sum(v[2] or 0 for v in regions)==0==national[2]
 years[year]={'regions':regions,'national':national}
maximum=max(abs(v[2]) for r in years.values() for v in r['regions'] if v[2] is not None)
out={'source':{'file':source.name,'table':'DT_1B26001_A01','title':'시군구별 이동자수','publisher':'국내인구이동통계, 국가데이터처'},'columns':['inflow','outflow','net'],'years':years,'maxAbsNet':maximum,'colorLimit':math.ceil(maximum/50000)*50000}
(root/'dist/data/movement.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
print('Verified 34 years: each net=inflow-outflow; provincial sums match national; national net zero.')
print('Maximum absolute net:',maximum,'symmetric scale:',out['colorLimit'])
