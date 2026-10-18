"""Build annual population data and an approximate diffusion cartogram mesh.
Source counts remain exact; spatial allocation uses fixed 2013 provincial polygons.
"""
import json, math, unicodedata
from pathlib import Path
import numpy as np
from openpyxl import load_workbook
root=Path(__file__).resolve().parents[1]
population_source=root/'Final.xlsx'
w=load_workbook(population_source,read_only=True,data_only=True)
s=w['데이터'];s.reset_dimensions();rows=list(s.values)
names=['Jeju','South Gyeongsang','North Gyeongsang','South Jeolla','North Jeolla','South Chungcheong','North Chungcheong','Gangwon','Gyeonggi','Sejong','Ulsan','Daejeon','Gwangju','Incheon','Daegu','Busan','Seoul']
codes=['39','38','37','36','35','34','33','32','31','29','26','25','24','23','22','21','11']
kr_names=['제주특별자치도','경상남도','경상북도','전라남도','전북특별자치도','충청남도','충청북도','강원특별자치도','경기도','세종특별자치시','울산광역시','대전광역시','광주광역시','인천광역시','대구광역시','부산광역시','서울특별시']
province_rows={r[0]:r for r in rows[2:] if r[0] in kr_names or r[0]=='전국'}
data={}
for j,year in enumerate(rows[0][1:],1):
 values=[[int(province_rows[name][j]) if isinstance(province_rows[name][j],(int,float)) else None,None,None] for name in kr_names]
 total=int(province_rows['전국'][j]);assert sum(v[0] or 0 for v in values)==total
 data[str(int(year))]={'total':total,'regions':values}
geo=json.load(open(root/'dist/data/boundaries.geojson'))
features=geo['features'];features.sort(key=lambda f:codes.index(f['properties']['code']))
# Equal-distance local approximation: longitude scaled by cos(36 degrees).
N=128;H=176;cos=math.cos(math.radians(36));bounds=[124,131,32,40]
def project(a):
 a=np.asarray(a);return np.stack(((a[...,0]-124)/7*(N-1),(40-a[...,1])/8*(H-1)),axis=-1)
# Raster coordinates use equal physical scale in x and y to within 1%.
# 7 degrees longitude * cos36 ~= 5.66 degrees; 8 latitude / 5.66 *128 ~=181.
xx,yy=np.meshgrid(np.arange(N),np.arange(H));owner=np.full((H,N),-1,dtype=int)
def inside(ring):
 ring=project(ring);mask=np.zeros((H,N),bool)
 for a,b in zip(ring,np.roll(ring,-1,axis=0)):
  if a[1]==b[1]:continue
  mask^=((a[1]>yy)!=(b[1]>yy)) & (xx<(b[0]-a[0])*(yy-a[1])/(b[1]-a[1])+a[0])
 return mask
for i,f in enumerate(features):
 polys=f['geometry']['coordinates'];polys=polys if f['geometry']['type']=='MultiPolygon' else [polys]
 for poly in polys:
  mask=inside(poly[0])
  for hole in poly[1:]:mask&=~inside(hole)
  owner[mask]=i
counts=np.array([(owner==i).sum() for i in range(17)])
assert (counts>0).all(),counts
# Bilinear interpolation on the Eulerian density/velocity raster.
def sample(a,p):
 x=np.clip(p[:,0],0,N-1.000001);y=np.clip(p[:,1],0,H-1.000001);ix=x.astype(int);iy=y.astype(int);u=x-ix;v=y-iy
 return (1-v)*((1-u)*a[iy,ix]+u*a[iy,ix+1])+v*((1-u)*a[iy+1,ix]+u*a[iy+1,ix+1])
mx,my=np.meshgrid(np.linspace(0,N-1,65),np.linspace(0,H-1,89));initial=np.stack((mx.ravel(),my.ravel()),axis=1)
kx=2*np.pi*np.fft.fftfreq(N)[None,:];ky=2*np.pi*np.fft.fftfreq(H)[:,None];k2=kx*kx+ky*ky
meshes={};minimum=1
for year,record in data.items():
 pops=np.array([r[0] or 0 for r in record['regions']],float)
 # Pool areas for units not yet independently reported; no missing count is invented.
 density=pops/counts
 if int(year)<1997:density[1]=density[10]=pops[1]/(counts[1]+counts[10])
 if int(year)<2012:density[5]=density[9]=pops[5]/(counts[5]+counts[9])
 rho=np.full((H,N),record['total']/sum(counts))
 for i in range(17):rho[owner==i]=density[i]
 # Smooth subpixel discontinuities before integrating diffusion flow.
 spectrum=np.fft.fft2(rho)*np.exp(-k2*.8)
 p=initial.copy();t=0.;steps=0
 while t<8000:
  ft=spectrum*np.exp(-k2*t);r=np.fft.ifft2(ft).real
  vx=-np.fft.ifft2(ft*(1j*kx)).real/np.maximum(r,1)
  vy=-np.fft.ifft2(ft*(1j*ky)).real/np.maximum(r,1)
  speed=max(np.max(np.abs(vx)),np.max(np.abs(vy)),1e-8)
  dt=min(.18/speed,max(.08,.04*(t+1)),8000-t)
  p+=dt*np.stack((sample(vx,p),sample(vy,p)),axis=1);t+=dt;steps+=1
 mesh=p.reshape(89,65,2);dx=mesh[:-1,1:]-mesh[:-1,:-1];dy=mesh[1:,:-1]-mesh[:-1,:-1]
 jac=dx[...,0]*dy[...,1]-dx[...,1]*dy[...,0];minimum=min(minimum,float(jac.min()))
 assert np.isfinite(mesh).all() and jac.min()>0,(year,jac.min())
 meshes[year]=np.round(p,3).tolist()
 print(year,'steps',steps,'minimum cell area',round(float(jac.min()),4),flush=True)
out={'regions':[{'name':n,'kr':kr,'code':c} for n,kr,c in zip(names,kr_names,codes)],'years':data,'meshes':meshes,'meshWidth':65,'meshHeight':89,'rasterWidth':N,'rasterHeight':H,'bounds':bounds,'minimumCellArea':minimum}
(root/'dist/data/population.json').write_text(json.dumps(out,separators=(',',':'),ensure_ascii=False))
(root/'dist/data/boundaries.geojson').write_text(json.dumps(geo,separators=(',',':'),ensure_ascii=False))
print('All annual totals reconcile. All mesh cell orientations positive.')
