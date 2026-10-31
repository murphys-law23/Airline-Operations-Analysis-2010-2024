from pathlib import Path
import json,contextlib,io,base64,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def main():
 cells=[];env={};count=0
 def md(s):cells.append({'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)})
 def code(s):
  nonlocal count
  count+=1;o=io.StringIO()
  with contextlib.redirect_stdout(o):exec(s,env)
  outputs=[]
  if o.getvalue():outputs.append({'output_type':'stream','name':'stdout','text':o.getvalue().splitlines(keepends=True)})
  for n in plt.get_fignums():
   buf=io.BytesIO();plt.figure(n).savefig(buf,format='png',dpi=110,bbox_inches='tight');outputs.append({'output_type':'display_data','metadata':{},'data':{'image/png':base64.b64encode(buf.getvalue()).decode(),'text/plain':['<Matplotlib figure>']}})
  plt.close('all');cells.append({'cell_type':'code','metadata':{},'execution_count':count,'source':s.splitlines(keepends=True),'outputs':outputs})
 md('# Airline Operations Analysis\n\nReal BTS reporting-carrier records, 2010–2024. The included fact is a complete aggregation of 180 monthly source files, not a sample.')
 code("from pathlib import Path\nimport pandas as pd,sqlite3\nimport matplotlib.pyplot as plt\nROOT=Path.cwd() if (Path.cwd()/'data').exists() else Path.cwd().parent\nf=pd.read_csv(ROOT/'data/fact_airport_month.csv.gz')\nprint(f'{len(f):,} analytical rows; {int(f.flights.sum()):,} flight records')\nprint(f.head().to_string(index=False))")
 md('## Data quality\n\nMissing arrival times are separate from on-time arrivals. Rates use summed numerators and denominators.')
 code("assert not f.duplicated(['year','month','carrier_id','airport']).any()\nassert len(f[['year','month']].drop_duplicates())==180\nassert (f.flights==f[['eligible','cancelled','diverted','unknown']].sum(axis=1)).all()\nprint('Unique fact grain, 180 reporting months and mutually exclusive outcomes verified.')")
 md('## Annual trends\n\nReporting coverage expanded in 2018. Traffic trends reflect reporting and carrier composition changes.')
 code("con=sqlite3.connect(':memory:')\nf.to_sql('flights',con,index=False)\nannual=pd.read_sql_query('SELECT year,SUM(flights) flights,SUM(delayed)*1.0/SUM(eligible) delay_rate,SUM(cancelled)*1.0/SUM(flights) cancel_rate FROM flights GROUP BY year ORDER BY year',con)\nannual['flight_change']=annual.flights.pct_change()\nprint(annual.round(4).to_string(index=False))\nfig,ax=plt.subplots(figsize=(11,4))\nax.plot(annual.year,annual.flights/1e6,color='#2c70ab',marker='o')\nax.fill_between(annual.year,annual.flights/1e6,color='#2c70ab',alpha=.15)\nax.axvline(2018,color='#d29536',linestyle='--')\nax.set(title='Reported scheduled flights',xlabel='Year',ylabel='Million flight records')\nfig.tight_layout()")
 md('## Delay-minute contributions\n\nCause shares describe attributed minutes. Extreme weather is not the full weather impact; NAS includes non-extreme weather.')
 code("cols=['carrier_minutes','late_aircraft_minutes','nas_minutes','weather_minutes','security_minutes']\nc=f[cols].sum().sort_values(ascending=False)\nprint(pd.DataFrame({'minutes':c,'share':c/c.sum()}).round(4).to_string())\nfig,ax=plt.subplots(figsize=(10,4))\n(c/1e6).sort_values().plot.barh(ax=ax,color='#2c70ab')\nax.set(xlabel='Million attributed minutes',ylabel='',title='Delay contributions')\nfig.tight_layout()")
 md('## Matched airport comparison\n\nBoth 2019 and 2024 must have at least 100,000 eligible arrivals. This controls airport membership, not traffic mix.')
 code("p=f[f.year.isin([2019,2024])].groupby(['airport','year'])[['flights','eligible','delayed']].sum().reset_index()\na=p[p.year.eq(2019)].merge(p[p.year.eq(2024)],on='airport',suffixes=('_2019','_2024'))\na=a[(a.eligible_2019>=100000)&(a.eligible_2024>=100000)]\na['traffic_change']=a.flights_2024/a.flights_2019-1\na['delay_change_pp']=100*(a.delayed_2024/a.eligible_2024-a.delayed_2019/a.eligible_2019)\nprint(a.sort_values('traffic_change',ascending=False)[['airport','traffic_change','delay_change_pp']].head(15).round(3).to_string(index=False))\ncon.close()")
 md('## Findings\n\n'+'\n'.join('- '+x for x in json.loads((ROOT/'reports/findings.json').read_text()))+'\n\nPrioritise high-volume disruption reviews, investigate the largest recorded delay-minute categories, and validate seasonal planning locally. The analysis is descriptive, not causal.')
 for i,c in enumerate(cells):c['id']=hashlib.sha256((str(i)+''.join(c['source'])).encode()).hexdigest()[:12]
 (ROOT/'python/analysis.ipynb').write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.12'}},'nbformat':4,'nbformat_minor':5},indent=1));print('Executed notebook created')
if __name__=='__main__':main()
