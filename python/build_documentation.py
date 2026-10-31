from pathlib import Path
import json,pandas as pd
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[('BTS dataset and definitions','https://transtats.bts.gov/DatabaseInfo.asp?DB_URL=&QO_VQ=EFD'),('BTS 2018 reporting change','https://www.bts.gov/topics/airlines-and-airports/lists-reporting-air-carriers-and-reportable-airports-time-performance'),('OurAirports coordinates and terms','https://ourairports.com/data/'),('Natural Earth terms','https://www.naturalearthdata.com/about/terms-of-use/'),('Power Query decompression','https://learn.microsoft.com/en-us/powerquery-m/binary-decompress'),('Azure Maps markers','https://learn.microsoft.com/en-us/azure/azure-maps/power-bi-visual-add-bubble-layer')]
def newdoc(title,sub):
 d=Document();s=d.sections[0];s.top_margin=s.bottom_margin=Inches(.65);s.left_margin=s.right_margin=Inches(.7)
 for n in ['Normal','Title','Heading 1','Heading 2']:
  d.styles[n].font.name='Calibri';d.styles[n].font.color.rgb=RGBColor(0,0,0)
 d.styles['Normal'].font.size=Pt(10);d.styles['Normal'].paragraph_format.space_after=Pt(6);d.styles['Normal'].paragraph_format.line_spacing=1.05;d.styles['Title'].font.size=Pt(24);d.styles['Heading 1'].font.size=Pt(15)
 d.add_paragraph(title,style='Title');d.add_paragraph(sub);return d

def table(d,heads,rows):
 t=d.add_table(rows=1,cols=len(heads));t.autofit=False
 for c,v in zip(t.rows[0].cells,heads):c.text=str(v)
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for i,r in enumerate(t.rows):
  for j,c in enumerate(r.cells):
   c.width=Inches(1.75 if j==0 else 4.6);pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
   for side in ['top','bottom','left','right']:
    e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
   pr.append(b);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'163650' if i==0 else ('F1F5F8' if i%2 else 'FFFFFF'));pr.append(sh)
   for p in c.paragraphs:
    p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4)
    for run in p.runs:run.font.size=Pt(9);run.bold=i==0;run.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else '20384C')
 return t

