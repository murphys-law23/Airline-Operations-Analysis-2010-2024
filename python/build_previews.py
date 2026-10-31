from pathlib import Path
import pandas as pd,json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
ROOT=Path(__file__).resolve().parents[1]
NAVY='#163650';BLUE='#2c70ab';CYAN='#45aebc';GOLD='#d29536';RED='#bf5748';BG='#edf2f6';EDGE='#c9d6df';MUT='#63788b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'text.color':NAVY,'xtick.color':MUT,'ytick.color':MUT})
def main():
 k=json.loads((ROOT/'reports/metrics.json').read_text());q={i:pd.read_csv(ROOT/f'reports/query_results/query_{i:02}.csv') for i in range(1,9)};f=pd.read_csv(ROOT/'data/fact_airport_month.csv.gz');a=pd.read_csv(ROOT/'data/dim_airports.csv');land=json.loads((ROOT/'data/reference/basemap.geojson').read_text());ap=f.groupby('airport')[['flights','eligible','delayed']].sum().reset_index().merge(a,on='airport');ap['rate']=ap.delayed/ap.eligible;ap=ap.sort_values('flights',ascending=False)
 def canvas(label):
  fig=plt.figure(figsize=(16,10),dpi=120,facecolor=BG)
  def txt(x,y,t,size=10,color=NAVY,bold=False,**kw):fig.text(x,y,t,fontsize=size,color=color,weight='bold' if bold else 'normal',**kw)
  def box(x,y,w,h,c='white'):fig.patches.append(Rectangle((x,y),w,h,facecolor=c,edgecolor=EDGE,lw=.8,transform=fig.transFigure,zorder=-1))
  def panel(x,y,w,h,title,sub='',left=.05):
   box(x,y,w,h);txt(x+.012,y+h-.028,title,11,bold=True);txt(x+.012,y+h-.05,sub,8,MUT);return fig.add_axes([x+left,y+.035,w-left-.018,h-.11],facecolor='none')
  box(.015,.91,.97,.075,NAVY);txt(.03,.965,'MURPHY ANALYTICS / U.S. DOMESTIC AVIATION',8,'#b8d7e9');txt(.03,.932,'AIRLINE OPERATIONS ANALYSIS',22,'white',True);txt(.97,.942,'2010–2024',20,'white',True,ha='right');txt(.02,.885,label+'  /  ALL REPORTING CARRIERS  /  ALL DESTINATION AIRPORTS',9,bold=True)
  cards=[('SCHEDULED FLIGHTS',f"{k['flights']/1e6:.1f}M",'All reported flight records'),('ON-TIME ARRIVALS',f"{k['on_time_rate']:.1%}",'Among eligible arrivals'),('CANCELLATION RATE',f"{k['cancel_rate']:.1%}",'Among scheduled flights'),('AVG LATE ARRIVAL',f"{k['mean_late_minutes']:.1f} min",'Arrivals delayed 15+ minutes'),('DESTINATION AIRPORTS',str(k['airports']),'In the full reporting scope')]
  for i,(l,v,n) in enumerate(cards):
   x=.015+i*.196;box(x,.77,.186,.095);box(x,.862,.186,.003,BLUE);txt(x+.01,.84,l,8,MUT,True);txt(x+.01,.802,v,23,bold=True);txt(x+.01,.782,n,7.5,MUT)
  txt(.02,.025,'BTS flight records · OurAirports coordinates · Natural Earth basemap · Static Python analytical preview',8,MUT);txt(.98,.025,'PYTHON / SQL / POWER BI BUILD KIT',8,MUT,ha='right');return fig,txt,box,panel
 def style(ax):
  ax.spines[['top','right','left']].set_visible(False);ax.spines['bottom'].set_color(EDGE);ax.tick_params(length=0,labelsize=8);ax.grid(axis='y',color=EDGE,lw=.6);ax.set_axisbelow(True)
 def bars(ax,labels,vals,fmt,color=BLUE):
  v=list(vals)[::-1];ax.barh(list(labels)[::-1],v,color=color,height=.58);mx=max(v);ax.set_xlim(0,mx*1.3);ax.spines[:].set_visible(False);ax.tick_params(length=0,labelbottom=False,labelsize=8)
  for i,x in enumerate(v):ax.text(x+mx*.025,i,fmt(x),va='center',fontsize=8)
 def mapplot(ax):
  for feat in land['features']:
   for poly in (feat['geometry']['coordinates'] if feat['geometry']['type']=='MultiPolygon' else [feat['geometry']['coordinates']]):ax.add_patch(Polygon(poly[0],facecolor='#dbe7ef',edgecolor='#a9becd',lw=.5))
  p=ap[ap.longitude.between(-128,-65)&ap.latitude.between(23,51)];ax.scatter(p.longitude,p.latitude,s=8+300*p.flights/p.flights.max(),c=[BLUE if r<.15 else GOLD if r<.25 else RED for r in p.rate],alpha=.8,edgecolors='white',linewidths=.5,zorder=3)
  for r in p.head(7).itertuples():ax.annotate(r.airport,(r.longitude,r.latitude),xytext=(5,6),textcoords='offset points',fontsize=7,fontweight='bold',zorder=4)
  ax.set_xlim(-128,-65);ax.set_ylim(23,51);ax.axis('off')
 fig,txt,box,panel=canvas('01 OVERVIEW');ax=panel(.015,.395,.47,.355,'ANNUAL FLIGHT ACTIVITY','Scheduled flight records in millions');ax.fill_between(q[1].year,q[1].flights/1e6,color=BLUE,alpha=.18);ax.plot(q[1].year,q[1].flights/1e6,color=BLUE,marker='o',ms=3);ax.set_ylim(0,q[1].flights.max()/1e6*1.15);ax.set_xticks(range(2010,2025,2));style(ax);ax.axvline(2018,color=GOLD,ls='--',lw=1);ax.text(2018.2,.5,'2018 reporting\nexpansion',fontsize=7)
 ax=panel(.495,.395,.49,.355,'AIRPORT PERFORMANCE MAP','Contiguous U.S. · size: traffic · colour: arrival-delay rate',left=.01);mapplot(ax);txt(.515,.41,'Blue <15%     Amber 15–24.9%     Red ≥25%',8,MUT)
 ax=panel(.015,.09,.315,.285,'DELAY MINUTES BY CAUSE','Share of attributed delay minutes',left=.12);labs=q[6].cause.replace({'National aviation system':'National system'});bars(ax,labs,q[6].minute_share,lambda v:f'{v:.1%}')
 ax=panel(.34,.09,.315,.285,'FLIGHT OUTCOMES','Shares of all scheduled flight records');ax.remove();vals=[k['eligible']-k['delayed'],k['delayed'],k['cancelled'],k['diverted'],k['unknown']];ax=fig.add_axes([.35,.12,.145,.16]);ax.pie(vals,colors=[BLUE,GOLD,RED,CYAN,'#b7c5d0'],startangle=90,wedgeprops={'width':.27,'edgecolor':'white'});ax.text(0,0,f"{k['flights']/1e6:.1f}M",ha='center',va='center',fontsize=17,weight='bold')
 for i,(l,v) in enumerate(zip(['On time','Delayed 15+','Cancelled','Diverted','Missing'],vals)):txt(.505,.28-i*.032,f'{l}  {v/k["flights"]:.1%}',8)
 ax=panel(.665,.09,.32,.285,'BUSIEST DESTINATION AIRPORTS','Top eight · scheduled arrivals');p=ap.head(8);bars(ax,p.airport,p.flights,lambda v:f'{v/1e6:.1f}M');txt(.02,.055,'Arrival-delay rates exclude cancellations and diversions. Long-term comparisons reflect reporting changes and traffic mix.',8,MUT);fig.savefig(ROOT/'reports/dashboard_overview.png',facecolor=BG);plt.close(fig)
 fig,txt,box,panel=canvas('02 AIRPORT NETWORK');ax=panel(.015,.24,.65,.51,'AIRPORT PERFORMANCE MAP','Contiguous U.S. · other regions available in the HTML report',left=.01);mapplot(ax);txt(.035,.255,'Blue <15%     Amber 15–24.9%     Red ≥25%',9,MUT);ax=panel(.675,.24,.31,.51,'HIGHEST DELAY RATES','At least 100,000 eligible arrivals');p=q[3].head(12);bars(ax,p.airport,p.delay_rate,lambda v:f'{v:.1%}',GOLD);txt(.03,.17,f"{k['mapped_airports']} of {k['airports']} airport codes have matched coordinates. Unmapped airports remain in totals and tables.",11);txt(.03,.12,'Rankings are descriptive: they do not control for carrier, route or season. The HTML report includes airport filtering and CSV export.',10,MUT);fig.savefig(ROOT/'reports/dashboard_airports.png',facecolor=BG);plt.close(fig)
 fig,txt,box,panel=canvas('03 CARRIER PERFORMANCE');p=q[4].sort_values('eligible',ascending=False).head(10);ax=panel(.015,.22,.475,.53,'ARRIVAL DELAY RATE','Ten largest reporting carriers by eligible arrivals',left=.06);bars(ax,p.carrier,p.delay_rate,lambda v:f'{v:.1%}');ax=panel(.5,.22,.485,.53,'CANCELLATION RATE','Cancelled / scheduled flights for the same carriers',left=.06);bars(ax,p.carrier,p.cancel_rate,lambda v:f'{v:.1%}',RED);txt(.025,.16,'Carrier identity uses DOT ID. Names and historical aliases appear in data/dim_carriers.csv.',11);txt(.025,.12,'Use a common year range for comparisons. Full-period rates combine differing operating histories and traffic mixes.',10,MUT);fig.savefig(ROOT/'reports/dashboard_carriers.png',facecolor=BG);plt.close(fig)
 fig,txt,box,panel=canvas('04 DELAY DRIVERS');ax=panel(.015,.43,.475,.32,'SEASONAL ARRIVAL DELAYS','Pooled calendar-month rate');ax.plot(q[5].month,q[5].delay_rate*100,color=BLUE,marker='o',ms=3);ax.fill_between(q[5].month,q[5].delay_rate*100,color=BLUE,alpha=.15);ax.set_ylim(0,q[5].delay_rate.max()*120);ax.set_ylabel('Percent');ax.set_xticks(range(1,13),['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']);style(ax);ax=panel(.5,.43,.485,.32,'ATTRIBUTED DELAY MINUTES','Cause shares describe minutes, not flights',left=.15);bars(ax,labs,q[6].minutes,lambda v:f'{v/1e6:.1f}M');ax=panel(.015,.07,.97,.34,'YEAR AND MONTH PATTERNS','Arrival-delay rate · darker means higher');mat=q[2].pivot(index='year',columns='month',values='delay_rate');ax.imshow(mat,aspect='auto',cmap='Blues',vmin=0,vmax=.4);ax.set_xticks(range(12),['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']);ax.set_yticks(range(15),mat.index);ax.tick_params(length=0,labelsize=7);ax.spines[:].set_visible(False)
 for i in range(15):
  for j in range(12):v=mat.iloc[i,j];ax.text(j,i,f'{v:.0%}',ha='center',va='center',fontsize=6,color='white' if v>.24 else NAVY)
 fig.savefig(ROOT/'reports/dashboard_drivers.png',facecolor=BG);plt.close(fig);print('Four analytical previews created')
if __name__=='__main__':main()
