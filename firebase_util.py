import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Path to Firebase service account JSON
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_JSON", "./cheesydelight-80a43-firebase-adminsdk-fbsvc-2e5458d166.json")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://cheesydelight-80a43-default-rtdb.firebaseio.com")

# Initialize Firebase app if not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })
    except Exception as e:
        raise RuntimeError(f"🔥 Firebase initialization failed: {e}")

# Firebase root DB reference
db_ref = db.reference("/")

# ✅ Utility to fetch coupon usage by session ID
def verify_session(session_id):
    try:
        return db_ref.child("couponUsage").child(session_id).get()
    except Exception as e:
        print(f"⚠️ Error verifying session '{session_id}': {e}")
        return None
