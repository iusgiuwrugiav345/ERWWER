// Shared client script: theme, snow (with wind), filtering, search, modal
document.addEventListener('DOMContentLoaded', () => {
    // THEME: apply saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark-theme';
    document.body.classList.remove('light-theme','dark-theme');
    document.body.classList.add(savedTheme);

    const toggleBtn = document.getElementById('toggleTheme');
    if(toggleBtn){
        toggleBtn.addEventListener('click', () => {
            const isDark = document.body.classList.toggle('dark-theme');
            document.body.classList.toggle('light-mode', !isDark);
            localStorage.setItem('theme', isDark ? 'dark-theme' : 'light-mode');
            const modalContent = document.querySelector('#orderModal .modal-content');
            if(modalContent) modalContent.classList.toggle('dark-theme', isDark);
            
            // Sync toggle button icon
            const icon = toggleBtn.querySelector('i');
            if(icon) {
                icon.className = isDark ? 'fas fa-moon' : 'fas fa-sun';
            }
        });
    }

    // MOBILE MENU
    const sidebar = document.querySelector('.sidebar');
    const openMenu = document.getElementById('openMenu');
    if(openMenu && sidebar) {
        openMenu.addEventListener('click', () => {
            sidebar.classList.add('active');
            const backdrop = document.createElement('div');
            backdrop.className = 'menu-backdrop';
            backdrop.style = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:900;';
            document.body.appendChild(backdrop);
            backdrop.addEventListener('click', () => {
                sidebar.classList.remove('active');
                backdrop.remove();
            });
        });
    }

    // SNOW - Simplified & Reliable
    const snowContainer = document.getElementById('snow-container');
    if(snowContainer){
        function createFlake() {
            const flake = document.createElement('div');
            flake.className = 'snowflake';
            flake.innerHTML = '❄';
            flake.style.left = Math.random() * 100 + 'vw';
            flake.style.opacity = Math.random();
            flake.style.fontSize = (Math.random() * 10 + 10) + 'px';
            flake.style.setProperty('--duration', (Math.random() * 5 + 5) + 's');
            flake.style.setProperty('--drift', (Math.random() * 20 - 10) + 'vw');
            snowContainer.appendChild(flake);
            setTimeout(() => flake.remove(), 10000);
        }
        setInterval(createFlake, 300);
    }

    // FILTERS and SEARCH
    const serviceCards = Array.from(document.querySelectorAll('.service-card'));
    let selectedSocial = 'all';
    let selectedCategory = 'all';

    function applyFilters(){
        const q = (document.getElementById('serviceSearch')?.value || '').trim().toLowerCase();
        serviceCards.forEach(card => {
            const s = card.dataset.social || 'default';
            const c = card.dataset.category || 'other';
            const title = (card.querySelector('h3')?.innerText || '').toLowerCase();
            const matchesSearch = !q || title.includes(q) || (card.dataset.serviceId||'').includes(q);
            const show = (selectedSocial === 'all' || s === selectedSocial) && (selectedCategory === 'all' || c === selectedCategory) && matchesSearch;
            card.style.display = show ? 'flex' : 'none';
        });
    }

    document.querySelectorAll('.social-tab').forEach(tab => {
        tab.addEventListener('click', ()=>{
            document.querySelectorAll('.social-tab').forEach(x=>x.classList.remove('active'));
            tab.classList.add('active');
            selectedSocial = tab.dataset.social;
            applyFilters();
        });
    });
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.addEventListener('click', ()=>{
            document.querySelectorAll('.category-tab').forEach(x=>x.classList.remove('active'));
            tab.classList.add('active');
            selectedCategory = tab.dataset.cat;
            applyFilters();
        });
    });

    const searchEl = document.getElementById('serviceSearch');
    if(searchEl){
        let t;
        searchEl.addEventListener('input', ()=>{
            clearTimeout(t); t = setTimeout(applyFilters, 180);
        });
    }

    // MODAL and CALCULATOR
    const modal = document.getElementById('orderModal');
    const modalContent = modal?.querySelector('.modal-content');
    const inputQty = document.getElementById('inputQuantity');
    const displayQty = document.getElementById('displayQuantity');
    const totalPriceEl = document.getElementById('totalPrice');
    const modalRateEl = document.getElementById('modalRate');

    function updateCalculation() {
        const rate = parseFloat(modalRateEl.innerText) || 0;
        const qty = parseInt(inputQty.value) || 0;
        const total = (rate / 1000) * qty;
        displayQty.innerText = qty.toLocaleString();
        totalPriceEl.innerText = total.toFixed(1);
    }

    if(inputQty) {
        inputQty.addEventListener('input', updateCalculation);
    }

    document.addEventListener('click', (e)=>{
        const sel = e.target.closest('.select-btn');
        if(sel){
            const card = sel.closest('.service-card');
            if(!card) return;
            document.getElementById('modalServiceName').innerText = card.querySelector('h3').innerText;
            modalRateEl.innerText = card.dataset.rate;
            document.getElementById('modalServiceId').value = card.dataset.serviceId;
            
            // Set min quantity as default
            const minQty = card.dataset.min || 1;
            inputQty.value = minQty;
            inputQty.min = minQty;
            
            updateCalculation();
            
            if(modal) modal.style.display = 'block';
            if(modalContent) modalContent.classList.toggle('dark-theme', document.body.classList.contains('dark-theme'));
        }
    });

    document.querySelectorAll('.modal .close').forEach(x=>x.addEventListener('click', ()=>{ if(modal) modal.style.display='none' }));
    window.addEventListener('click', (ev)=>{ if(ev.target === modal) modal.style.display='none' });

    // QUICK TOP-UP
    const topupForm = document.getElementById('quickTopupForm');
    if(topupForm){
        topupForm.addEventListener('submit', (e)=>{
            e.preventDefault();
            const amount = topupForm.querySelector('input[name="amount"]').value;
            alert('Simulated top-up: ' + amount);
        });
    }

    // init defaults
    const defaultSocial = document.querySelector('.social-tab[data-social="all"]'); if(defaultSocial) defaultSocial.classList.add('active');
    const defaultCat = document.querySelector('.category-tab[data-cat="all"]'); if(defaultCat) defaultCat.classList.add('active');
    applyFilters();
});

