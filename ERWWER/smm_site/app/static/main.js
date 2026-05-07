// Boostix client - spring edition
// Theme, sakura petals, mobile menu, services pagination/filter,
// purchase modal calculator, real top-up modal, live balance refresh.

document.addEventListener('DOMContentLoaded', () => {

    /* -------------------- THEME -------------------- */
    const savedTheme = localStorage.getItem('theme') || 'dark-theme';
    document.body.classList.remove('light-theme', 'dark-theme', 'light-mode');
    document.body.classList.add(savedTheme);
    syncThemeIcon();

    function toggleTheme() {
        const isDark = document.body.classList.contains('dark-theme');
        document.body.classList.remove('dark-theme', 'light-theme', 'light-mode');
        document.body.classList.add(isDark ? 'light-theme' : 'dark-theme');
        localStorage.setItem('theme', isDark ? 'light-theme' : 'dark-theme');
        syncThemeIcon();
    }
    function syncThemeIcon() {
        const isDark = document.body.classList.contains('dark-theme');
        document.querySelectorAll('#toggleTheme, #toggleThemeMob').forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) icon.className = isDark ? 'fas fa-moon' : 'fas fa-sun';
        });
    }
    document.querySelectorAll('#toggleTheme, #toggleThemeMob').forEach(btn => {
        btn.addEventListener('click', () => {
            toggleTheme();
            closeDrawer(); // close drawer after theme toggle
        });
    });

    /* -------------------- MOBILE DRAWER (burger menu) -------------------- */
    const mobBurger   = document.getElementById('mobBurger');
    const mobDrawer   = document.getElementById('mobDrawer');
    const mobBackdrop = document.getElementById('mobBackdrop');
    const mobClose    = document.getElementById('mobDrawerClose');

    function openDrawer() {
        if (!mobDrawer) return;
        mobDrawer.classList.add('is-open');
        mobDrawer.setAttribute('aria-hidden', 'false');
        if (mobBackdrop) mobBackdrop.classList.add('is-open');
        if (mobBurger) mobBurger.classList.add('is-open');
        document.body.style.overflow = 'hidden';
    }
    function closeDrawer() {
        if (!mobDrawer) return;
        mobDrawer.classList.remove('is-open');
        mobDrawer.setAttribute('aria-hidden', 'true');
        if (mobBackdrop) mobBackdrop.classList.remove('is-open');
        if (mobBurger) mobBurger.classList.remove('is-open');
        document.body.style.overflow = '';
    }

    if (mobBurger) mobBurger.addEventListener('click', () => {
        mobDrawer && mobDrawer.classList.contains('is-open') ? closeDrawer() : openDrawer();
    });
    if (mobClose)    mobClose.addEventListener('click', closeDrawer);
    if (mobBackdrop) mobBackdrop.addEventListener('click', closeDrawer);

    /* -------------------- SAKURA PETALS -------------------- */
    const petalContainer = document.getElementById('petal-container');
    if (petalContainer) {
        function spawnPetal() {
            const p = document.createElement('div');
            p.className = 'petal';
            const size = 8 + Math.random() * 12;
            p.style.width = size + 'px';
            p.style.height = size + 'px';
            p.style.left = Math.random() * 100 + 'vw';
            p.style.opacity = (0.55 + Math.random() * 0.45).toFixed(2);
            p.style.setProperty('--duration', (8 + Math.random() * 8) + 's');
            p.style.setProperty('--drift', ((Math.random() * 50) - 25) + 'vw');
            petalContainer.appendChild(p);
            setTimeout(() => p.remove(), 17000);
        }
        for (let i = 0; i < 8; i++) setTimeout(spawnPetal, Math.random() * 4000);
        setInterval(spawnPetal, 600);
    }

    /* -------------------- FILTERS, SEARCH, PAGINATION -------------------- */
    const serviceCards = Array.from(document.querySelectorAll('.service-card'));
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    let selectedSocial = 'all';
    let selectedCategory = 'all';
    let visibleCount = 5;
    const PAGE_INCREMENT = 5;

    function applyFilters() {
        const q = (document.getElementById('serviceSearch')?.value || '').trim().toLowerCase();
        const matches = [];
        serviceCards.forEach(card => {
            const s = card.dataset.social || 'default';
            const c = card.dataset.category || 'other';
            const title = (card.querySelector('h3')?.innerText || '').toLowerCase();
            const matchesSearch = !q || title.includes(q) || (card.dataset.serviceId || '').includes(q);
            const isMatch = (selectedSocial === 'all' || s === selectedSocial)
                && (selectedCategory === 'all' || c === selectedCategory)
                && matchesSearch;
            if (isMatch) matches.push(card);
            card.style.display = 'none';
        });
        matches.slice(0, visibleCount).forEach(c => { c.style.display = 'flex'; });
        if (loadMoreBtn) loadMoreBtn.style.display = matches.length > visibleCount ? 'inline-flex' : 'none';
    }

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            visibleCount += PAGE_INCREMENT;
            applyFilters();
        });
    }

    document.querySelectorAll('.social-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.social-tab').forEach(x => x.classList.remove('active'));
            tab.classList.add('active');
            selectedSocial = tab.dataset.social;
            visibleCount = 5;
            applyFilters();
        });
    });
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.category-tab').forEach(x => x.classList.remove('active'));
            tab.classList.add('active');
            selectedCategory = tab.dataset.cat;
            visibleCount = 5;
            applyFilters();
        });
    });

    const searchEl = document.getElementById('serviceSearch');
    if (searchEl) {
        let t;
        searchEl.addEventListener('input', () => {
            visibleCount = 5;
            clearTimeout(t);
            t = setTimeout(applyFilters, 180);
        });
    }

    const defaultSocial = document.querySelector('.social-tab[data-social="all"]');
    if (defaultSocial) defaultSocial.classList.add('active');
    const defaultCat = document.querySelector('.category-tab[data-cat="all"]');
    if (defaultCat) defaultCat.classList.add('active');
    applyFilters();

    /* -------------------- ORDER MODAL (purchase) -------------------- */
    const orderModal = document.getElementById('orderModal');
    const inputQty = document.getElementById('inputQuantity');
    const displayQty = document.getElementById('displayQuantity');
    const totalPriceEl = document.getElementById('totalPrice');
    const modalRateEl = document.getElementById('modalRate');
    const minHint = document.getElementById('minHint');
    const maxHint = document.getElementById('maxHint');

    function updateCalculation() {
        if (!modalRateEl || !inputQty) return;
        const rate = parseFloat(modalRateEl.innerText) || 0;
        const qty = parseInt(inputQty.value) || 0;
        const total = (rate / 1000) * qty;
        if (displayQty) displayQty.innerText = qty.toLocaleString('ru-RU');
        if (totalPriceEl) totalPriceEl.innerText = total.toFixed(1);
    }
    if (inputQty) inputQty.addEventListener('input', updateCalculation);

    document.addEventListener('click', (e) => {
        const sel = e.target.closest('.select-btn');
        if (!sel) return;
        const card = sel.closest('.service-card');
        if (!card || !orderModal) return;
        document.getElementById('modalServiceName').innerText = card.dataset.serviceName || card.querySelector('h3')?.innerText || 'Услуга';
        modalRateEl.innerText = card.dataset.rate;
        document.getElementById('modalServiceId').value = card.dataset.serviceId;
        const minQty = card.dataset.min || 1;
        const maxQty = card.dataset.max || '—';
        if (minHint) minHint.innerText = minQty;
        if (maxHint) maxHint.innerText = maxQty;
        if (inputQty) {
            inputQty.value = minQty;
            inputQty.min = minQty;
        }
        updateCalculation();
        openModal(orderModal);
    });

    /* -------------------- TOPUP MODAL -------------------- */
    const topupModal = document.getElementById('topupModal');
    const topupAmount = document.getElementById('topupAmount');

    // Topup modal openers: mobile nav button + desktop sidebar button
    ['openTopupBtn', 'openTopupBtnSidebar'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn && topupModal) btn.addEventListener('click', () => openModal(topupModal));
    });

    document.querySelectorAll('.quick-amount').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.quick-amount').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (topupAmount) topupAmount.value = btn.dataset.amount;
        });
    });
    if (topupAmount) {
        topupAmount.addEventListener('input', () => {
            document.querySelectorAll('.quick-amount').forEach(b => b.classList.remove('active'));
        });
    }

    /* -------------------- MODAL HELPERS -------------------- */
    function openModal(m) {
        m.classList.add('is-open');
        document.body.style.overflow = 'hidden';
    }
    function closeModal(m) {
        m.classList.remove('is-open');
        document.body.style.overflow = '';
    }
    document.querySelectorAll('.modal .close').forEach(btn => {
        btn.addEventListener('click', () => {
            const m = btn.closest('.modal');
            if (m) closeModal(m);
        });
    });
    document.querySelectorAll('.modal').forEach(m => {
        m.addEventListener('click', (ev) => { if (ev.target === m) closeModal(m); });
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.is-open').forEach(closeModal);
        }
    });

    /* -------------------- LIVE BALANCE REFRESH -------------------- */
    function refreshBalance() {
        fetch('/api/balance', { cache: 'no-store' })
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (!data) return;
                document.querySelectorAll('[data-balance-value]').forEach(el => {
                    el.textContent = data.balance;
                });
            })
            .catch(() => {});
    }
    refreshBalance();
    setInterval(refreshBalance, 15000);

    // Refresh balance when window/tab regains focus (e.g. user returns from payment)
    window.addEventListener('focus', refreshBalance);
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') refreshBalance();
    });

    /* -------------------- AUTO-OPEN TOPUP IF NEEDED -------------------- */
    // If we redirected back with ?need_topup=XX, auto-open the topup modal.
    const params = new URLSearchParams(window.location.search);
    const needTopup = params.get('need_topup');
    if (needTopup && topupModal) {
        if (topupAmount) topupAmount.value = Math.ceil(parseFloat(needTopup));
        openModal(topupModal);
    }
});
