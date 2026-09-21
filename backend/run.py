from app import create_app

app = create_app()

if __name__ == "__main__":
    # macOS 上 5000 端口常被 AirPlay 占用，默认使用 5001
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=app.config["DEBUG"], threaded=True)