def main():
 k=json.loads((ROOT/'reports/metrics.json').read_text());q={i:pd.read_csv(ROOT/f'reports/query_results/query_{i:02}.csv') for i in range(1,9)};a=q[1].set_index('year');s=q[5].sort_values('delay_rate',ascending=False);c=q[6].iloc[0];w=q[3].iloc[0];months=['January','February','March','April','May','June','July','August','September','October','November','December']
 findings=[f"The analysis processes {k['flights']:,} flight records from 180 monthly source files into {k['aggregate_rows']:,} analytical rows, covering {k['airports']} airports and {k['carriers']} DOT carrier identities.",f"{k['on_time_rate']:.1%} of eligible arrivals were on time; {k['delay_rate']:.1%} were delayed by at least 15 minutes. Cancellations were {k['cancel_rate']:.1%} of scheduled flight records.",f"Delayed eligible arrivals averaged {k['mean_late_minutes']:.1f} minutes late. This excludes on-time, cancelled and diverted flights.",f"Reported traffic changed by {a.loc[2020,'flights']/a.loc[2019,'flights']-1:+.1%} in 2020 versus 2019. In 2024, volume was {a.loc[2024,'flights']/a.loc[2019,'flights']-1:+.1%} relative to 2019; the delay rate changed by {100*(a.loc[2024,'delay_rate']-a.loc[2019,'delay_rate']):+.1f} percentage points.",f"{c['cause']} accounted for {c['minute_share']:.1%} of attributed delay minutes, the largest recorded category.",f"{months[int(s.iloc[0]['month'])-1]} had the highest pooled calendar-month delay rate ({s.iloc[0]['delay_rate']:.1%}); {months[int(s.iloc[-1]['month'])-1]} had the lowest ({s.iloc[-1]['delay_rate']:.1%}).",f"Among airports with at least 100,000 eligible arrivals across the full period, {w['airport']} had the highest delay rate ({w['delay_rate']:.1%}). Rankings are not adjusted for traffic mix."]
 (ROOT/'reports/findings.json').write_text(json.dumps(findings,indent=2))
 defs=[('Scheduled flights','Count of source records, including cancellations and diversions.'),('Eligible arrivals','Not cancelled or diverted, with a reported arrival delay.'),('Delayed arrivals','Eligible arrivals delayed at least 15 minutes.'),('On-time rate','(Eligible minus delayed) / eligible arrivals.'),('Cancellation rate','Cancelled flights / scheduled flight records.'),('Severe-delay rate','Eligible arrivals delayed at least 60 minutes / eligible arrivals.'),('Average late arrival','Arrival-delay minutes on delayed eligible flights / delayed eligible flights.'),('Cause-minute share','Minutes in a recorded cause / all attributed cause minutes.'),('Unknown arrival','Not cancelled or diverted, but arrival delay is missing.'),('YoY volume change','Current year / previous year minus one.')]
 d=newdoc('Airline Operations Analysis','Project handbook | U.S. domestic aviation | 2010–2024');d.add_paragraph('This project examines airline reliability, airport performance and delay causes using real BTS flight records. It supports operational benchmarking and identifies areas for investigation; it does not establish causal effects.')
 d.add_heading('Key findings',1)
 for x in findings:d.add_paragraph(x,style='List Bullet')
 d.add_heading('Recommendations',1)
 for x in ['Investigate persistent disruption at high-volume airports. Use the matched 2019–2024 airport comparison before relying on a full-period ranking.','Review the largest delay-minute categories with operations teams and test interventions against local route and turnaround evidence.','Validate seasonal staffing and recovery plans within individual airports and carriers. Pooled national patterns do not apply equally everywhere.']:d.add_paragraph(x,style='List Number')
 d.add_page_break();d.add_heading('Data scope and provenance',1);d.add_paragraph(f"All 180 BTS Reporting Carrier On-Time Performance files from January 2010 to December 2024 were processed. Original archives total {k['raw_bytes']/1e9:.2f} GB. Each source row represents one reported scheduled domestic flight. The delivered fact table is a complete aggregation, not a sample, at year × month × DOT carrier ID × destination airport.")
 d.add_paragraph('data/source_manifest.json records each URL, timestamp, byte size, SHA-256 and source-row count. The first 1,000 records of January 2024 are included as an inspection sample only. The full analysis always uses the complete fact table.')
 d.add_paragraph(f"OurAirports coordinates match {k['mapped_airports']} of {k['airports']} airport codes. Unmapped airports remain in totals and tables. The matching process prefers large and medium airports when IATA codes repeat. Current coordinates do not reconstruct historical airport relocations. The basemap uses Natural Earth boundaries.")
 d.add_heading('Metric definitions',1);table(d,['Metric','Definition'],defs);d.add_paragraph('All rates use summed counts. Percentages are never averaged across months, carriers or airports. A zero denominator produces a blank rate, not zero. Missing arrival times are not classified as on time.')
 d.add_page_break();d.add_heading('Methods and validation',1)
 for x in ['Download monthly archives with retries. Resume only from validated completed monthly aggregates.','Read selected columns in chunks of 150,000 rows. Define mutually exclusive outcomes and aggregate flight counts and delay minutes.','Preserve DOT reporting-carrier identities, join airport coordinates and build an indexed SQLite analytical model.','Run eight SQL queries and independently reconcile annual, monthly, airport and carrier results against pandas.','Generate the HTML dashboard, previews, notebook and handbooks from the same fact table.']:d.add_paragraph(x,style='List Number')
 table(d,['SQL query','Purpose'],[['01','Annual performance and LAG-based volume changes.'],['02','Monthly performance and a weighted rolling 12-month rate.'],['03','Airport rankings with a minimum-volume threshold.'],['04','Reporting-carrier comparisons with dimension joins.'],['05','Pooled calendar-month seasonality.'],['06','Delay-minute shares with UNION ALL and a window denominator.'],['07','Matched airport comparison between 2019 and 2024.'],['08','Carrier rankings partitioned by year.']])
 d.add_heading('Limitations',1);d.add_paragraph('BTS expanded reporting coverage in 2018 by lowering the reporting-carrier revenue threshold from 1% to 0.5%. Airline mergers, coverage and traffic mix change over time. Reported-flight growth is not a constant-coverage measure of total market growth. Marketing-carrier data are not mixed into this reporting-carrier series.')
 d.add_paragraph('Rankings are descriptive and unadjusted for carrier, route and season. National aviation system delays include non-extreme weather, so the extreme-weather category is not the full weather impact. Missing cause values contribute no attributed minutes. Flight counts do not establish passenger volume, revenue, profitability or route demand.')
 d.add_page_break();d.add_heading('Run and publish',1)
 for x in ['Extract the project and open dashboard/index.html in a browser. The included report works offline.','Use Python 3.11+. Install requirements.txt and run python python/run_all.py from the project root.','For source-level reproduction, run python python/ingest.py --workers 6 before run_all.py. This requires several GB and substantial processing time.','Run python -m unittest discover -s tests -v. Review reports/validation.txt and reports/unmapped_airports.csv.','Upload the project contents to a GitHub repository. README.md includes preview links and setup instructions. REPO_DESCRIPTION.txt provides the repository About text.']:d.add_paragraph(x,style='List Number')
 table(d,['Folder','Contents'],[['data','Complete compressed fact, dimensions, source manifest and coordinate snapshots.'],['python','Ingestion, analysis, report builders and executed notebook.'],['sql','Eight analytical queries.'],['dashboard','Offline HTML report and editable template.'],['reports','Four previews, SQL results, findings and validation evidence.'],['powerbi','M imports, DAX measures, model definitions and theme.'],['docs','Project handbook and Power BI build guide.']])
 d.add_paragraph('Power BI status: a build kit is included, not a native PBIX. Power BI Desktop execution has not been verified. The completed interactive report is HTML. PNGs are Python analytical previews, not Power BI screenshots.')
 d.add_heading('Primary sources',1)
 for n,u in SOURCES[:4]:
  p=d.add_paragraph(n+': '+u)
  for r in p.runs:r.font.size=Pt(8)
 d.save(ROOT/'docs/Project_Handbook.docx')
 b=newdoc('Power BI Build Guide','Airline Operations Analysis | 2010–2024');b.add_paragraph('Build a four-page report using the supplied Power Query, DAX and theme files. This kit has not been executed in Power BI Desktop, and no native PBIX is included. The completed interactive report is dashboard/index.html.')
 b.add_heading('Import and relationships',1)
 for x in ['Create a Text parameter named DataRoot with the extracted project folder, for example C:/Projects/airline_performance.','Create blank queries named FactFlights, Airports and Carriers. Paste the matching .m files into Advanced Editor. The fact query reads the compressed GZip CSV directly.','Create the Calendar and DelayCauses calculated tables from model.dax. Mark Calendar as the date table. Sort Calendar[Month] by MonthNumber.','Use single-direction one-to-many relationships from Calendar[Date] to FactFlights[Month Start], Airports[airport] to FactFlights[airport], and Carriers[carrier_id] to FactFlights[carrier_id]. Leave DelayCauses disconnected.','Create each measure in measures.dax separately. Use whole numbers for counts, one decimal for rates and minutes, and decimal numbers for percentage-point changes.','Import theme.json. Add synced year, carrier and airport slicers to four pages: Overview, Airport Network, Carrier Performance and Delay Drivers.']:b.add_paragraph(x,style='List Number')
 b.add_heading('Important modelling checks',1);b.add_paragraph('One fact row represents many flights. Use SUM(flights), never COUNTROWS of the fact, for flight volume. Retain unknown arrival records. Keep blank coordinates as null. Do not merge successor airlines into one historical network or relate the calendar using year alone.')
 b.add_page_break();b.add_heading('Report layout and map',1)
 table(b,['Visual','Fields and measures'],[['KPI strip','Scheduled Flights; On Time Rate; Cancellation Rate; Average Late Arrival Minutes; Airports In Scope.'],['Annual area chart','Calendar[Year] and Scheduled Flights. Annotate the 2018 reporting expansion.'],['Airport map','Airport code, Latitude, Longitude; Scheduled Flights as size; delay and cancellation rates as tooltips.'],['Cause bars','DelayCauses[Cause] and Selected Cause Share.'],['Airport table','Airport, Scheduled Flights, Eligible Arrivals, Arrival Delay Rate, Cancellation Rate. Apply a 10,000-eligible-arrival threshold.'],['Monthly trend','Calendar[YearMonth], Arrival Delay Rate and optional Rolling 12 Month Delay Rate.'],['Carrier charts','Carrier name with delay and cancellation rates. Top ten by eligible arrivals.'],['Seasonality and heatmap','Month versus delay rate; Year × Month matrix with blue conditional formatting.']])
 for x in ['Use Azure Maps with explicitly categorised latitude/longitude columns, rather than relying on airport-code geocoding. Add airport identity, coordinates, size and tooltip fields.','Use Airport Map Colour for field-value colour formatting where supported. Otherwise use a labelled continuous Arrival Delay Rate scale. Display bands below 15%, 15–24.9% and at least 25% are design thresholds, not service standards.','Exclude missing coordinates from the map only, not from model totals. Use separate views or bookmarks for the contiguous U.S., Alaska, Hawaii and territories.','Azure Maps requires network access and may depend on tenant settings. The delivered HTML map works offline. Maintain navy headers, white bordered panels and readable chart labels across separate pages.']:b.add_paragraph(x,style='List Number')
 b.add_page_break();b.add_heading('Acceptance checks',1);table(b,['Full-period metric','Expected result'],[['Scheduled flights',f"{k['flights']:,}"],['Eligible arrivals',f"{k['eligible']:,}"],['Delayed arrivals',f"{k['delayed']:,}"],['On-time rate',f"{k['on_time_rate']:.1%}"],['Cancellation rate',f"{k['cancel_rate']:.1%}"],['Average late arrival',f"{k['mean_late_minutes']:.1f} minutes"],['Airport count',str(k['airports'])]])
 for x in ['Reconcile annual and monthly visuals with query_01.csv and query_02.csv. Test a single year, carrier and airport, then clear filters.','On-time plus delayed must equal eligible arrivals. Eligible, cancelled, diverted and unknown must sum to scheduled flights.','Verify that totals recompute weighted rates from counts. First-year prior-year values should be blank; the rolling rate should not display a partial first-year window.','Confirm that map markers, tooltips and filter selections match the tables. Preserve airports without coordinates in the overall KPIs.','Save the completed native report as powerbi/Airline_Operations.pbix only after validation. Do not label the supplied PNGs as Power BI screenshots.']:b.add_paragraph(x,style='List Number')
 b.add_heading('Microsoft references',1)
 for n,u in SOURCES[4:]:
  p=b.add_paragraph(n+': '+u)
  for r in p.runs:r.font.size=Pt(8)
 b.save(ROOT/'docs/PowerBI_Build_Guide.docx')
 readme=f'''# Airline Operations Analysis — 2010–2024

**{k['flights']:,} real flight records · 15 years · Python · SQL · Power BI build kit**

![Dashboard overview](reports/dashboard_overview.png)

---

## Business question

How have airline reliability, airport performance and delay causes changed, and where should an operations team investigate recurring disruption?

## Data scope

All 180 monthly BTS Reporting Carrier On-Time Performance files, January 2010–December 2024. The complete delivered aggregate has **{k['aggregate_rows']:,} rows**, **{k['airports']} airports** and **{k['carriers']} DOT carrier identities**. Grain: month × reporting-carrier DOT ID × scheduled destination airport. No synthetic flight data.

The 1,000-row `data/flight_sample.csv` is an inspection sample only. All findings use the complete aggregate table. Original source URLs, hashes and row counts are in `data/source_manifest.json`.

## Findings

'''+ '\n'.join('- '+x for x in findings[1:])+'''

## Recommendations

Investigate persistent disruption at high-volume airports, review the largest recorded delay-minute categories and validate seasonal staffing within individual airports and carriers. Use the matched 2019–2024 airport cohort when assessing recovery. The analysis is descriptive, not causal.

---

## Dashboard

Extract the project and open [dashboard/index.html](dashboard/index.html) locally. GitHub displays HTML source; download the project to use its interactive report.

- **Overview:** activity trend, airport map, flight outcomes, busiest airports and cause shares.
- **Airport Network:** enlarged map, clickable airport markers, monthly trend, volume threshold and CSV export.
- **Carrier Performance:** delay and cancellation comparisons.
- **Delay Drivers:** seasonality, cause minutes and year/month heatmap.

Year, carrier and airport filters apply across pages. Map-region selection changes the viewport only. Alaska, Hawaii and territories have separate map views. PNGs are Python analytical previews.

<details><summary>Additional previews</summary>

![Airports](reports/dashboard_airports.png)

![Carriers](reports/dashboard_carriers.png)

![Delay drivers](reports/dashboard_drivers.png)

</details>

## Skills demonstrated

| Tool | Demonstrated work |
|---|---|
| Python | Resumable downloads, chunked processing, validation, coordinate joins, notebook analysis and reporting |
| SQL | Indexed SQLite model, joins, CTEs, LAG, rolling windows, ranking and weighted rates |
| Power BI build kit | Power Query imports, model relationships, DAX time comparisons, map setup and theme |
| Dashboard | Offline SVG map, linked filters, four views, tooltips and CSV export |

**Power BI status:** M, DAX, theme and build guide are supplied. No native `.pbix` is included, and Power BI Desktop execution is not verified. The completed interactive dashboard is HTML.

---

## Reproduce

Requires Python 3.11+.

```bash
python -m pip install -r requirements.txt
python python/run_all.py
```

This rebuilds from the complete included aggregate dataset. To reproduce from flight-level sources:

```bash
python python/ingest.py --workers 6
python python/run_all.py
```

The source download requires several GB and substantial time. Valid completed months are reused. Raw archives, monthly intermediates and the rebuildable SQLite database are excluded from Git and the delivered ZIP.

```bash
python -m unittest discover -s tests -v
```

See `reports/validation.txt` for reconciliation evidence and `python/analysis.ipynb` for executed analysis.

## Definitions

Eligible arrivals exclude cancellations, diversions and missing arrival times. Delayed means arrival at least 15 minutes late. On-time rate is (eligible − delayed) / eligible. Cancellation rate is cancelled / scheduled. Average late arrival uses delayed eligible flights only. Cause shares describe attributed minutes, not flights. All rates use summed numerators and denominators; percentages are not averaged across groups.

## Project structure

| Folder | Contents |
|---|---|
| `data/` | Complete fact table, dimensions, manifest and coordinate snapshots |
| `python/` | Reproducible scripts and executed notebook |
| `sql/` | Eight analytical queries |
| `dashboard/` | Offline report and editable template |
| `reports/` | Previews, findings, SQL results and validation |
| `powerbi/` | M, DAX, model and theme |
| `docs/` | [Project handbook](docs/Project_Handbook.docx) and [Power BI guide](docs/PowerBI_Build_Guide.docx) |
| `tests/` | Metric boundary checks |

---

## Limitations

Reporting expanded in 2018; mergers, coverage and traffic mix also change over time. Reported traffic is not a constant-coverage market census. Marketing-carrier records are not mixed into this series. Rankings are unadjusted for traffic mix. Extreme-weather minutes are not the full weather impact. Missing cause values contribute no attributed minutes. Current airport coordinates do not capture historical relocations; unmatched airports remain in totals. The analysis does not establish passenger volume, revenue or profitability.

## Sources and licence

'''+ '\n'.join(f'- [{n}]({u})' for n,u in SOURCES)+'''

Original code and documentation use the MIT licence. BTS data retain their U.S. federal status; OurAirports and Natural Earth data are public domain. No source-agency endorsement is implied.
'''
 (ROOT/'README.md').write_text(readme);print('Documentation built')
if __name__=='__main__':main()
