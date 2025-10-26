import time
from app.core.database import SessionLocal
from app.models.clip import Clip

db = SessionLocal()

start = time.time()
clips = db.query(Clip).filter(Clip.is_deleted == False).limit(50).all()
end = time.time()

print(f"Query time: {(end - start) * 1000:.2f}ms")
db.close()
