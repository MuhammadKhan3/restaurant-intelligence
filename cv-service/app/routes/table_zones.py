"""Table zone configuration routes: create/read/update/delete, persisted to disk."""

from fastapi import APIRouter, HTTPException, Request, Response

from app.tables.models import TableZone

router = APIRouter(prefix="/table-zones", tags=["table-zones"])


def _persist(request: Request) -> None:
    store = request.app.state.table_zone_store
    store.save(request.app.state.settings.table_zones_file)


@router.get("", response_model=list[TableZone])
def list_table_zones(request: Request) -> list[TableZone]:
    return request.app.state.table_zone_store.list()


@router.post("", response_model=TableZone, status_code=201)
def create_table_zone(zone: TableZone, request: Request) -> TableZone:
    store = request.app.state.table_zone_store
    try:
        created = store.create(zone)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    _persist(request)
    return created


@router.get("/{zone_id}", response_model=TableZone)
def get_table_zone(zone_id: str, request: Request) -> TableZone:
    zone = request.app.state.table_zone_store.get(zone_id)
    if zone is None:
        raise HTTPException(status_code=404, detail=f"Table zone not found: {zone_id}")
    return zone


@router.put("/{zone_id}", response_model=TableZone)
def update_table_zone(zone_id: str, zone: TableZone, request: Request) -> TableZone:
    store = request.app.state.table_zone_store
    try:
        updated = store.update(zone_id, zone)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    _persist(request)
    return updated


@router.delete("/{zone_id}", status_code=204, response_class=Response)
def delete_table_zone(zone_id: str, request: Request) -> Response:
    store = request.app.state.table_zone_store
    try:
        store.delete(zone_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    _persist(request)
    return Response(status_code=204)
