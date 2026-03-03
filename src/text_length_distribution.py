import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv("https://huggingface.co/datasets/COLX523/Misinformation/resolve/main/cleaned_dataset.csv")

df["text_length"] = df["text"].str.len()

plt.figure(figsize=(12, 6))
plt.hist(df["text_length"], bins=100, edgecolor="black")
plt.xlabel("Text Length (characters)")
plt.ylabel("Number of Rows")
plt.title("Distribution of Text Lengths")
plt.axvline(x=1000, color="red", linestyle="--", label="1000 char threshold")
plt.legend()
plt.yscale("log")  # log scale 
plt.savefig("../reports/text_len_dist.png")
plt.close()


plt.figure(figsize=(12, 6))
plt.hist(df["text_length"], bins=100, edgecolor="black")
plt.xlabel("Text Length (characters)")
plt.ylabel("Number of Rows")
plt.title("Distribution of Text Lengths (0-2000 chars)")
plt.xlim(0, 2000)
plt.axvline(x=280, color="red", linestyle="--", label="280 char (Twitter limit)")
plt.axvline(x=560, color="orange", linestyle="--", label="560 char (2x tweets)")
plt.legend()
plt.savefig("../reports/text_len_dist_0-2000_chars.png")
plt.close()
