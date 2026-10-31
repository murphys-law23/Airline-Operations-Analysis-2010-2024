from pathlib import Path
import json,pandas as pd
from ingest import METRICS
ROOT=Path(__file__).resolve().parents[1]
def main():
 f=pd.read_csv(ROOT/'data/fact_airport_month.csv.gz');a=pd.read_csv(ROOT/'data/dim_airports.csv');c=pd.read_csv(ROOT/'data/dim_carriers.csv')
 for k in METRICS:assert (f[k]%1==0).all();f[k]=f[k].astype('int64')
 values={'__DATA__':f[['year','month','carrier_id','airport']+METRICS].values.tolist(),'__AIRPORTS__':json.loads(a.set_index('airport').to_json(orient='index')),'__CARRIERS__':json.loads(c.set_index('carrier_id').to_json(orient='index')),'__LAND__':json.loads((ROOT/'data/reference/basemap.geojson').read_text()),'__METRICS__':METRICS}
 s=(ROOT/'dashboard/template.html').read_text()
 for k,v in values.items():s=s.replace(k,json.dumps(v,separators=(',',':'),allow_nan=False).replace('</','<\\/'))
 (ROOT/'dashboard/index.html').write_text(s);print('Built offline dashboard:',len(s),'characters')
if __name__=='__main__':main()
