// Apply saved theme on page load
document.addEventListener("DOMContentLoaded", function () {
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
    }
});


// Toggle dark mode
document.getElementById("darkModeToggle")?.addEventListener("click", function () {
    document.body.classList.toggle("dark-mode");

    if (document.body.classList.contains("dark-mode")) {
        localStorage.setItem("theme", "dark");
    } else {
        localStorage.setItem("theme", "light");
    }
});


function logoutAdmin() {
    window.location.href = "/";
}
document.addEventListener("DOMContentLoaded", function () {

    // ===== Status Chart =====
    const ctx1 = document.getElementById("statusChart");

    if (ctx1) {
        new Chart(ctx1, {
            type: "doughnut",
            data: {
                labels: ["Pending", "In Progress", "Resolved"],
                datasets: [{
                    data: [
                        statusData.pending,
                        statusData.progress,
                        statusData.resolved
                    ],
                    backgroundColor: [
                        "#f59e0b",
                        "#3b82f6",
                        "#10b981"
                    ]
                }]
            }
        });
    }

    // ===== Monthly Trends Chart =====
    const ctx2 = document.getElementById("trendsChart");

    if (ctx2) {
        new Chart(ctx2, {
            type: "line",
            data: {
                labels: months,
                datasets: [{
                    label: "Complaints",
                    data: monthlyCounts,
                    borderColor: "#0ea5e9",
                    fill: false,
                    tension: 0.3
                }]
            }
        });
    }

});
function openEditModal(id, title, category, description, image, status) {

    document.getElementById("modalComplaintId").value = id;
    document.getElementById("modalTitle").innerText = title;
    document.getElementById("modalCategory").innerText = category;
    document.getElementById("modalDescription").innerText = description;
    document.getElementById("modalStatus").value = status;

    if (image) {
        document.getElementById("modalImage").src = "/static/uploads/" + image;
    }

    document.getElementById("editModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("editModal").style.display = "none";
}

function updateStatus() {

    const id = document.getElementById("modalComplaintId").value;
    const status = document.getElementById("modalStatus").value;

    fetch(`/admin/update-status/${id}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ status: status })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    });
}

setTimeout(() => {
    document.querySelectorAll(".flash").forEach(flash => {
        flash.style.opacity = "0";
        setTimeout(() => flash.remove(), 500);
    });
}, 4000);

