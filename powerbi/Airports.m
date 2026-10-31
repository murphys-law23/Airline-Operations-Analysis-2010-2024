let
 Source=Csv.Document(File.Contents(DataRoot & "/data/dim_airports.csv"),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),
 Headers=Table.PromoteHeaders(Source,[PromoteAllScalars=true]),
 Clean=Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,{"latitude","longitude"}),
 Typed=Table.TransformColumnTypes(Clean,{{"latitude",type number},{"longitude",type number}})
in Typed