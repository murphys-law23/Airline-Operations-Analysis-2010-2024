import unittest,sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from ingest import transform
class Metrics(unittest.TestCase):
 def frame(self,delays,cancel=None,divert=None):
  n=len(delays);d=pd.DataFrame({'Year':[2024]*n,'Month':[1]*n,'Reporting_Airline':['AA']*n,'DOT_ID_Reporting_Airline':[19805]*n,'Dest':['JFK']*n,'Cancelled':cancel or [0]*n,'Diverted':divert or [0]*n,'ArrDelay':delays})
  for k in ['CarrierDelay','WeatherDelay','NASDelay','SecurityDelay','LateAircraftDelay']:d[k]=float('nan')
  return d
 def test_thresholds(self):
  x=transform(self.frame([-5,0,14,15,59,60]));self.assertEqual(x.delayed.sum(),3);self.assertEqual(x.severe.sum(),1);self.assertEqual(x.delay_minutes.sum(),134)
 def test_cancelled(self):self.assertEqual(transform(self.frame([100,None],[1,1])).eligible.sum(),0)
 def test_diverted(self):self.assertEqual(transform(self.frame([100],[0],[1])).eligible.sum(),0)
 def test_missing(self):
  x=transform(self.frame([None]));self.assertEqual(x.unknown.sum(),1);self.assertEqual(x.eligible.sum(),0)
 def test_reconciliation(self):
  x=transform(self.frame([0,20,None,None,None],[0,0,1,0,0],[0,0,0,1,0]));self.assertEqual(x.flights.sum(),x[['eligible','cancelled','diverted','unknown']].sum().sum())
 def test_cause_scope(self):
  d=self.frame([10,30,40],[0,0,1]);d.CarrierDelay=[10,30,40];self.assertEqual(transform(d).carrier_minutes.sum(),30)
 def test_weighted(self):
  x=transform(self.frame([20]+[0]*9));self.assertEqual(x.delayed.sum()/x.eligible.sum(),.1)
if __name__=='__main__':unittest.main()
