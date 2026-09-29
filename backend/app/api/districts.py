from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/districts")
def get_districts(request: Request) -> dict:
    """District polygons as GeoJSON, straight from the scenario (the only source of district shapes)."""
    world = request.app.state.demo.world
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": d["id"],
                "properties": {
                    "id": d["id"], "name": d["name"], "centroid": d["centroid"], "neighbours": d["neighbours"],
                },
                "geometry": {"type": "Polygon", "coordinates": d["polygon"]},
            }
            for d in world.districts
        ],
    }
