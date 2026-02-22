@app.get("/images-list/{annotator_id}")
def get_images_for_annotator(annotator_id: str):
    # כל התמונות
    if not os.path.exists(IMAGES_DIR):
        return []

    all_images = sorted(
        f for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff"))
    )

    data = load_data()

    # תמונות שכבר סומנו ע"י annotator
    done = set()
    for image_id, annotations in data.items():
        for ann in annotations:
            if ann["annotator_id"] == annotator_id:
                done.add(image_id)

    # מחזירים רק מה שנשאר
    remaining = [img for img in all_images if img not in done]
    return remaining
