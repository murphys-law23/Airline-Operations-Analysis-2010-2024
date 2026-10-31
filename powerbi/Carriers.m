let
 Source=Csv.Document(File.Contents(DataRoot & "/data/dim_carriers.csv"),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),
 Headers=Table.PromoteHeaders(Source,[PromoteAllScalars=true]),
 Clean=Headers,
 Typed=Table.TransformColumnTypes(Clean,{{"carrier_id",Int64.Type}})
in Typed