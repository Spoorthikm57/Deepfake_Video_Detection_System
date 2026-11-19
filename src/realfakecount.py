import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV
csv_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\dataset_labels.csv"
df = pd.read_csv(csv_path)

# Count REAL and FAKE videos
counts = df['label'].value_counts()
print("Number of videos per class:")
print(counts)

# Compute percentages
total = len(df)
percent_real = (counts.get('REAL', 0) / total) * 100
percent_fake = (counts.get('FAKE', 0) / total) * 100
print(f"\nPercentage of REAL videos: {percent_real:.2f}%")
print(f"Percentage of FAKE videos: {percent_fake:.2f}%")

# Optional: visualize the distribution
counts.plot(kind='bar', color=['green', 'red'])
plt.title("Distribution of REAL vs FAKE Videos")
plt.ylabel("Number of videos")
plt.show()
