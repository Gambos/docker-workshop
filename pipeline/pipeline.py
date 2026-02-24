from calendar import month
import sys
import pandas as pd

print("arguments", sys.argv)
day = int(sys.argv[1])
print(f"Running pipeline for day {day}")

df = pd.DataFrame({"day": [1, 2], "num_passengers": [3, 4]})
month = 2 
df['month'] = month
print(df.head())
df.to_parquet(f"output_{month}.parquet")

