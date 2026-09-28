"""
High-Speed Vector Indexing Script for Gagandristhi V2 Semantic Retrieval Engine
Extracts 512-dim normalized feature embeddings across the satellite image dataset
using OpenAI CLIP ViT-B/32 accelerated on NVIDIA CUDA.
Saves precomputed index to processing/weights/ for sub-millisecond search at runtime.
"""

import os
import sys
import time
import json
import torch
from PIL import Image
from typing import List, Dict, Any

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from transformers import CLIPProcessor, CLIPModel

def _extract_embed(output):
    if hasattr(output, "pooler_output") and output.pooler_output is not None:
        return output.pooler_output
    elif hasattr(output, "image_embeds") and output.image_embeds is not None:
        return output.image_embeds
    elif isinstance(output, (tuple, list)):
        return output[0]
    return output

def build_index(batch_size: int = 64):
    print("=" * 65)
    print(" GAGANDRISTHI V2: BATCH SEMANTIC INDEX BUILDER (CLIP ViT-B/32)")
    print("=" * 65)

    test_images_dir = os.path.join(ROOT, "test_images")
    weights_dir = os.path.join(ROOT, "weights")
    os.makedirs(weights_dir, exist_ok=True)

    output_embeddings_path = os.path.join(weights_dir, "semantic_embeddings.pt")
    output_metadata_path = os.path.join(weights_dir, "semantic_metadata.json")

    # 1. Discover all candidate images (excluding mask overlays)
    excluded_prefixes = ("mask_", "change_overlay", "processor_mask")
    valid_exts = {".png", ".jpg", ".jpeg"}

    image_paths = []
    for fname in os.listdir(test_images_dir):
        ext = os.path.splitext(fname)[1].lower()
        if ext in valid_exts and not fname.startswith(excluded_prefixes):
            image_paths.append(os.path.join(test_images_dir, fname))

    # Natural sorting so tiles appear in numerical order (1.png, 2.png, ...)
    def sort_key(p):
        base = os.path.splitext(os.path.basename(p))[0]
        return (0, int(base)) if base.isdigit() else (1, base)

    image_paths.sort(key=sort_key)
    total_images = len(image_paths)
    print(f"[*] Discovered {total_images} satellite images in {test_images_dir}")

    if total_images == 0:
        print("[ERROR] No valid images found to index!")
        return False

    # 2. Initialize Model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Initializing OpenAI CLIP ViT-B/32 on: {device.upper()}")
    if device == "cuda":
        print(f"    GPU Device: {torch.cuda.get_device_name(0)}")

    model_name = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name).to(device)
    model.eval()

    # 3. Batch Extraction Loop
    all_embeddings = []
    metadata_list = []

    print(f"[*] Starting batch inference (Batch Size: {batch_size})...")
    start_time = time.time()

    for i in range(0, total_images, batch_size):
        batch_paths = image_paths[i:i + batch_size]
        batch_images = []
        valid_indices = []

        for b_idx, path in enumerate(batch_paths):
            try:
                img = Image.open(path).convert("RGB")
                batch_images.append(img)
                valid_indices.append(b_idx)
            except Exception as e:
                print(f"    [WARN] Failed to open {os.path.basename(path)}: {e}")

        if not batch_images:
            continue

        try:
            inputs = processor(images=batch_images, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                out = model.get_image_features(**inputs)
                embeds = _extract_embed(out)
                embeds = embeds / embeds.norm(dim=-1, keepdim=True)
                embeds = embeds.cpu()

            all_embeddings.append(embeds)

            for b_idx, img in zip(valid_indices, batch_images):
                path = batch_paths[b_idx]
                fname = os.path.basename(path)
                tile_id = f"tile_{os.path.splitext(fname)[0]}"
                metadata_list.append({
                    "tile_id": tile_id,
                    "filename": fname,
                    "name": f"Satellite Tile #{os.path.splitext(fname)[0]}",
                    "category": "SATELLITE_CATALOG",
                    "description": f"Earth observation multi-spectral satellite scene ({fname})",
                    "dimensions": f"{img.width}x{img.height}"
                })

        except Exception as e:
            print(f"    [ERROR] Batch {i} to {i+batch_size} failed: {e}")

        processed_so_far = min(i + batch_size, total_images)
        pct = (processed_so_far / total_images) * 100
        elapsed = time.time() - start_time
        speed = processed_so_far / max(0.1, elapsed)
        sys.stdout.write(f"\r  -> Progress: {processed_so_far}/{total_images} ({pct:.1f}%) | Speed: {speed:.1f} tiles/sec")
        sys.stdout.flush()

    total_time = time.time() - start_time
    print(f"\n[OK] Feature extraction complete in {total_time:.2f} seconds ({len(metadata_list)} tiles processed)")

    # 4. Save Embeddings Tensor Matrix
    final_embeddings = torch.cat(all_embeddings, dim=0)  # Shape: (N, 512)
    print(f"[*] Saving vector index matrix: shape={list(final_embeddings.shape)} to {output_embeddings_path}...")
    torch.save(final_embeddings, output_embeddings_path)

    # 5. Save Metadata
    print(f"[*] Saving catalog metadata to {output_metadata_path}...")
    with open(output_metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=2)

    emb_size_mb = os.path.getsize(output_embeddings_path) / (1024 * 1024)
    meta_size_kb = os.path.getsize(output_metadata_path) / 1024

    print("=" * 65)
    print(" INDEX CREATED SUCCESSFULLY!")
    print(f" Total Tiles Indexed:  {len(metadata_list)}")
    print(f" Embedding Matrix:     {output_embeddings_path} ({emb_size_mb:.2f} MB)")
    print(f" Metadata Catalogue:   {output_metadata_path} ({meta_size_kb:.1f} KB)")
    print(f" Total Elapsed Time:   {total_time:.2f} seconds")
    print("=" * 65)
    return True

if __name__ == "__main__":
    success = build_index(batch_size=64)
    sys.exit(0 if success else 1)
