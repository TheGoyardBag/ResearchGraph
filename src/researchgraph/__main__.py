"""Command-line interface. No cloud resources or paid APIs are enabled automatically."""
import argparse, json, os
from .common import Settings, ASSETS, load
def main():
    parser=argparse.ArgumentParser(prog="researchgraph")
    parser.add_argument("command",choices=["setup","train","serve","report","demo"])
    parser.add_argument("--port",type=int,default=8105)
    parser.add_argument("--host",default="127.0.0.1")
    args=parser.parse_args()
    if args.command=="setup":
        settings=Settings.environment()
        print("Local access token:",settings.initialize())
        print("Run: python -m researchgraph serve")
    elif args.command=="train":
        from .training import train
        print(json.dumps(train(),indent=2))
    elif args.command=="report": print(json.dumps(load(ASSETS/"artifacts"/"metrics.json"),indent=2))
    elif args.command=="demo":
        from .service import demo
        print(json.dumps(demo(),indent=2))
    else:
        import uvicorn
        from .api import create_app
        settings=Settings.environment()
        if not settings.token: parser.error("Run 'python -m researchgraph setup' first.")
        if args.host not in {"127.0.0.1","localhost","::1"}: print("WARNING: use a TLS reverse proxy and proper identity management before exposing this service.")
        uvicorn.run(create_app(settings),host=args.host,port=args.port)
if __name__=="__main__": main()
