from pathlib import Path
import pandas as pd,json,sqlite3
from ingest import METRICS
ROOT=Path(__file__).resolve().parents[1]
def main():
 f=pd.read_csv(ROOT/'data/fact_airport_month.csv.gz');a=pd.read_csv(ROOT/'data/dim_airports.csv')[['airport','city','state']];geo=pd.read_csv(ROOT/'data/reference/airports_coordinates.csv');geo['priority']=geo.type.map({'large_airport':0,'medium_airport':1,'small_airport':2,'closed':3}).fillna(4);geo=geo.sort_values(['priority','id']).dropna(subset=['iata_code']).drop_duplicates('iata_code')
 a=a.merge(geo[['iata_code','name','latitude_deg','longitude_deg']],left_on='airport',right_on='iata_code',how='left').drop(columns='iata_code').rename(columns={'latitude_deg':'latitude','longitude_deg':'longitude'});a['name']=a.name.fillna(a.city+' ('+a.airport+')');a.to_csv(ROOT/'data/dim_airports.csv',index=False);a[a.latitude.isna()].to_csv(ROOT/'reports/unmapped_airports.csv',index=False)
 c=f[['carrier_id','carrier']].drop_duplicates();assert not c.carrier_id.duplicated().any();names=json.loads((ROOT/'data/reference/carrier_names.json').read_text());c['name']=c.carrier.map(names).fillna(c.carrier);c.to_csv(ROOT/'data/dim_carriers.csv',index=False)
 keys=['year','month','carrier_id','airport'];assert not f.duplicated(keys).any();assert f[keys].notna().all().all();assert len(f[['year','month']].drop_duplicates())==180;assert set(f.year)==set(range(2010,2025));assert (f[METRICS]>=0).all().all();assert (f.severe<=f.delayed).all() and (f.delayed<=f.eligible).all();assert (f.flights==f[['eligible','cancelled','diverted','unknown']].sum(axis=1)).all();assert not a.airport.duplicated().any()
 manifest=json.loads((ROOT/'data/source_manifest.json').read_text());assert len(manifest)==180
 for r in manifest:assert f.loc[f.year.eq(r['year'])&f.month.eq(r['month']),'flights'].sum()==r['flight_rows']
 con=sqlite3.connect(ROOT/'data/airline_warehouse.sqlite')
 for name,d in [('fact_airport_month',f),('dim_airports',a),('dim_carriers',c)]:d.to_sql(name,con,if_exists='replace',index=False)
 con.executescript('CREATE UNIQUE INDEX IF NOT EXISTS fact_grain ON fact_airport_month(year,month,carrier_id,airport); CREATE INDEX IF NOT EXISTS airport_idx ON fact_airport_month(airport);')
 out=ROOT/'reports/query_results';out.mkdir(exist_ok=True);qs=[]
 for i,sql in enumerate((ROOT/'sql/analysis.sql').read_text().split('-- QUERY'),1):
  d=pd.read_sql_query(sql,con);d.to_csv(out/f'query_{i:02}.csv',index=False);qs.append(d)
 for keys,q in [(['year'],qs[0]),(['year','month'],qs[1]),(['airport'],qs[2]),(['carrier_id'],qs[3])]:
  p=f.groupby(keys)[METRICS].sum();p['delay_rate']=p.delayed/p.eligible;p['cancel_rate']=p.cancelled/p.flights;j=q.set_index(keys).join(p,rsuffix='_p')
  for k in ['flights','eligible','delayed','cancelled','delay_rate','cancel_rate']:assert ((j[k]-j[k+'_p']).abs()<1e-9).all()
 s=f[METRICS].sum();k={x:int(s[x]) for x in METRICS};k.update({'delay_rate':s.delayed/s.eligible,'on_time_rate':1-s.delayed/s.eligible,'cancel_rate':s.cancelled/s.flights,'mean_late_minutes':s.delay_minutes/s.delayed,'aggregate_rows':len(f),'airports':len(a),'carriers':len(c),'mapped_airports':int(a.latitude.notna().sum()),'raw_bytes':sum(x['bytes'] for x in manifest)})
 (ROOT/'reports/metrics.json').write_text(json.dumps(k,indent=2));(ROOT/'reports/validation.txt').write_text('PASS: 180 monthly source files and source-flight totals reconciled.\nPASS: unique fact grain and unique dimension keys.\nPASS: additive measures are non-negative.\nPASS: severe <= delayed <= eligible.\nPASS: eligible + cancelled + diverted + unknown = scheduled flights.\nPASS: SQL annual/monthly/airport/carrier results match independent pandas aggregates to 1e-9.\nMap coverage: '+str(k['mapped_airports'])+' / '+str(k['airports'])+' airports.\n')
 f.to_csv(ROOT/'data/fact_airport_month.csv',index=False);print(json.dumps(k,indent=2));con.close()
if __name__=='__main__':main()
