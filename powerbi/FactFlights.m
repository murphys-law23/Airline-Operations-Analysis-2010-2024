// Create a Text parameter named DataRoot with the extracted project folder path.
let
 Source=Csv.Document(Binary.Decompress(File.Contents(DataRoot & "/data/fact_airport_month.csv.gz"),Compression.GZip),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),
 Headers=Table.PromoteHeaders(Source,[PromoteAllScalars=true]),
 Typed=Table.TransformColumnTypes(Headers,{{"year",Int64.Type},{"month",Int64.Type},{"carrier_id",Int64.Type},{"flights",Int64.Type},{"cancelled",Int64.Type},{"diverted",Int64.Type},{"eligible",Int64.Type},{"delayed",Int64.Type},{"severe",Int64.Type},{"unknown",Int64.Type},{"delay_minutes",Int64.Type},{"carrier_minutes",Int64.Type},{"weather_minutes",Int64.Type},{"nas_minutes",Int64.Type},{"security_minutes",Int64.Type},{"late_aircraft_minutes",Int64.Type}}),
 WithDate=Table.AddColumn(Typed,"Month Start",each #date([year],[month],1),type date)
in WithDate