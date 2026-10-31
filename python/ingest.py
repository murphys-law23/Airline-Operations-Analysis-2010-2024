"""Reproducible BTS download and chunked aggregation. Raw archives are not shipped in Git."""
from pathlib import Path
import pandas as pd,urllib.request,json,zipfile,hashlib,shutil,time,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1]
METRICS=['flights','cancelled','diverted','eligible','delayed','severe','unknown','delay_minutes','carrier_minutes','weather_minutes','nas_minutes','security_minutes','late_aircraft_minutes']
COLS=['Year','Month','Reporting_Airline','DOT_ID_Reporting_Airline','Dest','DestCityName','DestState','Cancelled','Diverted','ArrDelay','CarrierDelay','WeatherDelay','NASDelay','SecurityDelay','LateAircraftDelay']
def transform(d):
 e=d.Cancelled.eq(0)&d.Diverted.eq(0)&d.ArrDelay.notna();late=e&d.ArrDelay.ge(15)
 x=pd.DataFrame({'year':d.Year.astype(int),'month':d.Month.astype(int),'carrier':d.Reporting_Airline,'carrier_id':d.DOT_ID_Reporting_Airline.astype(int),'airport':d.Dest})
 x['flights']=1;x['cancelled']=d.Cancelled.astype(int);x['diverted']=(d.Diverted.eq(1)&d.Cancelled.eq(0)).astype(int);x['eligible']=e.astype(int);x['delayed']=late.astype(int);x['severe']=(e&d.ArrDelay.ge(60)).astype(int);x['unknown']=(~e&d.Cancelled.eq(0)&d.Diverted.eq(0)).astype(int);x['delay_minutes']=d.ArrDelay.where(late,0).fillna(0)
 for a,b in [('CarrierDelay','carrier'),('WeatherDelay','weather'),('NASDelay','nas'),('SecurityDelay','security'),('LateAircraftDelay','late_aircraft')]:x[b+'_minutes']=pd.to_numeric(d[a],errors='coerce').where(late,0).fillna(0)
 return x

def process(y,m):
 tag=f'{y}_{m:02}';out=ROOT/'data/monthly';raw=ROOT/'data/raw';out.mkdir(parents=True,exist_ok=True);raw.mkdir(parents=True,exist_ok=True);meta=out/(tag+'.json')
 if meta.exists():
  info=json.loads(meta.read_text())
  try:
   cached=pd.read_csv(out/(tag+'.csv.gz'))
   if len(cached)==info['aggregate_rows'] and cached.flights.sum()==info['flight_rows']:return info
  except (OSError,ValueError):pass
  meta.unlink()
 url=f'https://www.transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip';zp=raw/(tag+'.zip')
 for attempt in range(3):
  try:
   if not zp.exists():
    with urllib.request.urlopen(url,timeout=150) as r,open(str(zp)+'.part','wb') as f:shutil.copyfileobj(r,f)
    Path(str(zp)+'.part').replace(zp)
   parts=[];dims=[];rows=0
   with zipfile.ZipFile(zp) as z:
    with z.open(next(n for n in z.namelist() if n.endswith('.csv'))) as f:
     for d in pd.read_csv(f,usecols=COLS,chunksize=150000,low_memory=False):
      assert d.Year.eq(y).all() and d.Month.eq(m).all()
      x=transform(d);parts.append(x.groupby(['year','month','carrier','carrier_id','airport'])[METRICS].sum());dims.append(d[['Dest','DestCityName','DestState']].drop_duplicates());rows+=len(d)
      if y==2024 and m==1 and rows==len(d):d.head(1000).to_csv(ROOT/'data/flight_sample.csv',index=False)
   a=pd.concat(parts).groupby(level=[0,1,2,3,4]).sum().reset_index();assert a.flights.sum()==rows;assert (a.flights==a[['eligible','cancelled','diverted','unknown']].sum(axis=1)).all();a.to_csv(out/(tag+'.csv.gz'),index=False)
   pd.concat(dims).drop_duplicates().to_csv(out/(tag+'_airports.csv'),index=False)
   with zp.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
   info={'year':y,'month':m,'url':url,'sha256':sha,'bytes':zp.stat().st_size,'flight_rows':rows,'aggregate_rows':len(a),'retrieved_utc':pd.Timestamp.now(tz='UTC').isoformat()};meta.write_text(json.dumps(info,indent=2));print(tag,rows,flush=True);return info
  except Exception as e:
   print(tag,'retry',attempt+1,str(e),flush=True)
   if isinstance(e,zipfile.BadZipFile):zp.unlink(missing_ok=True)
   if attempt==2:raise
   time.sleep(2)
def main():
 p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=6);a=p.parse_args();results=[]
 with ThreadPoolExecutor(a.workers) as ex:
  fs=[ex.submit(process,y,m) for y in range(2010,2025) for m in range(1,13)]
  for f in as_completed(fs):results.append(f.result())
 results.sort(key=lambda r:(r['year'],r['month']));(ROOT/'data/source_manifest.json').write_text(json.dumps(results,indent=2))
 tags=[f"{r['year']}_{r['month']:02}" for r in results];d=pd.concat([pd.read_csv(ROOT/'data/monthly'/(t+'.csv.gz')) for t in tags],ignore_index=True);d.to_csv(ROOT/'data/fact_airport_month.csv.gz',index=False)
 dims=pd.concat([pd.read_csv(ROOT/'data/monthly'/(t+'_airports.csv')) for t in tags]).drop_duplicates('Dest',keep='last');dims.columns=['airport','city','state'];dims.to_csv(ROOT/'data/dim_airports.csv',index=False);print('COMPLETE',len(d),int(d.flights.sum()),flush=True)
if __name__=='__main__':main()
