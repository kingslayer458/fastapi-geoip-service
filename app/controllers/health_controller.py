from fastapi import APIRouter
router = APIRouter(tags=["Health"])


@router.get("/")
def root():

    return {
        "service": "GeoIP lookup microservice",
    }
