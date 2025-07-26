from fastapi import FastAPI, HTTPException
from auth.kite import get_access_token

app = FastAPI()


@app.get("/token")
def get_token():
    try:
        access_token = get_access_token()
        return {"access_token": access_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
