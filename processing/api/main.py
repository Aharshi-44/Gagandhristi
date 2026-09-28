import os
import sys
import shutil
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse


# ============================================================
# PROJECT ROOT
# ============================================================

PROCESSING_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROCESSING_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROCESSING_ROOT
    )


# ============================================================
# PROJECT IMPORT
# ============================================================

from service.processor import ChangeProcessor


# ============================================================
# RESULT STORAGE
# ============================================================

RESULTS_ROOT = os.path.join(
    PROCESSING_ROOT,
    "results"
)

os.makedirs(
    RESULTS_ROOT,
    exist_ok=True
)


# ============================================================
# PUBLIC API URL
# ============================================================

PROCESSING_PUBLIC_URL = os.getenv(
    "PROCESSING_PUBLIC_URL",
    "http://localhost:8000"
).rstrip("/")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Gagandhristi Multi-Model Processing API",
    description=(
        "Satellite multi-temporal change detection service supporting "
        "Structural Changes (Siamese U-Net), Vegetation Clearance (NDVI/VARI), "
        "and All Pixel-to-Pixel Anomalies (CVA)."
    ),
    version="2.0.0"
)


# ============================================================
# LOAD MODEL ONCE
# ============================================================

print("\n==========================================")
print(" GAGANDHRISTI PROCESSING API (MULTI-MODEL)")
print("==========================================")

processor = ChangeProcessor()

print("[OK] Processing engine ready with 3 analytical channels")


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "service": "Gagandhristi Multi-Model Processing API",
        "status": "running",
        "supported_channels": [
            {
                "id": "STRUCTURAL_DL",
                "name": "Structural Changes",
                "model": "Siamese U-Net (LEVIR-CD)",
                "category": "INFRASTRUCTURE"
            },
            {
                "id": "VEGETATION_NDVI",
                "name": "Vegetation Change",
                "model": "NDVI / VARI Multi-Temporal Index",
                "category": "ENVIRONMENTAL"
            },
            {
                "id": "PIXEL_DIFFERENCE",
                "name": "All Pixel-to-Pixel Change",
                "model": "Radiometric Change Vector Analysis (CVA)",
                "category": "TACTICAL_ANOMALY"
            }
        ],
        "threshold": processor.threshold,
        "device": str(processor.device)
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": processor.model is not None,
        "device": str(processor.device),
        "channels": ["structural", "vegetation", "pixel_diff"]
    }


# ============================================================
# PROCESS HELPER FUNCTION
# ============================================================

