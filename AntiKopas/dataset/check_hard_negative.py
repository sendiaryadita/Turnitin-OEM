import pandas as pd


FILE = "dataset/hard_negative_dataset.csv"

df = pd.read_csv(FILE)

print("=" * 60)
print("CHECK HARD NEGATIVE DATASET")
print("=" * 60)

print(f"Total data : {len(df)}")
print(f"Label 1    : {(df['label'] == 1).sum()}")
print(f"Label 0    : {(df['label'] == 0).sum()}")

print("\n" + "=" * 60)
print("CONTOH DATA")
print("=" * 60)

for i, row in df.head(10).iterrows():

    print(f"\nDATA {i + 1}")
    print("-" * 60)

    print("TEXT A:")
    print(row["text_a"])

    print("\nTEXT B:")
    print(row["text_b"])

    print("\nLABEL:")
    print(row["label"])