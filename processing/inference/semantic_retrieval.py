import os
import io
import base64
import torch
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional
from transformers import CLIPProcessor, CLIPModel

def _extract_embed(output):
    """Safely extracts 2D tensor embedding from various transformers CLIP output formats."""
    if hasattr(output, "pooler_output") and output.pooler_output is not None:
        return output.pooler_output
    elif hasattr(output, "image_embeds") and output.image_embeds is not None:
        return output.image_embeds
    elif hasattr(output, "text_embeds") and output.text_embeds is not None:
        return output.text_embeds
    elif isinstance(output, (tuple, list)):
        return output[0]
    return output

class SemanticRetrievalEngine:
    """
    Semantic & Multimodal Retrieval Engine for Satellite Imagery (PS 2.2.1).
    Utilizes OpenAI CLIP Vision-Language Foundation Model on CUDA for zero-shot
    free-text search and query-by-example visual similarity matching.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[SemanticRetrieval] Loading Vision-Language CLIP model on {self.device}...")
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

        # In-memory index of catalog tiles
        # tile_id -> {"tile_id", "name", "category", "description", "embedding", "thumbnail_b64"}
        self.tile_index: Dict[str, Dict[str, Any]] = {}
        self._initialize_catalog()

    def _get_thumbnail_base64(self, image: Image.Image, size=(180, 180)) -> str:
        thumb = image.copy()
        thumb.thumbnail(size)
        buffer = io.BytesIO()
        thumb.save(buffer, format="JPEG", quality=85)
        return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    def index_image(self, tile_id: str, image_source, name: str, category: str = "GENERAL", description: str = ""):
        """
        Computes 512-dim normalized feature embedding for a satellite image and stores in vector index.
        """
        try:
            if isinstance(image_source, str):
                image = Image.open(image_source).convert("RGB")
            elif isinstance(image_source, Image.Image):
                image = image_source.convert("RGB")
            else:
                image = Image.open(io.BytesIO(image_source)).convert("RGB")

            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                out = self.model.get_image_features(**inputs)
                img_embed = _extract_embed(out)
                img_embed = img_embed / img_embed.norm(dim=-1, keepdim=True)
                img_embed = img_embed.cpu().squeeze(0)

            thumb_b64 = self._get_thumbnail_base64(image)
            self.tile_index[tile_id] = {
                "tile_id": tile_id,
                "name": name,
                "category": category,
                "description": description,
                "embedding": img_embed,
                "thumbnail_b64": thumb_b64,
                "dimensions": f"{image.width}x{image.height}"
            }
            print(f"[SemanticRetrieval] Indexed tile: {tile_id} ({name}) - {category}")
        except Exception as e:
            print(f"[SemanticRetrieval] Error indexing {tile_id}: {e}")

    def _initialize_catalog(self):
        """Indexes default sample satellite tiles and scenes on startup."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_images_dir = os.path.join(base_dir, "test_images")

        default_tiles = [
            ("tile_pre_infrastructure", "T1.jpeg", "Sector Alpha - Pre-Event Rural Settlement", "INFRASTRUCTURE", "Pre-event optical satellite tile showing rural buildings, road corridors, and farmland"),
            ("tile_post_construction", "T2.jpeg", "Sector Alpha - Post-Event Urban Expansion", "INFRASTRUCTURE", "Post-event optical satellite tile showing newly constructed military/industrial structures and excavation"),
            ("tile_structural_mask", "mask_structural.png", "Structural Anomaly Detection Mask", "TACTICAL_ANOMALY", "Bi-temporal deep learning binary mask isolating new structure footprints"),
            ("tile_vegetation_delta", "mask_vegetation.png", "Vegetation Variance & Soil Disruption", "ENVIRONMENTAL", "NDVI difference map depicting soil clearance and deforestation"),
            ("tile_cva_radiometric", "mask_pixel_diff.png", "Radiometric Change Vector Magnitude", "TACTICAL_ANOMALY", "Multi-spectral CVA radiometric anomaly highlighting high-reflectance earthworks"),
            ("tile_multitemporal_scene", "visual_comparison.png", "Comprehensive Multi-Sensor Surveillance Tile", "GENERAL", "Multi-panel analytical overview comparing structural, vegetation, and spectral shifts")
        ]

        for tile_id, filename, name, category, desc in default_tiles:
            path = os.path.join(test_images_dir, filename)
            if os.path.exists(path):
                self.index_image(tile_id, path, name, category, desc)

        print(f"[SemanticRetrieval] Catalog initialized with {len(self.tile_index)} indexed satellite tiles.")

    def retrieve_by_text(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes zero-shot natural language search over the indexed satellite tile catalog.
        Computes cosine similarity between text prompt embedding and all tile visual embeddings.
        """
        if not self.tile_index:
            return []

        # Enhance query with satellite context
        context_query = f"satellite aerial imagery of {query.strip()}"
        inputs = self.processor(text=[context_query, query], return_tensors="pt", padding=True).to(self.device)

        with torch.no_grad():
            out = self.model.get_text_features(**inputs)
            text_embeds = _extract_embed(out)
            text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
            # Use average of contextualized and direct embedding
            text_embed = text_embeds.mean(dim=0, keepdim=True)
            text_embed = text_embed / text_embed.norm(dim=-1, keepdim=True)
            text_embed = text_embed.cpu().squeeze(0)

        results = []
        for tile_id, item in self.tile_index.items():
            img_embed = item["embedding"]
            cosine_sim = float(torch.dot(text_embed, img_embed).item())
            # Scale cosine similarity [-1, 1] to percentage [0%, 100%]
            calibrated_score = round(max(0.0, min(100.0, (cosine_sim - 0.10) / 0.25 * 100.0)), 1)

            confidence_label = "HIGH_CONFIDENCE" if calibrated_score >= 70.0 else ("MODERATE_MATCH" if calibrated_score >= 45.0 else "LOW_CORRELATION")

            results.append({
                "tile_id": tile_id,
                "name": item["name"],
                "category": item["category"],
                "description": item["description"],
                "raw_cosine_similarity": round(cosine_sim, 4),
                "similarity_score": calibrated_score,
                "confidence_label": confidence_label,
                "dimensions": item.get("dimensions", "N/A"),
                "thumbnail_b64": item["thumbnail_b64"]
            })

        # Sort descending by similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_results = results[:top_k]
        for rank, res in enumerate(top_results, 1):
            res["rank"] = rank

        return top_results

    def retrieve_by_image(self, query_image_bytes: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes Query-by-Example visual similarity search.
        Given a query image/crop, retrieves visually matching tiles from the satellite catalog.
        """
        if not self.tile_index:
            return []

        query_image = Image.open(io.BytesIO(query_image_bytes)).convert("RGB")
        inputs = self.processor(images=query_image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            out = self.model.get_image_features(**inputs)
            q_embed = _extract_embed(out)
            q_embed = q_embed / q_embed.norm(dim=-1, keepdim=True)
            q_embed = q_embed.cpu().squeeze(0)

        results = []
        for tile_id, item in self.tile_index.items():
            img_embed = item["embedding"]
            cosine_sim = float(torch.dot(q_embed, img_embed).item())
            calibrated_score = round(max(0.0, min(100.0, (cosine_sim - 0.40) / 0.55 * 100.0)), 1)

            confidence_label = "EXACT_OR_HIGH" if calibrated_score >= 75.0 else ("SIMILAR_TARGET" if calibrated_score >= 50.0 else "DISSIMILAR")

            results.append({
                "tile_id": tile_id,
                "name": item["name"],
                "category": item["category"],
                "description": item["description"],
                "raw_cosine_similarity": round(cosine_sim, 4),
                "similarity_score": calibrated_score,
                "confidence_label": confidence_label,
                "dimensions": item.get("dimensions", "N/A"),
                "thumbnail_b64": item["thumbnail_b64"]
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_results = results[:top_k]
        for rank, res in enumerate(top_results, 1):
            res["rank"] = rank

        return top_results

    def get_catalog_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "tile_id": item["tile_id"],
                "name": item["name"],
                "category": item["category"],
                "description": item["description"],
                "dimensions": item.get("dimensions", "N/A"),
                "thumbnail_b64": item["thumbnail_b64"]
            }
            for item in self.tile_index.values()
        ]
