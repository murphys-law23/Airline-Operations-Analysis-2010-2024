from pathlib import Path
import urllib.request,json,re,hashlib,pandas as pd
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
URLS={'airports.csv':'https://davidmegginson.github.io/ourairports-data/airports.csv','countries.json':'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson','bts.html':'https://www.transtats.bts.gov/OT_Delay/OT_DelayCause1.asp'}
def get(k,u):
 p=ROOT/'data/reference'/k
 if not p.exists():p.write_bytes(urllib.request.urlopen(u,timeout=120).read())
 print(k,p.stat().st_size,flush=True)
def main():
 with ThreadPoolExecutor(3) as ex:list(ex.map(lambda kv:get(*kv),URLS.items()))
 p=ROOT/'data/reference';a=pd.read_csv(p/'airports.csv');a=a[a.iso_country.isin(['US','PR','VI','GU','MP','AS'])];a[['id','type','name','latitude_deg','longitude_deg','iso_country','iata_code','local_code']].to_csv(p/'airports_coordinates.csv',index=False)
 g=json.loads((p/'countries.json').read_text());g['features']=[x for x in g['features'] if x['properties']['ADMIN'] in ['United States of America','Canada','Mexico','Cuba','Puerto Rico','Dominican Republic','Haiti','The Bahamas']];(p/'basemap.geojson').write_text(json.dumps(g,separators=(',',':')))
 s=(p/'bts.html').read_text();sel=re.search(r'<select[^>]+name=[\'"]?Carrier.*?</select>',s,re.I|re.S).group(0);rows=re.findall(r'<OPTION\s+VALUE\s*=\s*([^>]+)>([^<]+)',sel,re.I);names={}
 for val,name in rows:
  code=val.split('::')[0].strip("'\"")
  if code=='All':continue
  name=re.sub(r'\s*\([^)]*\)$','',name)
  if code in names and name not in names[code]:names[code]+=' / '+name
  else:names.setdefault(code,name)
 (p/'carrier_names.json').write_text(json.dumps(names,indent=2));(p/'sources.json').write_text(json.dumps([{'file':k,'url':u,'retrieved':'2026-10-30','sha256':hashlib.sha256((p/k).read_bytes()).hexdigest()} for k,u in URLS.items()],indent=2))
if __name__=='__main__':main()
