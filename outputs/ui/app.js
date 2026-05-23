// Application State
let currentFeed = 'traffic';
let cameras = [];
let filteredCameras = [];
let selectedCameraId = null;


// DOM Elements
const activeCountEl = document.getElementById('active-count');
const lastUpdatedEl = document.getElementById('last-updated-time');
const searchInput = document.getElementById('search-input');
const routeFilter = document.getElementById('route-filter');
const countyFilter = document.getElementById('county-filter');
const routeFilterLabel = document.getElementById('route-filter-label');
const countyFilterLabel = document.getElementById('county-filter-label');
const cameraList = document.getElementById('camera-list');
const cameraGallery = document.getElementById('camera-gallery');
const galleryHeaderTitle = document.getElementById('gallery-header-title');
const feedSelect = document.getElementById('feed-select');

// Modal Elements
const cameraModal = document.getElementById('camera-modal');
const modalImage = document.getElementById('modal-image');
const modalYoutubeFrame = document.getElementById('modal-youtube-frame');
const modalTitle = document.getElementById('modal-camera-title');
const modalRoute = document.getElementById('modal-route');
const modalDirection = document.getElementById('modal-direction');
const modalCounty = document.getElementById('modal-county');
const modalNearby = document.getElementById('modal-nearby');
const modalCloseBtn = document.getElementById('modal-close-btn');

// Modal Metadata Label Elements for Zoo Feed adjustments
const modalLblRoute = document.getElementById('modal-lbl-route');
const modalLblCounty = document.getElementById('modal-lbl-county');

// Intelligence Sandbox Elements
const promptSelect = document.getElementById('prompt-select');
const customPromptGroup = document.getElementById('custom-prompt-group');
const customPromptInput = document.getElementById('custom-prompt-input');
const runAnalysisBtn = document.getElementById('run-analysis-btn');
const resultPlaceholder = document.getElementById('result-placeholder');
const resultLoader = document.getElementById('result-loader');
const resultBody = document.getElementById('analysis-result-content');

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    fetchCameras();
    setupEventListeners();
});



