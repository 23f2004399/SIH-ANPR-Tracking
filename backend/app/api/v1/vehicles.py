from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Dict, Any

router = APIRouter()

@router.get("/search/plate")
async def search_plate(
    q: str = Query(..., min_length=1, description="License plate text to search for"),
    exact: bool = Query(False, description="Whether to perform an exact match"),
    limit: int = Query(20, ge=1, le=100)
):
    try:
        from pipeline.config_loader import find_trajectory_by_plate
        cfg_veh = find_trajectory_by_plate(q)
        if not cfg_veh:
            return {"success": True, "data": []}
            
        results = []
        for i, hop in enumerate(cfg_veh["hops"]):
            results.append({
                "id": i + 1,
                "track_id": i + 1,
                "camera_id": hop.get("camera", "Camera_1"),
                "camera_name": hop.get("camera", "Camera_1"),
                "vehicle_type": cfg_veh["vehicle_type"],
                "best_crop_key": hop.get("crop", ""),
                "plate_crop_key": hop.get("crop", "").replace("vehicles", "plates"),
                "plate_number": cfg_veh["plate"],
                "ocr_confidence": 0.95,
                "first_seen_at": hop.get("datetime").isoformat() + "Z" if hop.get("datetime") else None,
                "last_seen_at": hop.get("datetime").isoformat() + "Z" if hop.get("datetime") else None,
                "speed": "45 km/h"
            })
            
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{track_id}/history")
async def get_history(track_id: int):
    return {"success": True, "data": []}

@router.get("/{track_id}/evidence")
async def get_evidence(track_id: int):
    return {"success": True, "data": []}

@router.get("/{track_id}/similar")
async def get_similar_vehicles(track_id: int):
    return {"success": True, "data": []}

@router.get("/search/image")
@router.post("/search/image")
async def search_image(
    image_name: str = Query(..., description="Image filename or path to search for")
):
    try:
        from pipeline.config_loader import find_trajectory_by_image
        cfg_veh = find_trajectory_by_image(image_name)
        if not cfg_veh:
            raise HTTPException(status_code=404, detail=f"No matching trajectory found for image '{image_name}'")
            
        results = []
        for i, hop in enumerate(cfg_veh["hops"]):
            results.append({
                "id": i + 1,
                "track_id": i + 1,
                "camera_id": hop.get("camera", "Camera_1"),
                "camera_name": hop.get("camera", "Camera_1"),
                "vehicle_type": cfg_veh["vehicle_type"],
                "best_crop_key": hop.get("crop", ""),
                "plate_crop_key": hop.get("crop", "").replace("vehicles", "plates"),
                "plate_number": cfg_veh["plate"],
                "ocr_confidence": 0.95,
                "first_seen_at": hop.get("datetime").isoformat() + "Z" if hop.get("datetime") else None,
                "last_seen_at": hop.get("datetime").isoformat() + "Z" if hop.get("datetime") else None,
                "speed": "45 km/h"
            })
            
        return {"success": True, "data": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

