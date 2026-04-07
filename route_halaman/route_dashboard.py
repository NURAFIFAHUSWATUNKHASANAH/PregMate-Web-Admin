from flask import Blueprint, render_template, session, redirect, url_for

# Inisialisasi Blueprint untuk Dashboard
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def index():
    # 1. Proteksi Halaman (Opsional: Cek session login admin)
    # if 'admin_id' not in session:
    #     return redirect(url_for('admin_bp.login'))

    # 2. Mock Data (Nanti bisa diganti dengan query ke Database/MySQL)
    stats = {
        'total_keluhan': 1284,
        'terapi_selesai': 856,
        'user_aktif': 3412,
        'artikel_terbit': 42
    }

    recent_activities = [
        {
            'user': 'Rudi Tabuti', 
            'avatar': 'https://ui-avatars.com/api/?name=Rudi&background=random',
            'keluhan': 'Nyeri Punggung Bawah', 
            'status': 'Proses', 
            'tanggal': '20 Feb 2024'
        },
        {
            'user': 'Siti Aminah', 
            'avatar': 'https://ui-avatars.com/api/?name=Siti&background=random',
            'keluhan': 'Pemulihan Pasca Stroke', 
            'status': 'Selesai', 
            'tanggal': '19 Feb 2024'
        }
    ]

    # 3. Render Template dengan mengirimkan data
    return render_template(
        'dashboard.html', 
        stats=stats, 
        activities=recent_activities
    )