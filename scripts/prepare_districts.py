"""Read Final.xlsx only. Join named, reviewed historical units to fixed 2013 geometry.
Missing is None; zero stays zero. Geometry is approximate, never an invented count.
"""
import json, math
from pathlib import Path
from openpyxl import load_workbook
root=Path(__file__).resolve().parents[1]
source=root/'Final.xlsx'
w=load_workbook(source,read_only=True,data_only=True);s=w['데이터'];s.reset_dimensions();table=list(s.values)
years=[str(int(y)) for y in table[0][1:]]
base_path=root/'dist/data/population.json';base=json.load(open(base_path));regions=base['regions']
byname={r['kr']:r['code'] for r in regions};index={r['code']:i for i,r in enumerate(regions)}
def number(value):
 if value is None or str(value).strip() in ('','-'):return None
 value=float(value)
 assert value>=0 and value.is_integer(),value
 return int(value)
province=None;records={y:{} for y in years};national={};province_values={y:{} for y in years};raw=[]
for rownum,row in enumerate(table[2:],3):
 name=row[0].strip();values=[number(v) for v in row[1:]]
 if name=='전국':national=dict(zip(years,values));continue
 if row[0]==name:
  assert name in byname,('Unknown province',name)
  province=byname[name]
  for y,v in zip(years,values):province_values[y][province]=v
  if province!='29':continue
  name='세종시'
 assert province is not None
 # No inference of a gu's parent from row order. Names are kept as source province/name pairs.
 raw.append({'province':province,'name':name,'values':dict(zip(years,values)),'row':rownum})
 for y,v in zip(years,values):
  if v is None:continue
  key=province+':'+name
  if key in records[y]:
   assert province=='29' and records[y][key]['value']==v,('Ambiguous source name',y,key)
   continue
  records[y][key]={'value':v,'label':next(r['kr'] for r in regions if r['code']==province)+' '+name,'sourceKey':key,'sourceRows':[rownum],'province':index[province],'approximate':False}
for y in years:
 assert sum(v for v in province_values[y].values() if v is not None)==national[y]
 assert national[y]==base['years'][y]['total']
 for r in regions:assert province_values[y][r['code']]==base['years'][y]['regions'][index[r['code']]][0]
# Reuse existing cartogram meshes because every source population value is identical.
# Final.xlsx has totals only; do not present gender counts from a different workbook.
for y in years:
 base['years'][y]={'total':national[y],'regions':[[province_values[y][r['code']],None,None] for r in regions]}
base['source']={'file':source.name,'table':'DT_1B040A3','measure':'총인구수','meshReuse':'시도 인구 전 연도 일치 확인 후 기존 격자 재사용'}
geo_path=root/'dist/data/districts.geojson'
if geo_path.exists():geo=json.load(open(geo_path))
else:
 from urllib.request import urlopen
 with urlopen('https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_municipalities_geo_simple.json') as response:geo=json.load(response)
metro={'11','21','22','23','24','25','26'}
def get(rows,province,name):return rows.get(province+':'+name)
def approximate(rec,reason):return {**rec,'approximate':True,'reason':reason} if rec is not None else None
def combine(rows,province,names):
 parts=[get(rows,province,name) for name in names]
 if any(p is None for p in parts):return None
 return {'value':sum(p['value'] for p in parts),'label':' + '.join(p['label'] for p in parts),'sourceKey':'+'.join(p['sourceKey'] for p in parts),'sourceRows':sum((p['sourceRows'] for p in parts),[]),'province':index[province],'approximate':True,'reason':'과거 시·군의 전체 합계 / 고정 경계에 통합 표시'}
