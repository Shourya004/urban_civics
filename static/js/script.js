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

// Sidebar toggle
document.getElementById("hamburgerBtn")?.addEventListener("click", function () {
    document.getElementById("sidebar").classList.toggle("active");
    document.getElementById("overlay").classList.toggle("active");
});

// Category selection
function selectCategory(element, category) {
    document.querySelectorAll(".category-option").forEach(el => {
        el.classList.remove("selected");
    });

    element.classList.add("selected");
    document.getElementById("selectedCategory").value = category;
}

// Page navigation
function showPage(pageId) {
    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    document.getElementById(pageId).classList.add("active");
}

// Logout
function logout() {
    window.location.href = "/logout";
}

function openComplaintModal(title, description, status, date, address) {

    const modal = document.getElementById("complaintModal");
    const header = document.getElementById("modalHeader");
    const body = document.getElementById("modalBody");

    header.innerHTML = `
        <h3>${title}</h3>
        <p>Status: <strong>${status}</strong></p>
    `;

    body.innerHTML = `
        <p><strong>Location:</strong> ${address}</p>
        <p><strong>Date:</strong> ${date}</p>
        <hr>
        <p>${description}</p>
    `;

    modal.style.display = "flex";
}


function closeModal() {
    document.getElementById("complaintModal").style.display = "none";
}

let map;
let marker;

function openMap() {
    document.getElementById("mapModal").style.display = "block";

    setTimeout(() => {
        if (!map) {
            map = L.map('map').setView([28.6139, 77.2090], 13); // fallback Delhi

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(map);

            // ✅ AUTO GET CURRENT LOCATION
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function (position) {

                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;

                    map.setView([lat, lng], 15);

                    if (marker) {
                        map.removeLayer(marker);
                    }

                    marker = L.marker([lat, lng]).addTo(map);

                    document.getElementById("latitude").value = lat;
                    document.getElementById("longitude").value = lng;

                    // Reverse Geocoding
                    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.display_name) {
                                document.getElementById("address").value = data.display_name;
                            }
                        });

                }, function () {
                    alert("Location access denied. Please allow location permission.");
                });
            }

            // Manual click selection still works
            map.on('click', function (e) {

                const lat = e.latlng.lat;
                const lng = e.latlng.lng;

                if (marker) {
                    map.removeLayer(marker);
                }

                marker = L.marker([lat, lng]).addTo(map);

                document.getElementById("latitude").value = lat;
                document.getElementById("longitude").value = lng;

                fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.display_name) {
                            document.getElementById("address").value = data.display_name;
                        }
                    });
            });
        }
    }, 200);
}

function closeMap() {
    document.getElementById("mapModal").style.display = "none";
}

function openEditProfile() {
    document.getElementById("editProfileModal").style.display = "block";
}

function closeEditProfile() {
    document.getElementById("editProfileModal").style.display = "none";
}

function openChangePassword() {
    document.getElementById("changePasswordModal").style.display = "block";
}

function closeChangePassword() {
    document.getElementById("changePasswordModal").style.display = "none";
}

function openDeleteModal() {
    document.getElementById("deleteModal").style.display = "flex";
}

function closeDeleteModal() {
    document.getElementById("deleteModal").style.display = "none";
}

function openEmailUpdate() {
    document.getElementById("updateEmailModal").style.display = "block";
}

function closeEmailUpdate() {
    document.getElementById("updateEmailModal").style.display = "none";
}

function markSatisfied(id, imageName) {

    fetch(`/complaint/feedback/${id}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ feedback: "satisfied" })
    })
    .then(res => res.json())
    .then(data => {

        if (data.success) {

            alert("Thank you for confirming resolution ❤️");

            // Auto download image
            if (imageName) {
                const link = document.createElement("a");
                link.href = "/static/uploads/" + imageName;
                link.download = imageName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }

            location.reload();
        }
    });
}

function markNotSolved(id, imageName) {

    fetch(`/complaint/feedback/${id}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ feedback: "not_solved" })
    })
    .then(res => res.json())
    .then(data => {

        const caption = `
My complaint (ID: ${id}) is still not resolved by authorities.
Raising my voice for better civic response.
#CivicIssues #Accountability #PublicVoice
        `;

        alert("You can now post this on Instagram.");

        // Download caption file automatically
        const blob = new Blob([caption], { type: "text/plain" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "instagram_caption.txt";
        link.click();

        // Open image in new tab
        if (imageName) {
            window.open("/static/uploads/" + imageName, "_blank");
        }
    });
}

setTimeout(() => {
    document.querySelectorAll(".flash").forEach(flash => {
        flash.style.opacity = "0";
        setTimeout(() => flash.remove(), 500);
    });
}, 4000);