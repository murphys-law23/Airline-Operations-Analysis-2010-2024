-- SQLite 3.25+. Each query runs against fact_airport_month and dimensions.
-- 01 Annual weighted performance and year-over-year volume
WITH a AS (SELECT year,SUM(flights) flights,SUM(eligible) eligible,SUM(delayed) delayed,SUM(cancelled) cancelled,
 1.0*SUM(delayed)/NULLIF(SUM(eligible),0) delay_rate,1.0*SUM(cancelled)/NULLIF(SUM(flights),0) cancel_rate,
 1.0*SUM(delay_minutes)/NULLIF(SUM(delayed),0) mean_late_minutes FROM fact_airport_month GROUP BY year)
SELECT *,1.0*flights/NULLIF(LAG(flights) OVER(ORDER BY year),0)-1 flights_yoy FROM a ORDER BY year;
-- QUERY
-- 02 Monthly performance with a weighted trailing 12-month rate
WITH a AS (SELECT year,month,SUM(flights) flights,SUM(eligible) eligible,SUM(delayed) delayed,SUM(cancelled) cancelled,
 1.0*SUM(delayed)/NULLIF(SUM(eligible),0) delay_rate,1.0*SUM(cancelled)/NULLIF(SUM(flights),0) cancel_rate
 FROM fact_airport_month GROUP BY year,month)
SELECT *,CASE WHEN ROW_NUMBER() OVER(ORDER BY year,month)>=12 THEN
 1.0*SUM(delayed) OVER(ORDER BY year,month ROWS 11 PRECEDING)/NULLIF(SUM(eligible) OVER(ORDER BY year,month ROWS 11 PRECEDING),0)
 END rolling_12m_delay_rate FROM a ORDER BY year,month;
-- QUERY
-- 03 Airport comparisons: at least 100,000 eligible arrivals in the full period
WITH a AS (SELECT f.airport,d.city,d.state,SUM(flights) flights,SUM(eligible) eligible,SUM(delayed) delayed,SUM(cancelled) cancelled,
 1.0*SUM(delayed)/NULLIF(SUM(eligible),0) delay_rate,1.0*SUM(cancelled)/NULLIF(SUM(flights),0) cancel_rate
 FROM fact_airport_month f JOIN dim_airports d USING(airport) GROUP BY f.airport,d.city,d.state HAVING SUM(eligible)>=100000)
SELECT *,DENSE_RANK() OVER(ORDER BY delay_rate DESC) delay_rank FROM a ORDER BY delay_rank,airport;
-- QUERY
-- 04 Carrier identity uses DOT ID; rankings are not adjusted for traffic mix
SELECT f.carrier_id,c.carrier,c.name,SUM(flights) flights,SUM(eligible) eligible,SUM(delayed) delayed,SUM(cancelled) cancelled,
 1.0*SUM(delayed)/NULLIF(SUM(eligible),0) delay_rate,1.0*SUM(cancelled)/NULLIF(SUM(flights),0) cancel_rate,
 MIN(year) first_year,MAX(year) last_year FROM fact_airport_month f JOIN dim_carriers c USING(carrier_id)
 GROUP BY f.carrier_id,c.carrier,c.name ORDER BY flights DESC;
-- QUERY
-- 05 Calendar-month seasonality, pooled across years
SELECT month,SUM(flights) flights,SUM(eligible) eligible,SUM(delayed) delayed,
 1.0*SUM(delayed)/NULLIF(SUM(eligible),0) delay_rate,1.0*SUM(cancelled)/NULLIF(SUM(flights),0) cancel_rate
 FROM fact_airport_month GROUP BY month ORDER BY month;
-- QUERY
-- 06 Shares of attributed delay minutes, not shares of flights
WITH c AS (SELECT 'Air carrier' cause,SUM(carrier_minutes) minutes FROM fact_airport_month UNION ALL
 SELECT 'Late aircraft',SUM(late_aircraft_minutes) FROM fact_airport_month UNION ALL
 SELECT 'National aviation system',SUM(nas_minutes) FROM fact_airport_month UNION ALL
 SELECT 'Extreme weather',SUM(weather_minutes) FROM fact_airport_month UNION ALL
 SELECT 'Security',SUM(security_minutes) FROM fact_airport_month)
SELECT *,1.0*minutes/NULLIF(SUM(minutes) OVER(),0) minute_share FROM c ORDER BY minutes DESC;
-- QUERY
-- 07 Fixed airport cohort: recovery and reliability, 2019 versus 2024
WITH a AS (SELECT airport,year,SUM(flights) flights,SUM(eligible) eligible,SUM(delayed) delayed
 FROM fact_airport_month WHERE year IN(2019,2024) GROUP BY airport,year)
SELECT a.airport,a.flights flights_2019,b.flights flights_2024,1.0*b.flights/a.flights-1 traffic_change,
 1.0*a.delayed/a.eligible delay_rate_2019,1.0*b.delayed/b.eligible delay_rate_2024,
 100.0*(1.0*b.delayed/b.eligible-1.0*a.delayed/a.eligible) delay_change_pp
 FROM a JOIN a b ON a.airport=b.airport AND a.year=2019 AND b.year=2024
 WHERE a.eligible>=100000 AND b.eligible>=100000 ORDER BY traffic_change DESC;
-- QUERY
-- 08 Reporting-carrier rankings within each year, minimum 100,000 eligible arrivals
WITH a AS (SELECT year,carrier_id,SUM(eligible) eligible,1.0*SUM(delayed)/NULLIF(SUM(eligible),0) delay_rate
 FROM fact_airport_month GROUP BY year,carrier_id HAVING SUM(eligible)>=100000)
SELECT *,DENSE_RANK() OVER(PARTITION BY year ORDER BY delay_rate) reliability_rank FROM a ORDER BY year,reliability_rank;
