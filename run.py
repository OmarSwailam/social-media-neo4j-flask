from app.config import Config
from app import create_app
from app.seed import seed

app = create_app(Config)

if __name__ == '__main__':
    seed()
    app.run(host="0.0.0.0", port=5000)
