import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

load_dotenv()

FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_JSON", "./cheesydelight-80a43-firebase-adminsdk-fbsvc-2e5458d166.json")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://cheesydelight-80a43-default-rtdb.firebaseio.com")

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })

db_ref = db.reference("/")

def verify_session(session_id):
    return db_ref.child("couponUsage").child(session_id).get()
