// Application State
let currentFeed = 'traffic';
let cameras = [];
let filteredCameras = [];
let selectedCameraId = null;
let map = null;
let markers = [];
let infoWindow = null;

// Premium dark stylesheet for Google Maps
const darkMapStyle = [
    { elementType: "geometry", stylers: [{ color: "#07070a" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#0a0a0f" }, { weight: 2 }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#71717a" }] },
    {
        featureType: "administrative.locality",
        elementType: "labels.text.fill",
        stylers: [{ color: "#a1a1aa" }]
    },
    {
        featureType: "poi",
        elementType: "labels.text.fill",
        stylers: [{ color: "#52525b" }]
    },
    {
        featureType: "poi.park",
        elementType: "geometry",
        stylers: [{ color: "#0a0a0f" }]
    },
    {
        featureType: "poi.park",
        elementType: "labels.text.fill",
        stylers: [{ color: "#3f3f46" }]
    },
    {
        featureType: "road",
        elementType: "geometry",
        stylers: [{ color: "#18181b" }]
    },
    {
        featureType: "road",
        elementType: "geometry.stroke",
        stylers: [{ color: "#0a0a0f" }]
    },
    {
        featureType: "road",
        elementType: "labels.text.fill",
        stylers: [{ color: "#52525b" }]
    },
    {
        featureType: "road.highway",
        elementType: "geometry",
        stylers: [{ color: "#18181b" }]
    },
    {
        featureType: "road.highway",
        elementType: "geometry.stroke",
        stylers: [{ color: "#040406" }]
    },
    {
        featureType: "road.highway",
        elementType: "labels.text.fill",
        stylers: [{ color: "#e4e4e7" }]
    },
    {
        featureType: "transit",
        elementType: "geometry",
        stylers: [{ color: "#0a0a0f" }]
    },
    {
        featureType: "transit.station",
        elementType: "labels.text.fill",
        stylers: [{ color: "#52525b" }]
    },
    {
        featureType: "water",
        elementType: "geometry",
        stylers: [{ color: "#050508" }]
    },
    {
        featureType: "water",
        elementType: "labels.text.fill",
        stylers: [{ color: "#3f3f46" }]
    },
    {
        featureType: "water",
        elementType: "labels.text.stroke",
        stylers: [{ color: "#0a0a0f" }]
    }
];

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
    initMap();
    fetchCameras();
    setupEventListeners();
});

// Initialize Google Map
function initMap() {
    const bayAreaCenter = { lat: 37.7749, lng: -122.4194 };
    
    map = new google.maps.Map(document.getElementById('map'), {
        center: bayAreaCenter,
        zoom: 9.5,
        styles: darkMapStyle,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        zoomControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM
        }
    });

    infoWindow = new google.maps.InfoWindow();
}

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

    // Auto-refresh feeds list every 2 minutes
    setInterval(() => {
        if (!cameraModal.classList.contains('show')) {
            fetchCameras();
        }
    }, 120000);
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
        
        // Relocate map to San Diego Zoo
        const zooCenter = { lat: 32.7350, lng: -117.1500 };
        map.setCenter(zooCenter);
        map.setZoom(16);
    } else {
        routeFilterLabel.textContent = 'Filter by Route';
        countyFilterLabel.textContent = 'Filter by County';
        modalLblRoute.textContent = 'Route:';
        modalLblCounty.textContent = 'County:';
        
        // Relocate map to Bay Area
        const bayAreaCenter = { lat: 37.7749, lng: -122.4194 };
        map.setCenter(bayAreaCenter);
        map.setZoom(9.5);
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
    renderMapMarkers();
    renderListView();
    renderGalleryView();
}

// Render Pins on Google Map
function renderMapMarkers() {
    // Clear old markers
    markers.forEach(m => m.setMap(null));
    markers = [];
    
    filteredCameras.forEach((cam, index) => {
        if (cam.latitude && cam.longitude) {
            const latLng = { lat: cam.latitude, lng: cam.longitude };
            const markerImgUrl = cam.youtube_id ? `https://www.youtube.com/watch?v=${cam.youtube_id}` : cam.img_url;
            const proxiedImg = `/api/proxy?url=${encodeURIComponent(markerImgUrl)}`;
            const isSelected = selectedCameraId === index;
            
            // Neon Violet for Zoo, Neon Cyan for Traffic
            const activeColor = currentFeed === 'zoo' ? '#8b5cf6' : '#06b6d4';
            
            const marker = new google.maps.Marker({
                position: latLng,
                map: map,
                title: cam.name,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    fillColor: isSelected ? '#ffffff' : activeColor,
                    fillOpacity: 0.9,
                    strokeColor: isSelected ? activeColor : '#ffffff',
                    strokeWeight: 1.5,
                    scale: isSelected ? 8 : 6
                }
            });
            
            const popupContent = `
                <div style="font-family: var(--font-sans); width: 220px; display: flex; flex-direction: column; gap: 4px; padding: 2px;">
                    <strong style="color: #ffffff; font-size: 0.85rem; line-height: 1.2;">${cam.name}</strong>
                    <span style="color: #a1a1aa; font-size: 0.75rem;">Nearby: ${cam.nearby}</span>
                    <img src="${proxiedImg}" alt="${cam.name}" style="width: 100%; height: 130px; object-fit: cover; border-radius: 6px; margin-top: 4px; border: 1px solid rgba(255,255,255,0.05);" />
                    <button onclick="window.selectCameraFromMap(${index})" style="background: ${activeColor}; border: none; padding: 6px 8px; border-radius: 4px; font-size: 0.75rem; color: #000; font-weight: 600; cursor: pointer; margin-top: 6px; text-align: center; width: 100%;">Analyze Feed</button>
                </div>
            `;
            
            marker.addListener('click', () => {
                infoWindow.setContent(popupContent);
                infoWindow.open(map, marker);
                selectCamera(index, false);
            });
            
            markers.push(marker);
        }
    });

    // Make marker button click callback global
    window.selectCameraFromMap = (idx) => {
        selectCamera(idx, false);
        openModal(idx);
    };
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
        
        const routeLabel = currentFeed === 'traffic' ? 'Route' : 'Zone';
        const countyLabel = currentFeed === 'traffic' ? cam.county : cam.county;
        
        item.innerHTML = `
            <div class="item-name">${cam.name}</div>
            <div class="item-meta">
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
        card.id = `cam-card-${idx}`;
        if (selectedCameraId === idx) {
            card.style.borderColor = 'var(--accent-violet)';
            card.style.boxShadow = 'var(--shadow-glow)';
        }
        
        const cardImgUrl = cam.youtube_id ? `https://www.youtube.com/watch?v=${cam.youtube_id}` : cam.img_url;
        const proxiedImg = `/api/proxy?url=${encodeURIComponent(cardImgUrl)}`;
        
        card.innerHTML = `
            <div class="card-img-wrapper" onclick="openModal(${idx})">
                <img src="${proxiedImg}" alt="Live feed for ${cam.name}" class="card-img" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22><rect width=%22100%22 height=%22100%22 fill=%22%230d0d15%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%2352525b%22>FEED OFFLINE</text></svg>';" />
                <div class="card-badge">Live</div>
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
        const marker = markers[idx];
        if (marker) {
            if (panToMarker) {
                map.panTo(marker.getPosition());
                map.setZoom(currentFeed === 'zoo' ? 17 : 12);
            }
            google.maps.event.trigger(marker, 'click');
        }
        
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
