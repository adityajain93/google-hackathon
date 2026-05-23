// Application State
let currentFeed = 'traffic';
let cameras = [];
let filteredCameras = [];
let selectedCameraId = null;
let isLoadingStateActive = false;


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
    if (!isLoadingStateActive) {
        showLoadingState();
        isLoadingStateActive = true;
    }
    try {
        const response = await fetch(`/api/cameras?feed=${currentFeed}`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        
        if (data.is_loading) {
            setTimeout(fetchCameras, 1500);
            return;
        }
        
        isLoadingStateActive = false;
        cameras = data.cameras || [];
        filteredCameras = [...cameras];
        
        updateStats(cameras.length, data.last_updated);
        populateFilters(cameras);
        renderApp();
    } catch (error) {
        console.error('Error fetching camera data:', error);
        isLoadingStateActive = false;
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
        <div class="empty-state" style="padding: 5rem 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1rem; width: 100%; grid-column: 1 / -1;">
            <div class="labs-spinner" style="width: 40px; height: 40px; border-width: 3px;"></div>
            <span style="color: var(--text-secondary); font-size: 0.95rem; font-weight: 500; letter-spacing: 0.05em;">FETCHING LIVE CCTV FEEDS...</span>
        </div>
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

    // Auto-refresh card images + re-analyze car counts every 30 seconds
    setInterval(() => {
        startLiveImageSync();
    }, 30000);
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
    isLoadingStateActive = false;
    
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
        let safetyPill = '';
        if (cam.safety_summary) {
            let safetyClass = 'safety-safe';
            if (cam.safety_summary === 'Accident' || cam.safety_summary === 'Collision') {
                safetyClass = 'safety-danger';
            } else if (cam.safety_summary === 'Hazard') {
                safetyClass = 'safety-warning';
            }
            safetyPill = `<span class="list-safety-badge ${safetyClass}">${cam.safety_summary}</span>`;
        }

        const countPill = cam.latest_count_summary 
            ? `<span class="list-count-badge ${accentClass}">${cam.latest_count_summary}</span>` 
            : '';

        const aqiPill = cam.air_quality_summary
            ? `<span class="list-aqi-badge ${cam.air_quality_css_class || ''}" title="AQI: ${cam.air_quality_aqi}">AQI ${cam.air_quality_aqi}</span>`
            : '';
            
        item.innerHTML = `
            <div class="item-header" style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; width: 100%;">
                <div class="item-name">${cam.name}</div>
                <div class="item-badges" style="display: flex; gap: 4px; align-items: center; flex-shrink: 0;">
                    ${safetyPill}
                    ${countPill}
                    ${aqiPill}
                </div>
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
        let safetyBadge = '';
        if (cam.safety_summary) {
            let safetyClass = 'safety-safe';
            if (cam.safety_summary === 'Accident' || cam.safety_summary === 'Collision') {
                safetyClass = 'safety-danger';
            } else if (cam.safety_summary === 'Hazard') {
                safetyClass = 'safety-warning';
            }
            safetyBadge = `<div class="safety-badge ${safetyClass}">${cam.safety_summary}</div>`;
        }

        const countBadge = cam.latest_count_summary 
            ? `<div class="count-badge ${accentClass}">${cam.latest_count_summary}</div>` 
            : '';

        const aqiBadge = cam.air_quality_summary
            ? `<div class="aqi-badge ${cam.air_quality_css_class || ''}" title="AQI: ${cam.air_quality_aqi}">AQI ${cam.air_quality_aqi}</div>`
            : '';
        
        card.innerHTML = `
            <div class="card-img-wrapper" onclick="openModal(${idx})">
                <img src="${proxiedImg}" alt="Live feed for ${cam.name}" class="card-img" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22><rect width=%22100%22 height=%22100%22 fill=%22%230d0d15%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%2352525b%22>FEED OFFLINE</text></svg>';" />
                <div class="card-badges">
                    ${safetyBadge}
                    ${countBadge}
                    ${aqiBadge}
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

    // Kick off live image+count sync immediately after render
    startLiveImageSync();
}

// Live Image + Count Sync: refreshes each visible card's image and re-analyzes vehicle count.
// Cameras are staggered (1 per second) to avoid simultaneous API calls.
function startLiveImageSync() {
    if (currentFeed !== 'traffic') return; // Only for traffic cameras

    filteredCameras.forEach((cam, idx) => {
        if (cam.youtube_id) return; // Skip YouTube streams — they're live embeds

        setTimeout(async () => {
            // 1. Refresh the card image with a new timestamp (gets a fresh CCTV frame)
            const card = document.getElementById(`cam-card-${cam.id}`);
            if (!card) return;
            const img = card.querySelector('.card-img');
            if (img) {
                img.src = `/api/proxy?url=${encodeURIComponent(cam.img_url)}&t=${Date.now()}`;
            }

            // 2. Trigger a fresh count analysis for this camera
            try {
                const resp = await fetch(`/api/analyze?feed=traffic&url=${encodeURIComponent(cam.img_url)}&prompt=count`);
                if (!resp.ok) return;
                const data = await resp.json();
                if (data.status !== 'success') return;

                const summary = extractCountSummary(data.result);
                if (!summary) return;

                // Update local camera cache
                cam.latest_count_summary = summary;
                cam.latest_count_details = data.result;

                // Update the count badge on the card directly
                const badgeContainer = card.querySelector('.card-badges');
                if (badgeContainer) {
                    let countBadge = badgeContainer.querySelector('.count-badge');
                    if (!countBadge) {
                        countBadge = document.createElement('div');
                        countBadge.className = 'count-badge traffic-accent';
                        const liveBadge = badgeContainer.querySelector('.card-badge');
                        if (liveBadge) badgeContainer.insertBefore(countBadge, liveBadge);
                        else badgeContainer.appendChild(countBadge);
                    }
                    countBadge.textContent = summary;
                }

                // Update the sidebar list badge too
                const listItem = document.getElementById(`cam-list-item-${cam.id}`);
                if (listItem) {
                    const badgesWrapper = listItem.querySelector('.item-badges');
                    if (badgesWrapper) {
                        let countPill = badgesWrapper.querySelector('.list-count-badge');
                        if (!countPill) {
                            countPill = document.createElement('span');
                            countPill.className = 'list-count-badge traffic-accent';
                            badgesWrapper.appendChild(countPill);
                        }
                        countPill.textContent = summary;
                    }
                }
            } catch (e) {
                // Silently fail — count badge stays as-is
            }
        }, idx * 1000); // Stagger: 1 second apart per camera
    });
}

// Client-side count parser — mirrors the backend extract_count_summary logic
function extractCountSummary(text) {
    if (!text) return null;
    const clean = text.replace('[SIMULATION]', '').trim();
    // Primary: structured output "Total: N vehicles"
    const totalMatch = clean.match(/Total:\s*(\d+)\s*vehicles?/i);
    if (totalMatch) return `${totalMatch[1]} Vehicles`;
    // Fallback: sum individual vehicle category counts
    const vehicleMatches = clean.match(/(\d+)\s*(?:car|truck|motorcycle|vehicle)s?/gi);
    if (vehicleMatches) {
        const total = vehicleMatches.reduce((sum, m) => sum + parseInt(m.match(/\d+/)[0]), 0);
        return `${total} Vehicles`;
    }
    const approxMatch = clean.match(/(?:approximately|count:?)\s*(\d+)/i);
    if (approxMatch) return `${approxMatch[1]} Vehicles`;
    const numMatch = clean.match(/(\d+)/);
    if (numMatch) return `${numMatch[1]} Vehicles`;
    return null;
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
                localCam.safety_summary = updatedCam.safety_summary;
                localCam.safety_details = updatedCam.safety_details;
                localCam.air_quality_aqi = updatedCam.air_quality_aqi;
                localCam.air_quality_summary = updatedCam.air_quality_summary;
                localCam.air_quality_css_class = updatedCam.air_quality_css_class;
            }
            
            // Update card element badges directly
            const card = document.getElementById(`cam-card-${updatedCam.id}`);
            if (card) {
                const badgeContainer = card.querySelector('.card-badges');
                if (badgeContainer) {
                    // Update/insert safety badge
                    let safetyBadge = badgeContainer.querySelector('.safety-badge');
                    if (updatedCam.safety_summary) {
                        if (!safetyBadge) {
                            safetyBadge = document.createElement('div');
                            badgeContainer.insertBefore(safetyBadge, badgeContainer.firstChild);
                        }
                        let safetyClass = 'safety-safe';
                        if (updatedCam.safety_summary === 'Accident' || updatedCam.safety_summary === 'Collision') {
                            safetyClass = 'safety-danger';
                        } else if (updatedCam.safety_summary === 'Hazard') {
                            safetyClass = 'safety-warning';
                        }
                        safetyBadge.className = `safety-badge ${safetyClass}`;
                        safetyBadge.textContent = updatedCam.safety_summary;
                    } else if (safetyBadge) {
                        safetyBadge.remove();
                    }

                    // Update/insert count badge
                    let countBadge = badgeContainer.querySelector('.count-badge');
                    if (updatedCam.latest_count_summary) {
                        if (!countBadge) {
                            countBadge = document.createElement('div');
                            countBadge.className = `count-badge ${currentFeed === 'zoo' ? 'zoo-accent' : 'traffic-accent'}`;
                            const liveBadge = badgeContainer.querySelector('.card-badge');
                            if (liveBadge) {
                                badgeContainer.insertBefore(countBadge, liveBadge);
                            } else {
                                badgeContainer.appendChild(countBadge);
                            }
                        }
                        countBadge.textContent = updatedCam.latest_count_summary;
                    } else if (countBadge) {
                        countBadge.remove();
                    }

                    // Update/insert AQI badge
                    let aqiBadge = badgeContainer.querySelector('.aqi-badge');
                    if (updatedCam.air_quality_summary) {
                        if (!aqiBadge) {
                            aqiBadge = document.createElement('div');
                            const liveBadge = badgeContainer.querySelector('.card-badge');
                            if (liveBadge) {
                                badgeContainer.insertBefore(aqiBadge, liveBadge);
                            } else {
                                badgeContainer.appendChild(aqiBadge);
                            }
                        }
                        aqiBadge.className = `aqi-badge ${updatedCam.air_quality_css_class || ''}`;
                        aqiBadge.textContent = `AQI ${updatedCam.air_quality_aqi}`;
                        aqiBadge.title = `AQI: ${updatedCam.air_quality_aqi}`;
                    } else if (aqiBadge) {
                        aqiBadge.remove();
                    }
                }
            }
            
            // Update sidebar item badges directly
            const listItem = document.getElementById(`cam-list-item-${updatedCam.id}`);
            if (listItem) {
                const header = listItem.querySelector('.item-header');
                if (header) {
                    let badgesWrapper = header.querySelector('.item-badges');
                    if (badgesWrapper) {
                        // Update safety pill
                        let safetyPill = badgesWrapper.querySelector('.list-safety-badge');
                        if (updatedCam.safety_summary) {
                            if (!safetyPill) {
                                safetyPill = document.createElement('span');
                                badgesWrapper.insertBefore(safetyPill, badgesWrapper.firstChild);
                            }
                            let safetyClass = 'safety-safe';
                            if (updatedCam.safety_summary === 'Accident' || updatedCam.safety_summary === 'Collision') {
                                safetyClass = 'safety-danger';
                            } else if (updatedCam.safety_summary === 'Hazard') {
                                safetyClass = 'safety-warning';
                            }
                            safetyPill.className = `list-safety-badge ${safetyClass}`;
                            safetyPill.textContent = updatedCam.safety_summary;
                        } else if (safetyPill) {
                            safetyPill.remove();
                        }

                        // Update count pill
                        let countPill = badgesWrapper.querySelector('.list-count-badge');
                        if (updatedCam.latest_count_summary) {
                            if (!countPill) {
                                countPill = document.createElement('span');
                                countPill.className = `list-count-badge ${currentFeed === 'zoo' ? 'zoo-accent' : 'traffic-accent'}`;
                                badgesWrapper.appendChild(countPill);
                            }
                            countPill.textContent = updatedCam.latest_count_summary;
                        } else if (countPill) {
                            countPill.remove();
                        }

                        // Update AQI pill
                        let aqiPill = badgesWrapper.querySelector('.list-aqi-badge');
                        if (updatedCam.air_quality_summary) {
                            if (!aqiPill) {
                                aqiPill = document.createElement('span');
                                badgesWrapper.appendChild(aqiPill);
                            }
                            aqiPill.className = `list-aqi-badge ${updatedCam.air_quality_css_class || ''}`;
                            aqiPill.textContent = `AQI ${updatedCam.air_quality_aqi}`;
                            aqiPill.title = `AQI: ${updatedCam.air_quality_aqi}`;
                        } else if (aqiPill) {
                            aqiPill.remove();
                        }
                    }
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
