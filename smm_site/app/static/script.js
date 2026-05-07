const socialBtns = document.querySelectorAll(".social-btn");
const serviceCards = document.querySelectorAll(".service-card");
const searchInput = document.getElementById("searchInput");

socialBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        socialBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const social = btn.dataset.social;

        serviceCards.forEach(card => {
            if (social === "all" || card.dataset.social === social) {
                card.style.display = "block";
            } else {
                card.style.display = "none";
            }
        });
    });
});

searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    serviceCards.forEach(card => {
        const name = card.dataset.name.toLowerCase();
        if (name.includes(query)) {
            card.style.display = "block";
        } else {
            card.style.display = "none";
        }
    });
});
