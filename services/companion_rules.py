from typing import Dict

RULES = {

    "trimester_1": {

        "ibu": [
            "Minum vitamin asam folat",
            "Minum air putih minimal 8 gelas",
            "Istirahat yang cukup",
            "Catat keluhan harian",
            "Hindari aktivitas berat"
        ],

        "pendamping": [
            "Mengingatkan ibu minum vitamin",
            "Membantu pekerjaan rumah",
            "Mengingatkan jadwal ANC",
            "Memberikan dukungan emosional"
        ],

        "education": [
            "Perkembangan janin trimester 1",
            "Cara mengatasi morning sickness",
            "Nutrisi trimester 1"
        ]
    },

    "trimester_2": {

        "ibu": [
            "Minum vitamin",
            "Minum air putih",
            "Jalan kaki 20 menit",
            "Catat gerakan janin",
            "Catat berat badan"
        ],

        "pendamping": [
            "Menemani olahraga ringan",
            "Mengingatkan vitamin",
            "Mengingatkan minum air",
            "Menemani kontrol ANC"
        ],

        "education": [
            "Gerakan janin",
            "Nutrisi trimester 2",
            "Olahraga ibu hamil"
        ]
    },

    "trimester_3": {

        "ibu": [
            "Hitung gerakan janin",
            "Catat kontraksi",
            "Istirahat cukup",
            "Siapkan tas bersalin",
            "Tetap minum vitamin"
        ],

        "pendamping": [
            "Pastikan tas bersalin siap",
            "Pastikan kendaraan siap",
            "Dampingi kontrol ANC",
            "Pelajari tanda persalinan"
        ],

        "education": [
            "Tanda persalinan",
            "ASI Eksklusif",
            "Perawatan bayi baru lahir"
        ]
    }

}


def get_rule(trimester: int) -> Dict:

    if trimester == 1:
        return RULES["trimester_1"]

    elif trimester == 2:
        return RULES["trimester_2"]

    return RULES["trimester_3"]