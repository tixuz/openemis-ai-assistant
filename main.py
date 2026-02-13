from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleWARE
import uvicorn

app = FastAPI()

# Allow CORS for the Chrome Extension to communicate with the backend
origins = [
    "http://localhost:8000", # FastAPI's default host
    "chrome-extension://*", # Allow all Chrome Extensions, though you might want to restrict this in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, allow all origins. In production, restrict to your extension ID.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "No message provided")
    response_message = f"Echo from server: {user_message}"
    return JSONResponse(content={"response": response_message})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
