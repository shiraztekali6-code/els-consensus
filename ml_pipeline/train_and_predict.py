# =====================================================
# INSTALL
# =====================================================
!pip install pandas numpy scikit-learn torch torchvision umap-learn seaborn openpyxl

# =====================================================
# IMPORTS
# =====================================================
import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
import umap
import seaborn as sns
import matplotlib.pyplot as plt

# =====================================================
# CONFIG
# =====================================================
CONSENSUS_CSV = "consensus.csv"
NEW_IMAGES_FOLDER = "new_images/"
METADATA_FILE = "metadata.xlsx"
IMAGE_FOLDER = "images/"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =====================================================
# LOAD DATA
# =====================================================
df = pd.read_csv(CONSENSUS_CSV)

if "image_id" not in df.columns:
    raise ValueError("CSV must contain 'image_id' column")

df["image_path"] = df["image_id"].apply(lambda x: os.path.join(IMAGE_FOLDER, f"{x}.png"))

feature_cols = [c for c in df.columns if c not in ["image_id", "image_path"]]

# =====================================================
# IMAGE TRANSFORM
# =====================================================
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

def load_image(path):
    img = Image.open(path).convert("RGB")
    return transform(img)

# =====================================================
# FEATURE EXTRACTOR (ResNet)
# =====================================================
resnet = models.resnet18(pretrained=True)
feature_extractor = nn.Sequential(*list(resnet.children())[:-1])
feature_extractor = feature_extractor.to(DEVICE)
feature_extractor.eval()

def extract_embedding(img_tensor):
    with torch.no_grad():
        emb = feature_extractor(img_tensor.unsqueeze(0).to(DEVICE))
    return emb.cpu().numpy().flatten()

# =====================================================
# BUILD TRAIN EMBEDDINGS
# =====================================================
embeddings = []
valid_indices = []

for i, row in df.iterrows():
    path = row["image_path"]
    if not os.path.exists(path):
        continue
    try:
        img = load_image(path)
        emb = extract_embedding(img)
        embeddings.append(emb)
        valid_indices.append(i)
    except:
        continue

df_valid = df.iloc[valid_indices].reset_index(drop=True)
X = np.array(embeddings)
y = df_valid[feature_cols].values

print("Embeddings shape:", X.shape)

# =====================================================
# TRAIN MODEL (MULTI-LABEL)
# =====================================================
model = MultiOutputClassifier(
    RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
)

model.fit(X, y)

# =====================================================
# PREDICT NEW IMAGES
# =====================================================
results = []

for fname in os.listdir(NEW_IMAGES_FOLDER):
    if not fname.endswith(".png"):
        continue

    path = os.path.join(NEW_IMAGES_FOLDER, fname)

    try:
        img = load_image(path)
        emb = extract_embedding(img)

        pred = model.predict([emb])[0]

        row = dict(zip(feature_cols, pred))
        row["image_id"] = fname.replace(".png", "")

        results.append(row)

    except:
        continue

pred_df = pd.DataFrame(results)

# =====================================================
# DEFINE BIOLOGY FUNCTIONS
# =====================================================
def is_els(row):
    return int(row.get("b_cells", 0) or row.get("t_cells", 0))

def maturity_score(row):
    return (
        row.get("ki67", 0) +
        row.get("b_t_separation", 0) +
        row.get("t_cell_ring", 0)
    )

pred_df["ELS"] = pred_df.apply(is_els, axis=1)
pred_df["maturity_score"] = pred_df.apply(maturity_score, axis=1)

# =====================================================
# UMAP
# =====================================================
umap_model = umap.UMAP(n_neighbors=10, min_dist=0.3, random_state=42)
embedding_2d = umap_model.fit_transform(pred_df[feature_cols].values)

pred_df["UMAP1"] = embedding_2d[:, 0]
pred_df["UMAP2"] = embedding_2d[:, 1]

plt.figure()
plt.scatter(pred_df["UMAP1"], pred_df["UMAP2"])
plt.title("UMAP of Predicted ELS")
plt.show()

# =====================================================
# HEATMAP
# =====================================================
sns.clustermap(pred_df[feature_cols], cmap="viridis")
plt.show()

# =====================================================
# MERGE WITH METADATA
# =====================================================
if os.path.exists(METADATA_FILE):
    meta = pd.read_excel(METADATA_FILE)
    final_df = pred_df.merge(meta, on="image_id", how="left")
else:
    final_df = pred_df

# =====================================================
# SAVE OUTPUT
# =====================================================
final_df.to_excel("ELS_predictions_final.xlsx", index=False)

print("Done! Saved to ELS_predictions_final.xlsx")
