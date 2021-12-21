from fastapi import FastAPI, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.v2 import router as router_v2
from schema.root import Version, API
from reporter.version import version
import default

app = FastAPI(title="QuantumLeap",
              description=default.DESCRIPTION,
              version=default.VERSION,
              contact=default.CONTACT,
              license_info=default.LICENSE,
              openapi_tags=default.TAGS)

app.include_router(router_v2.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request,
                                       exc: RequestValidationError):

    errors: list = []
    for e in exc.errors():
        message = {"message": e['msg'], "type": e['type']}
        errors.append(message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"error": "Validation error", "description": errors}),
    )


@app.get("/", response_model=API, tags=['meta'])
async def root():
    return {
        "v2": "/v2"
    }


@app.get("/version", response_model=Version, tags=['meta'])
async def api_version():
    return version()
