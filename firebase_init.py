import firebase_admin
from firebase_admin import credentials

def init_firebase():
    # Cek apakah app sudah diinisialisasi sebelumnya untuk mencegah error
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("Firebase SDK Initialized")
    else:
        print("Firebase SDK already initialized")