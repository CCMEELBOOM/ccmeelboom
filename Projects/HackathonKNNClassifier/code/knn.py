import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (needed on some Matplotlib versions)
from collections import Counter
from sklearn.metrics import classification_report, confusion_matrix

# simulated dataset 
data = pd.read_csv(r"C:\Users\ccmee\Documents\sdsu-hackathon\Backend\data_sort\trash_knn_synth_v1.csv")


# type of sensor data collected
features = ["transparency_0_1", "nir_organic_idx", "acoustic_peak_hz"]
X = data[features].to_numpy(float)
y = data["class"].to_numpy()

# split; 20% of data for testing and 80% for training
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=2, stratify=y
)

# 3D scatter plot of data concentration 
fig = plt.figure(figsize=(7,6))
ax = fig.add_subplot(111, projection="3d")

colors = {"compostable":"tab:green", "recyclable":"tab:blue", "landfill":"tab:red"}
markers = {"compostable":"o", "recyclable":"^", "landfill":"s"}

for cls in colors:
    m = (y_train == cls)
    ax.scatter(
        X_train[m, 0], X_train[m, 1], X_train[m, 2],
        s=14, alpha=0.7, color=colors[cls], marker=markers[cls], label=cls
    )

ax.set_xlabel(features[0])
ax.set_ylabel(features[1])
ax.set_zlabel(features[2])

# nice initial view; tweak as you like
ax.view_init(elev=22, azim=45)
# optional: acoustic can be large; log Z helps readability
# ax.set_zscale('log')

ax.legend()
plt.tight_layout()
plt.show()


def euclidean_distance(a,b):
    return np.sqrt(np.sum((a-b)**2))

class KNN:
    def __init__(self, k):
        self.k = int(k)

    def fit(self, x, y):
        self.X_train = np.asarray(x, float)   # (n_samples, n_features)
        self.y_train = np.asarray(y)

    def predict(self, new_points):
        P = np.atleast_2d(np.asarray(new_points, float))  # (m, n_features)
        predictions = [self.predict_class(p) for p in P]
        return np.array(predictions)

    def predict_class(self, new_point):
        # vectorized distance is faster, but your loop is fine:
        dists = np.linalg.norm(self.X_train - new_point, axis=1)
        k_indices = np.argpartition(dists, self.k - 1)[: self.k]
        k_nearest_labels = self.y_train[k_indices]
        return Counter(k_nearest_labels).most_common(1)[0][0]

# Training and evaluation; adjust K to change fine tune for accuracy 
knn = KNN(16)
knn.fit(X_train, y_train)
predictions = knn.predict(X_test)
accuracy = np.mean(predictions == y_test) * 100
print(f"Accuracy: {accuracy:.2f}%")

# X_test: shape (n, 3)
# y_test, predictions: arrays of strings: 'compostable'|'recyclable'|'landfill'
# features: list of 3 feature names

color_map = {
    "compostable": "tab:green",
    "recyclable":  "tab:blue",
    "landfill":    "tab:red",
}

fig = plt.figure(figsize=(7,6))
ax = fig.add_subplot(111, projection="3d")

# TRUE labels (filled markers)
for cls, color in color_map.items():
    m = (y_test == cls)
    ax.scatter(
        X_test[m, 0], X_test[m, 1], X_test[m, 2],
        s=20, alpha=0.5, color=color, marker="o", label=f"True {cls}"
    )

# PREDICTIONS (hollow markers with colored edges)
for cls, color in color_map.items():
    m = (predictions == cls)
    ax.scatter(
        X_test[m, 0], X_test[m, 1], X_test[m, 2],
        s=50, facecolors="none", edgecolors=color, linewidths=1.5,
        marker="o", label=f"Pred {cls}"
    )

ax.set_xlabel(features[0])
ax.set_ylabel(features[1])
ax.set_zlabel(features[2])
ax.view_init(elev=22, azim=45)
ax.legend(loc="upper left", ncol=2, fontsize=8)
plt.tight_layout()
plt.show()