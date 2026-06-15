/**
 * CivitAI Uploader Neo — frontend logic for selection, preview, favorites and reordering.
 */

(function () {
    const SELECTED_KEY = 'civitai-gallery-selected';
    const LAST_CLICKED_KEY = 'civitai-gallery-last-clicked';

    function getInput(selector) {
        const el = gradioApp().querySelector(selector);
        if (!el) return null;
        return el.querySelector('textarea, input');
    }

    function syncState(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    }

    function readSelected() {
        try {
            const raw = localStorage.getItem(SELECTED_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }

    function writeSelected(selected) {
        syncState(SELECTED_KEY, selected);
        const input = getInput('#civitai_gallery_selected_sync');
        if (input) {
            input.value = JSON.stringify(selected);
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    function readLastClicked() {
        try {
            const raw = localStorage.getItem(LAST_CLICKED_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    }

    function writeLastClicked(path) {
        syncState(LAST_CLICKED_KEY, path);
    }

    function getAllCardPaths() {
        const cards = gradioApp().querySelectorAll('.gallery-card');
        return Array.from(cards).map(c => c.dataset.path).filter(Boolean);
    }

    function updateCardVisuals(selected) {
        const selectedSet = new Set(selected);
        const cards = gradioApp().querySelectorAll('.gallery-card');
        cards.forEach(card => {
            const path = card.dataset.path;
            card.classList.toggle('selected', selectedSet.has(path));
        });
    }

    function updateSelectedListVisuals(selected) {
        const items = gradioApp().querySelectorAll('.gallery-selected-item');
        items.forEach((item, idx) => {
            const indexEl = item.querySelector('.gallery-selected-index');
            if (indexEl) indexEl.textContent = idx + 1;
        });
    }

    // ── Card click with Ctrl/Shift multi-select ──
    window.handleGalleryCardClick = function (event, card) {
        event.stopPropagation();
        const path = card.dataset.path;
        if (!path) return;

        const selected = readSelected();
        const allPaths = getAllCardPaths();
        const index = allPaths.indexOf(path);

        if (event.shiftKey && readLastClicked()) {
            // Range selection
            const lastIndex = allPaths.indexOf(readLastClicked());
            if (lastIndex !== -1) {
                const start = Math.min(lastIndex, index);
                const end = Math.max(lastIndex, index);
                const range = allPaths.slice(start, end + 1);
                const newSelected = Array.from(new Set([...selected, ...range]));
                writeSelected(newSelected);
            }
        } else if (event.ctrlKey || event.metaKey) {
            // Toggle individual
            const idx = selected.indexOf(path);
            if (idx >= 0) selected.splice(idx, 1);
            else selected.push(path);
            writeSelected(selected);
            writeLastClicked(path);
        } else {
            // Simple toggle
            const idx = selected.indexOf(path);
            if (idx >= 0) selected.splice(idx, 1);
            else selected.push(path);
            writeSelected(selected);
            writeLastClicked(path);
        }
        updateCardVisuals(readSelected());
    };

    // ── Hover preview ──
    window.previewGalleryImage = function (img) {
        const card = img.closest('.gallery-card');
        if (!card) return;
        const path = card.dataset.path;
        if (!path) return;

        const input = getInput('#civitai_gallery_preview_sync');
        if (input) {
            input.value = path;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    };

    // ── Favorite toggle ──
    window.toggleGalleryFav = function (event, star) {
        event.stopPropagation();
        const card = star.closest('.gallery-card');
        if (!card) return;
        const path = card.dataset.path;
        if (!path) return;

        // Call Python endpoint via a hidden sync if needed; for now optimistic toggle
        star.classList.toggle('active');
        // Notify Python to persist favorite status
        const input = getInput('#civitai_gallery_fav_sync');
        if (input) {
            input.value = JSON.stringify({ action: 'toggle', path: path });
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    };

    // ── Source folder selection ──
    window.selectGallerySource = function (item) {
        const path = item.dataset.path;
        if (!path) return;
        const input = getInput('#civitai_gallery_folder');
        if (input) {
            input.value = path;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
        // Trigger scan button click
        const scanBtn = gradioApp().querySelector('#civitai_gallery_scan_btn');
        if (scanBtn) scanBtn.click();
    };

    // ── Tag filter click ──
    window.filterGalleryByTag = function (chip) {
        const tag = chip.dataset.tag;
        if (!tag) return;
        const input = gradioApp().querySelector('#civitai_gallery_tag_filter input, #civitai_gallery_tag_filter textarea');
        if (input) {
            const current = input.value.trim();
            input.value = current ? `${current}, #${tag}` : `#${tag}`;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    };

    // ── Remove from selected list ──
    window.removeGallerySelection = function (button) {
        const item = button.closest('.gallery-selected-item');
        if (!item) return;
        const path = item.dataset.path;
        if (!path) return;

        const selected = readSelected();
        const idx = selected.indexOf(path);
        if (idx >= 0) selected.splice(idx, 1);
        writeSelected(selected);
        updateCardVisuals(selected);
    };

    // ── Drag-and-drop reordering ──
    function initSortable() {
        const list = gradioApp().querySelector('#gallery-selected-list');
        if (!list || list._sortable) return;

        if (typeof Sortable === 'undefined') {
            setTimeout(initSortable, 500);
            return;
        }

        list._sortable = new Sortable(list, {
            animation: 150,
            onEnd: function () {
                const items = list.querySelectorAll('.gallery-selected-item');
                const newOrder = Array.from(items).map(item => item.dataset.path).filter(Boolean);
                writeSelected(newOrder);
                updateSelectedListVisuals(newOrder);
            }
        });
    }

    // ── Compare tab: post one side ──
    window.postCompareSide = function (side) {
        const selected = readSelected();
        if (selected.length !== 2) return;
        const path = side === 'left' ? selected[0] : selected[1];

        // Replace selection with just this image and notify Python
        writeSelected([path]);
        updateCardVisuals([path]);

        // Switch to Gallery tab
        const galleryTab = gradioApp().querySelector('#civitai_gallery_tab_gallery');
        if (galleryTab) galleryTab.click();
    };

    // ── Restore visuals after Gradio re-renders ──
    const observer = new MutationObserver(() => {
        const selected = readSelected();
        updateCardVisuals(selected);
        initSortable();
    });

    function startObserver() {
        const browser = gradioApp().querySelector('#civitai_gallery_browser');
        const selected = gradioApp().querySelector('#civitai_gallery_selected');
        if (browser) observer.observe(browser, { childList: true, subtree: true });
        if (selected) observer.observe(selected, { childList: true, subtree: true });
        initSortable();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startObserver);
    } else {
        startObserver();
    }
})();
