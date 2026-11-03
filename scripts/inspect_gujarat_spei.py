
from pathlib import Path
import pandas as pd

folder = Path("data/raw/drought_atlas_gujarat_districts")

files = sorted(
    f for f in folder.iterdir()
    if f.name.startswith("data_distwise_id_")
)

print("Total district files:", len(files))

for file in files[:3]:
    print("\nFILE:", file.name)

    df = pd.read_csv(
        file,
        sep=r"\s+",
        header=None,
        na_values=["NaN", "nan"]
    )

    print("Shape:", df.shape)
    print("First 5 rows:")
    print(df.head())
    print("Column count:", len(df.columns))