async def handle_change_processing(
    t1: UploadFile,
    t2: UploadFile,
    channel_type: str = "structural"
):
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/jpg",
        "image/tiff",
        "image/tif",
        "image/geotiff",
        "application/octet-stream"
    }

    t1_ext = os.path.splitext(t1.filename or ".jpeg")[1].lower()
    t2_ext = os.path.splitext(t2.filename or ".jpeg")[1].lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".geotiff"}

    if t1.content_type not in allowed_types and t1_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail="T1 must be a JPEG, PNG, or GeoTIFF image."
        )

    if t2.content_type not in allowed_types and t2_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail="T2 must be a JPEG, PNG, or GeoTIFF image."
        )

    result_id = uuid.uuid4().hex
    result_dir = os.path.join(RESULTS_ROOT, result_id)
    os.makedirs(result_dir, exist_ok=True)

    if t1_ext not in allowed_exts:
        t1_ext = ".tif" if "tiff" in (t1.content_type or "") else ".jpeg"
    if t2_ext not in allowed_exts:
        t2_ext = ".tif" if "tiff" in (t2.content_type or "") else ".jpeg"

    t1_path = os.path.join(result_dir, "T1" + t1_ext)
    t2_path = os.path.join(result_dir, "T2" + t2_ext)
    mask_path = os.path.join(result_dir, "change_mask.png")

    try:
        with open(t1_path, "wb") as buffer:
            shutil.copyfileobj(t1.file, buffer)

        with open(t2_path, "wb") as buffer:
            shutil.copyfileobj(t2.file, buffer)

        result = processor.process(
            t1_path,
            t2_path,
            output_mask_path=mask_path,
            channel_type=channel_type
        )

        overlay_path = os.path.join(result_dir, "change_overlay.png")

        if not os.path.exists(mask_path):
            raise RuntimeError("Change mask was not generated.")

        if not os.path.exists(overlay_path):
            raise RuntimeError("Change overlay was not generated.")

        mask_url = f"{PROCESSING_PUBLIC_URL}/results/{result_id}/mask"
        overlay_url = f"{PROCESSING_PUBLIC_URL}/results/{result_id}/overlay"

        result["result_id"] = result_id
        result["output_mask"] = mask_url
        result["overlay_image"] = overlay_url

        # Check for generated GeoTIFF web previews
        if "t1_preview" in result and os.path.exists(result["t1_preview"]):
            result["t1_preview"] = f"{PROCESSING_PUBLIC_URL}/results/{result_id}/t1-preview"
        if "t2_preview" in result and os.path.exists(result["t2_preview"]):
            result["t2_preview"] = f"{PROCESSING_PUBLIC_URL}/results/{result_id}/t2-preview"

        result["inputs"] = {
            "t1_filename": t1.filename,
            "t2_filename": t2.filename,
            "channel_type": channel_type
        }

        return result

    except Exception as error:
        try:
            if os.path.exists(result_dir):
                shutil.rmtree(result_dir)
        except Exception:
            pass

        raise HTTPException(status_code=500, detail=str(error))

    finally:
        await t1.close()
        await t2.close()


# ============================================================
# UNIFIED PROCESS ENDPOINT (BACKWARD COMPATIBLE)
# ============================================================

@app.post("/process")
async def process_images(
    t1: UploadFile = File(...),
    t2: UploadFile = File(...),
    channel_type: str = Form("structural")
):
    """
    Main processing endpoint. Supports channel_type parameter:
    - 'structural' (Siamese U-Net - default)
    - 'vegetation' (NDVI / VARI index)
    - 'pixel_diff' (Pixel-to-pixel CVA)
    """
    return await handle_change_processing(t1, t2, channel_type=channel_type)


# ============================================================
# DEDICATED CONVENIENCE ENDPOINTS
# ============================================================

@app.post("/process/structural")
async def process_structural(
    t1: UploadFile = File(...),
    t2: UploadFile = File(...)
):
    return await handle_change_processing(t1, t2, channel_type="structural")


@app.post("/process/vegetation")
async def process_vegetation(
    t1: UploadFile = File(...),
    t2: UploadFile = File(...)
):
    return await handle_change_processing(t1, t2, channel_type="vegetation")


@app.post("/process/pixel-diff")
async def process_pixel_diff(
    t1: UploadFile = File(...),
    t2: UploadFile = File(...)
):
    return await handle_change_processing(t1, t2, channel_type="pixel_diff")


# ============================================================
# SERVE CHANGE MASK
# ============================================================

@app.get("/results/{result_id}/mask")
def get_change_mask(result_id: str):
    mask_path = os.path.join(RESULTS_ROOT, result_id, "change_mask.png")

    if not os.path.isfile(mask_path):
        raise HTTPException(status_code=404, detail="Change mask not found.")

    return FileResponse(mask_path, media_type="image/png", filename="change_mask.png")


# ============================================================
# SERVE CHANGE OVERLAY
# ============================================================

@app.get("/results/{result_id}/overlay")
def get_change_overlay(result_id: str):
    overlay_path = os.path.join(RESULTS_ROOT, result_id, "change_overlay.png")

    if not os.path.isfile(overlay_path):
        raise HTTPException(status_code=404, detail="Change overlay not found.")

    return FileResponse(overlay_path, media_type="image/png", filename="change_overlay.png")


# ============================================================
# SERVE GEOTIFF WEB PREVIEWS
# ============================================================

