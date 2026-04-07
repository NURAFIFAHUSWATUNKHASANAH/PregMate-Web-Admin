// SWEETALERT HAPUS

document.addEventListener("DOMContentLoaded", function () {

    const tombolHapus = document.querySelectorAll(".btn-hapus");

    tombolHapus.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.dataset.url;
            const nama = this.dataset.nama;

            Swal.fire({
                title: "Yakin ingin menghapus?",
                html: `Data <strong>${nama}</strong> akan dihapus permanen.`,
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#ef4444",
                cancelButtonColor: "#6b7280",
                confirmButtonText: "Ya, Hapus!",
                cancelButtonText: "Batal",
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });

});

// LOGOUT

// ===== LOGOUT ALERT =====
const tombolLogout = document.querySelectorAll(".btn-logout");

tombolLogout.forEach(button => {
    button.addEventListener("click", function (e) {
        e.preventDefault();

        const url = this.getAttribute("data-url");

        Swal.fire({
            title: "Yakin ingin logout?",
            text: "Sesi Anda akan berakhir.",
            icon: "question",
            showCancelButton: true,
            confirmButtonColor: "#ef4444",
            cancelButtonColor: "#6b7280",
            confirmButtonText: "Ya, Logout",
            cancelButtonText: "Batal"
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = url;
            }
        });
    });
});