# Explicit, scoped relationships: no generic same-name matching between provinces.
promotions={'31':{'여주시':'여주군','양주시':'양주군','포천시':'포천군','광주시':'광주군','화성시':'화성군','김포시':'김포군','안성시':'안성군','이천시':'이천군','파주시':'파주군','용인시':'용인군'},'34':{'당진시':'당진군','논산시':'논산군','계룡시':'계룡출장소'},'33':{'증평군':'증평출장소'},'38':{'양산시':'양산군'}}
splits={('11','광진구'):'성동구',('11','강북구'):'도봉구',('11','금천구'):'구로구',('21','사상구'):'북구',('21','수영구'):'남구',('21','연제구'):'동래구',('23','계양구'):'북구',('23','부평구'):'북구',('23','연수구'):'남구',('24','남구'):'서구'}
mergers={'31':{'남양주시':['미금시','남양주군'],'평택시':['송탄시','평택시','평택군']},'34':{'공주시':['공주시','공주군'],'천안시':['천안시','천안군'],'보령시':['대천시','보령군'],'아산시':['온양시','아산군'],'서산시':['서산시','서산군']},'33':{'충주시':['충주시','중원군'],'제천시':['제천시','제천군']},'36':{'광양시':['동광양시','광양군'],'순천시':['순천시','승주군'],'나주시':['나주시','나주군']},'37':{'포항시':['포항시','영일군'],'경주시':['경주시','경주군'],'김천시':['김천시','금릉군'],'안동시':['안동시','안동군'],'구미시':['구미시','선산군'],'영주시':['영주시','영풍군'],'영천시':['영천시','영천군'],'상주시':['상주시','상주군'],'문경시':['점촌시','문경군'],'경산시':['경산시','경산군']},'38':{'진주시':['진주시','진양군'],'통영시':['충무시','통영군'],'사천시':['삼천포시','사천군'],'김해시':['김해시','김해군'],'밀양시':['밀양시','밀양군'],'거제시':['장승포시','거제군']}}
features=[]
for feature in geo['features']:
 p=feature['properties'];code=p['code'];province=code[:2];name=p['name'];values={}
 for year,rows in records.items():
  y=int(year);local=name
  if province not in metro and name.endswith('구') and '시' in name:local=name.rsplit('시',1)[0]+'시'
  rec=get(rows,province,local)
  if province=='26' and y<1997:
   # No identical whole-Ulsan total on five separate district features.
   if y<1995:
    old='울산군' if name=='울주군' else '울산시'
    rec=None if name=='북구' else approximate(get(rows,'38',old),'광역시 출범 전 경남의 시·군 / 2013 경계로 근사 표시')
   else:rec=approximate(get(rows,'38','울산시'),'광역시 출범 전 울산시 통합 영역 / 2013 경계로 근사 표시')
  if province=='38' and name.startswith('창원시') and y<2010:
   old='마산시' if '마산' in name else '진해시' if '진해' in name else '창원시'
   rec=approximate(get(rows,'38',old),'2010년 통합 전 시 단위 / 고정 경계로 근사 표시')
  if province=='33' and (name.startswith('청주시') or name=='청원군') and y>=2014:rec=approximate(get(rows,'33','청주시'),'청주·청원 통합 시 단위 / 고정 경계로 근사 표시')
  if province=='39' and y<2006 and name in ('제주시','서귀포시'):rec=combine(rows,'39',[name,'북제주군' if name=='제주시' else '남제주군'])
  if province=='36' and local=='여수시' and y<1998:rec=combine(rows,'36',['여수시','여천시','여천군'])
  if y<1995 and local in mergers.get(province,{}):rec=combine(rows,province,mergers[province][local])
  if rec is None and local in promotions.get(province,{}):rec=approximate(get(rows,province,promotions[province][local]),'승격 전 지역명 / 고정 경계로 근사 표시')
  if rec is None and (province,name) in splits and y<1995:rec=approximate(get(rows,province,splits[province,name]),'분구 전 상위 지역 / 통합 영역으로 표시')
  if province=='23' and name=='남구' and y>=2018:rec=get(rows,'23','미추홀구')
  if province=='23' and name in ('강화군','옹진군') and y<1995:rec=approximate(get(rows,'31',name),'인천 편입 전 경기도 소속 / 고정 경계로 표시')
  if province=='22' and name=='달성군' and y<1995:rec=approximate(get(rows,'37',name),'대구 편입 전 경북 소속 / 고정 경계로 표시')
  if province=='37' and name=='군위군' and y>=2023:rec=approximate(get(rows,'22',name),'대구 편입 후 소속 / 지도 경계는 2013년 기준')
  if rec is not None:values[year]=rec
 features.append({'type':'Feature','properties':{'code':code,'name':name,'province':index[province],'values':values},'geometry':feature['geometry']})
missing={y:[f['properties']['code']+':'+f['properties']['name'] for f in features if y not in f['properties']['values']] for y in years}
assert all(not (f['properties']['code'].startswith('26') and int(y)<1997 and '+' in rec['sourceKey']) for f in features for y,rec in f['properties']['values'].items())
maximum=max(rec['value'] for f in features for rec in f['properties']['values'].values())
metadata={'firstYear':1992,'lastYear':2025,'boundaryYear':2013,'source':'KOSIS 주민등록인구현황, 연말 총인구수, 외국인 제외','files':[source.name],'maxPopulation':maximum,'missing':missing,'missingPolicy':'hide','notes':['2010년부터 거주불명 등록자 포함','2013년 고정 경계로 과거 구역 근사 표시','자료 없음은 숨김, 숫자 0은 보존','2026년 주석은 기간 밖이므로 미적용','부산에 붙은 1997년 승격 주석은 표와 충돌하므로 미적용']}
geo_path.write_text(json.dumps({'type':'FeatureCollection','features':features,'metadata':metadata},ensure_ascii=False,separators=(',',':')))
base_path.write_text(json.dumps(base,ensure_ascii=False,separators=(',',':')))
(root/'dist/data/source-records.json').write_text(json.dumps({'source':source.name,'years':years,'regions':regions,'national':national,'rows':raw},ensure_ascii=False,separators=(',',':')))
print('Final.xlsx: 34 national/province totals verified; original cartogram meshes retained.')
print('Geometry parts:',len(features),'max population:',maximum)
print('Missing parts in 1992:',missing['1992'])
print('Source zero values preserved:',sum(v==0 for r in raw for v in r['values'].values()))