@app.get("/results/{result_id}/t1-preview")
def get_t1_preview(result_id: str):
    preview_path = os.path.join(RESULTS_ROOT, result_id, "T1_preview.png")

    if not os.path.isfile(preview_path):
        raise HTTPException(status_code=404, detail="T1 preview not found.")

    return FileResponse(preview_path, media_type="image/png", filename="T1_preview.png")


@app.get("/results/{result_id}/t2-preview")
def get_t2_preview(result_id: str):
    preview_path = os.path.join(RESULTS_ROOT, result_id, "T2_preview.png")

    if not os.path.isfile(preview_path):
        raise HTTPException(status_code=404, detail="T2 preview not found.")

    return FileResponse(preview_path, media_type="image/png", filename="T2_preview.png")


# ============================================================
# MODEL INFO
# ============================================================

@app.get("/model-info")
def model_info():
    return {
        "active_models": [
            {
                "channel_id": "STRUCTURAL_DL",
                "name": "Structural Changes",
                "framework": "PyTorch Siamese U-Net",
                "pretraining": "LEVIR-CD Building Dataset",
                "threshold": processor.threshold,
                "input_channels": 3,
                "output_overlay": "Red highlight over T2"
            },
            {
                "channel_id": "VEGETATION_NDVI",
                "name": "Vegetation Change",
                "framework": "NumPy / OpenCV Remote Sensing Indices",
                "formula": "NDVI = (NIR-Red)/(NIR+Red) or VARI = (Green-Red)/(Green+Red-Blue)",
                "threshold": 0.12,
                "output_overlay": "Red (Clearance) & Green (Regrowth) over T2"
            },
            {
                "channel_id": "PIXEL_DIFFERENCE",
                "name": "All Pixel-to-Pixel Change",
                "framework": "Radiometric Change Vector Analysis (CVA)",
                "formula": "Euclidean Euclidean distance + adaptive morphological cleaning",
                "threshold": 0.18,
                "output_overlay": "Amber / Orange tactical anomaly highlight over T2"
            }
        ],
        "device": str(processor.device)
    }


# ============================================================
# SEMANTIC & MULTIMODAL RETRIEVAL (PS 2.2.1)
# ============================================================

from typing import Optional
from pydantic import BaseModel
from inference.semantic_retrieval import SemanticRetrievalEngine

def get_retrieval_engine():
    return SemanticRetrievalEngine.get_instance()

from fastapi import Request

@app.post("/retrieve/text")
async def retrieve_by_text(request: Request):
    """
    Zero-shot natural language free-text retrieval over satellite imagery catalog (PS 2.2.1).
    Accepts JSON body or multipart/form-data.
    """
    search_query = None
    k = 5

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            search_query = body.get("query")
            k = int(body.get("top_k", 5))
        except Exception:
            pass
    else:
        form = await request.form()
        search_query = form.get("query")
        k = int(form.get("top_k", 5))

    if not search_query or not str(search_query).strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    engine = get_retrieval_engine()
    results = engine.retrieve_by_text(query=str(search_query).strip(), top_k=k)

    return {
        "status": "success",
        "query": str(search_query).strip(),
        "match_count": len(results),
        "results": results
    }

@app.post("/retrieve/image")
async def retrieve_by_image(
    query_image: UploadFile = File(...),
    top_k: int = Form(5)
):
    """
    Query-by-example visual similarity search across satellite tile catalog (PS 2.2.1).
    """
    content = await query_image.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty query image provided.")

    engine = get_retrieval_engine()
    results = engine.retrieve_by_image(query_image_bytes=content, top_k=int(top_k))

    return {
        "status": "success",
        "query_filename": query_image.filename,
        "match_count": len(results),
        "results": results
    }

@app.get("/retrieve/catalog")
def get_catalog():
    """
    Lists all indexed satellite tiles in the semantic retrieval catalog.
    """
    engine = get_retrieval_engine()
    tiles = engine.get_catalog_summary(limit=50)
    return {
        "status": "success",
        "catalog_size": engine.catalog_size,
        "tiles": tiles
    }