import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "finance.main:APP",
        reload=True,
    )