// Fetch Camera/Node List from Server API
async function fetchCameras() {
    showLoadingState();
    try {
        const response = await fetch(`/api/cameras?feed=${currentFeed}`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        cameras = data.cameras || [];
        filteredCameras = [...cameras];
        
        updateStats(cameras.length, data.last_updated);
        populateFilters(cameras);
        renderApp();
    } catch (error) {
        console.error('Error fetching camera data:', error);
        showErrorState();
    }
}

// Update Stats in Header
function updateStats(count, timestamp) {
    activeCountEl.textContent = count;
    if (timestamp) {
        const date = new Date(timestamp * 1000);
        lastUpdatedEl.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } else {
        lastUpdatedEl.textContent = 'Never';
    }
}

// Show Loading Skeletons
function showLoadingState() {
    cameraList.innerHTML = `
        <div class="camera-list-item shimmer" style="height: 55px; margin-bottom: 0.5rem;"></div>
        <div class="camera-list-item shimmer" style="height: 55px; margin-bottom: 0.5rem;"></div>
        <div class="camera-list-item shimmer" style="height: 55px; margin-bottom: 0.5rem;"></div>
    `;
    cameraGallery.innerHTML = `
        <div class="camera-card shimmer" style="height: 250px;"></div>
        <div class="camera-card shimmer" style="height: 250px;"></div>
        <div class="camera-card shimmer" style="height: 250px;"></div>
    `;
}

// Show Error Message
function showErrorState() {
    const errorHTML = `<div class="empty-state">Failed to load feed nodes. Please check the backend server.</div>`;
    cameraList.innerHTML = errorHTML;
    cameraGallery.innerHTML = errorHTML;
}

// Populate Filter Options dynamically
function populateFilters(camList) {
    const routes = new Set();
    const counties = new Set();
    
    camList.forEach(cam => {
        if (cam.route) routes.add(cam.route);
        if (cam.county) counties.add(cam.county);
    });
    
    // Sort routes numerically/alphabetically
    const sortedRoutes = Array.from(routes).sort((a, b) => {
        const aNum = parseInt(a.replace(/\D/g, ''));
        const bNum = parseInt(b.replace(/\D/g, ''));
        if (isNaN(aNum) || isNaN(bNum)) return a.localeCompare(b);
        return aNum - bNum;
    });
    
    const sortedCounties = Array.from(counties).sort();
    
    // Update filter dropdowns
    const routePlaceholder = currentFeed === 'traffic' ? 'All Routes' : 'All Zones';
    const countyPlaceholder = currentFeed === 'traffic' ? 'All Counties' : 'All Sectors';
    
    routeFilter.innerHTML = `<option value="all">${routePlaceholder}</option>`;
    countyFilter.innerHTML = `<option value="all">${countyPlaceholder}</option>`;
    
    sortedRoutes.forEach(route => {
        routeFilter.innerHTML += `<option value="${route}">${route}</option>`;
    });
    
    sortedCounties.forEach(county => {
        countyFilter.innerHTML += `<option value="${county}">${county}</option>`;
    });
}

// Setup Event Listeners
function setupEventListeners() {
    // Search & Filters
    searchInput.addEventListener('input', filterCameras);
    routeFilter.addEventListener('change', filterCameras);
    countyFilter.addEventListener('change', filterCameras);
    
    // Feed Switcher
    feedSelect.addEventListener('change', handleFeedSwitch);
    
    // Modal
    modalCloseBtn.addEventListener('click', closeModal);
    cameraModal.addEventListener('click', (e) => {
        if (e.target === cameraModal) closeModal();
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    // Sandbox prompt selection trigger
    promptSelect.addEventListener('change', () => {
        if (promptSelect.value === 'custom') {
            customPromptGroup.style.display = 'flex';
        } else {
            customPromptGroup.style.display = 'none';
        }
    });

    // Run AI button handler
    runAnalysisBtn.addEventListener('click', runAIAnalysis);

    // Auto-refresh count data in background every 15 seconds without resetting the UI
    setInterval(() => {
        updateCountsOnly();
    }, 15000);
}

// Handle Feed Switching
function handleFeedSwitch() {
    currentFeed = feedSelect.value;
    
    // Update UI Labels depending on feed
    if (currentFeed === 'zoo') {
        routeFilterLabel.textContent = 'Filter by Zone';
        countyFilterLabel.textContent = 'Filter by Sector';
        modalLblRoute.textContent = 'Zone:';
        modalLblCounty.textContent = 'Sector:';
    } else {
        routeFilterLabel.textContent = 'Filter by Route';
        countyFilterLabel.textContent = 'Filter by County';
        modalLblRoute.textContent = 'Route:';
        modalLblCounty.textContent = 'County:';
    }
    
    // Clear search filter state
    searchInput.value = '';
    selectedCameraId = null;
    
    // Fetch new cameras list
    fetchCameras();
}

// Filter Nodes based on search & selector criteria
function filterCameras() {
    const searchQuery = searchInput.value.toLowerCase().trim();
    const selectedRoute = routeFilter.value;
    const selectedCounty = countyFilter.value;
    
    filteredCameras = cameras.filter(cam => {
        const matchesSearch = cam.name.toLowerCase().includes(searchQuery) || 
                              cam.nearby.toLowerCase().includes(searchQuery) ||
                              cam.county.toLowerCase().includes(searchQuery);
                              
        const matchesRoute = selectedRoute === 'all' || cam.route === selectedRoute;
        const matchesCounty = selectedCounty === 'all' || cam.county === selectedCounty;
        
        return matchesSearch && matchesRoute && matchesCounty;
    });
    
    const feedHeaderName = currentFeed === 'traffic' ? 'Live Nodes' : 'Enclosure Nodes';
    galleryHeaderTitle.textContent = searchQuery || selectedRoute !== 'all' || selectedCounty !== 'all' 
        ? `Filtered Nodes (${filteredCameras.length})` 
        : `${feedHeaderName} (${filteredCameras.length})`;
        
    renderApp();
}

// Render Entire UI State
function renderApp() {
    renderListView();
    renderGalleryView();
}



// Render Left Sidebar list
function renderListView() {
    if (filteredCameras.length === 0) {
        cameraList.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 0.75rem; padding: 1rem;">No nodes found.</div>`;
        return;
    }
    
    cameraList.innerHTML = '';
    filteredCameras.forEach((cam, idx) => {
        const item = document.createElement('div');
        item.className = `camera-list-item ${selectedCameraId === idx ? 'selected' : ''}`;
        item.id = `cam-list-item-${cam.id}`;
        
        const routeLabel = currentFeed === 'traffic' ? 'Route' : 'Zone';
        const countyLabel = currentFeed === 'traffic' ? cam.county : cam.county;
        
        const accentClass = currentFeed === 'zoo' ? 'zoo-accent' : 'traffic-accent';
        const countPill = cam.latest_count_summary 
            ? `<span class="list-count-badge ${accentClass}">${cam.latest_count_summary}</span>` 
            : '';
            
        item.innerHTML = `
            <div class="item-header" style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; width: 100%;">
                <div class="item-name">${cam.name}</div>
                ${countPill}
            </div>
            <div class="item-meta" style="margin-top: 4px;">
                <span>${routeLabel}: ${cam.route}</span>
                <span>${countyLabel}</span>
            </div>
        `;
        item.addEventListener('click', () => {
            selectCamera(idx, true);
        });
        cameraList.appendChild(item);
    });
}

// Render Card Gallery
function renderGalleryView() {
    if (filteredCameras.length === 0) {
        cameraGallery.innerHTML = `<div class="empty-state">No camera nodes match search parameters.</div>`;
        return;
    }
    
    cameraGallery.innerHTML = '';
    
    filteredCameras.forEach((cam, idx) => {
        const card = document.createElement('div');
        card.className = 'camera-card';
        card.id = `cam-card-${cam.id}`;
        if (selectedCameraId === idx) {
            card.style.borderColor = 'var(--accent-violet)';
            card.style.boxShadow = 'var(--shadow-glow)';
        }
        
        const cardImgUrl = cam.youtube_id ? `https://www.youtube.com/watch?v=${cam.youtube_id}` : cam.img_url;
        const proxiedImg = `/api/proxy?url=${encodeURIComponent(cardImgUrl)}`;
        const accentClass = currentFeed === 'zoo' ? 'zoo-accent' : 'traffic-accent';
        const countBadge = cam.latest_count_summary 
            ? `<div class="count-badge ${accentClass}">${cam.latest_count_summary}</div>` 
            : '';
        
        card.innerHTML = `
            <div class="card-img-wrapper" onclick="openModal(${idx})">
                <img src="${proxiedImg}" alt="Live feed for ${cam.name}" class="card-img" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22><rect width=%22100%22 height=%22100%22 fill=%22%230d0d15%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%2352525b%22>FEED OFFLINE</text></svg>';" />
                <div class="card-badges">
                    ${countBadge}
                    <div class="card-badge">Live</div>
                </div>
            </div>
            <div class="card-body">
                <div class="card-title">${cam.name}</div>
                <div class="card-meta">
                    <span>${cam.nearby}</span>
                    <span>${cam.route}</span>
                </div>
            </div>
        `;
        cameraGallery.appendChild(card);
    });
}

// Focus camera item on sidebar, map and scroll card
function selectCamera(idx, panToMarker = true) {
    selectedCameraId = idx;
    
    renderListView();
    renderGalleryView();
    
    const cam = filteredCameras[idx];
    if (cam) {
        const card = document.getElementById(`cam-card-${idx}`);
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

// Open Detail & Intelligence Sandbox Modal
function openModal(idx) {
    const cam = filteredCameras[idx];
    if (!cam) return;
    
    selectedCameraId = idx;
    
    // Reset Sandbox outputs
    resultPlaceholder.style.display = 'block';
    resultLoader.style.display = 'none';
    resultBody.style.display = 'none';
    resultBody.textContent = '';
    promptSelect.value = 'describe';
    customPromptGroup.style.display = 'none';
    customPromptInput.value = '';
    
    const timestamp = new Date().getTime();
    const proxiedImg = `/api/proxy?url=${encodeURIComponent(cam.img_url)}&t=${timestamp}`;

    // Show YouTube live iframe if available, otherwise show image
    if (cam.youtube_id) {
        modalImage.style.display = 'none';
        modalYoutubeFrame.style.display = 'block';
        modalYoutubeFrame.src = `https://www.youtube.com/embed/${cam.youtube_id}?autoplay=1&mute=1`;
    } else {
        modalYoutubeFrame.style.display = 'none';
        modalYoutubeFrame.src = '';
        modalImage.style.display = 'block';
        modalImage.src = proxiedImg;
        modalImage.alt = cam.name;
    }
    
    modalTitle.textContent = cam.name;
    modalRoute.textContent = cam.route || 'N/A';
    modalDirection.textContent = cam.direction || 'N/A';
    modalCounty.textContent = cam.county || 'N/A';
    modalNearby.textContent = cam.nearby || 'N/A';
    
    cameraModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// Close Detail Modal
function closeModal() {
    cameraModal.classList.remove('show');
    document.body.style.overflow = 'auto';
    
    // Remove YouTube iframe if exists
    const imgContainer = document.querySelector('.modal-img-container');
    const iframe = imgContainer.querySelector('iframe');
    if (iframe) iframe.remove();
    
    modalImage.style.display = 'block';
    modalImage.src = '';
    modalYoutubeFrame.src = '';
    modalYoutubeFrame.style.display = 'none';
    modalImage.style.display = 'block';
}

// Run AI analysis sandbox action
async function runAIAnalysis() {
    const cam = filteredCameras[selectedCameraId];
    if (!cam) return;

    const objective = promptSelect.value;
    const customPrompt = customPromptInput.value.trim();

    // Verification
    if (objective === 'custom' && !customPrompt) {
        alert('Please enter a custom query prompt.');
        return;
    }

    // Toggle UI States
    resultPlaceholder.style.display = 'none';
    resultLoader.style.display = 'flex';
    resultBody.style.display = 'none';
    runAnalysisBtn.disabled = true;
    runAnalysisBtn.style.opacity = '0.6';

    try {
        const analyzeUrl = cam.youtube_id ? `https://www.youtube.com/watch?v=${cam.youtube_id}` : cam.img_url;
        let url = `/api/analyze?feed=${currentFeed}&url=${encodeURIComponent(analyzeUrl)}&prompt=${objective}`;
        if (objective === 'custom') {
            url += `&custom_prompt=${encodeURIComponent(customPrompt)}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error('API Request Failed');
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Typing effect simulating stream output
            typeWriter(data.result);
        } else {
            showAIError(data.message || 'Analysis error');
        }
    } catch (err) {
        showAIError('Failed to communicate with AI analysis server. Check backend connections.');
    }
}

// Simulates typewriter stream response
function typeWriter(text) {
    resultLoader.style.display = 'none';
    resultBody.style.display = 'block';
    
    resultBody.textContent = '';
    
    let i = 0;
    const speed = 10; // Typing speed in ms
    
    function type() {
        if (i < text.length) {
            resultBody.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        } else {
            runAnalysisBtn.disabled = false;
            runAnalysisBtn.style.opacity = '1';
        }
    }
    
    type();
}

function showAIError(msg) {
    resultLoader.style.display = 'none';
    resultBody.style.display = 'block';
    resultBody.textContent = `Error: ${msg}`;
    runAnalysisBtn.disabled = false;
    runAnalysisBtn.style.opacity = '1';
}

// Background poller updating count values in-place without page/flicker resets
async function updateCountsOnly() {
    try {
        const response = await fetch(`/api/cameras?feed=${currentFeed}`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        const updatedCameras = data.cameras || [];
        
        // Sync local camera data cache
        updatedCameras.forEach(updatedCam => {
            const localCam = cameras.find(c => c.id === updatedCam.id);
            if (localCam) {
                localCam.latest_count_summary = updatedCam.latest_count_summary;
                localCam.latest_count_details = updatedCam.latest_count_details;
            }
            
            // Update card element count badge directly
            const card = document.getElementById(`cam-card-${updatedCam.id}`);
            if (card) {
                const badgeContainer = card.querySelector('.card-badges');
                if (badgeContainer) {
                    let countBadge = badgeContainer.querySelector('.count-badge');
                    if (updatedCam.latest_count_summary) {
                        if (!countBadge) {
                            countBadge = document.createElement('div');
                            countBadge.className = `count-badge ${currentFeed === 'zoo' ? 'zoo-accent' : 'traffic-accent'}`;
                            badgeContainer.insertBefore(countBadge, badgeContainer.firstChild);
                        }
                        countBadge.textContent = updatedCam.latest_count_summary;
                    } else if (countBadge) {
                        countBadge.remove();
                    }
                }
            }
            
            // Update sidebar item count badge directly
            const listItem = document.getElementById(`cam-list-item-${updatedCam.id}`);
            if (listItem) {
                let listBadge = listItem.querySelector('.list-count-badge');
                if (updatedCam.latest_count_summary) {
                    if (!listBadge) {
                        const header = listItem.querySelector('.item-header');
                        if (header) {
                            listBadge = document.createElement('span');
                            listBadge.className = `list-count-badge ${currentFeed === 'zoo' ? 'zoo-accent' : 'traffic-accent'}`;
                            header.appendChild(listBadge);
                        }
                    }
                    if (listBadge) {
                        listBadge.textContent = updatedCam.latest_count_summary;
                    }
                } else if (listBadge) {
                    listBadge.remove();
                }
            }
        });
        
        // Update Last Refresh timestamp in UI header
        if (data.last_updated && lastUpdatedEl) {
            const date = new Date(data.last_updated * 1000);
            lastUpdatedEl.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
    } catch (error) {
        console.error('Error in background count polling:', error);
    }
}
