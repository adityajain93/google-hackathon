// Application State
let cameras = [];
let filteredCameras = [];
let selectedCameraId = null;
let map = null;
let markers = [];
let infoWindow = null;

// Premium dark stylesheet for Google Maps
const darkMapStyle = [
    { elementType: "geometry", stylers: [{ color: "#0a0e17" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#0f172a" }, { weight: 2 }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#94a3b8" }] },
    {
        featureType: "administrative.locality",
        elementType: "labels.text.fill",
        stylers: [{ color: "#cbd5e1" }]
    },
    {
        featureType: "poi",
        elementType: "labels.text.fill",
        stylers: [{ color: "#64748b" }]
    },
    {
        featureType: "poi.park",
        elementType: "geometry",
        stylers: [{ color: "#0f172a" }]
    },
    {
        featureType: "poi.park",
        elementType: "labels.text.fill",
        stylers: [{ color: "#475569" }]
    },
    {
        featureType: "road",
        elementType: "geometry",
        stylers: [{ color: "#1e293b" }]
    },
    {
        featureType: "road",
        elementType: "geometry.stroke",
        stylers: [{ color: "#0f172a" }]
    },
    {
        featureType: "road",
        elementType: "labels.text.fill",
        stylers: [{ color: "#64748b" }]
    },
    {
        featureType: "road.highway",
        elementType: "geometry",
        stylers: [{ color: "#1e293b" }]
    },
    {
        featureType: "road.highway",
        elementType: "geometry.stroke",
        stylers: [{ color: "#0a0e17" }]
    },
    {
        featureType: "road.highway",
        elementType: "labels.text.fill",
        stylers: [{ color: "#e2e8f0" }]
    },
    {
        featureType: "transit",
        elementType: "geometry",
        stylers: [{ color: "#0f172a" }]
    },
    {
        featureType: "transit.station",
        elementType: "labels.text.fill",
        stylers: [{ color: "#64748b" }]
    },
    {
        featureType: "water",
        elementType: "geometry",
        stylers: [{ color: "#080c14" }]
    },
    {
        featureType: "water",
        elementType: "labels.text.fill",
        stylers: [{ color: "#475569" }]
    },
    {
        featureType: "water",
        elementType: "labels.text.stroke",
        stylers: [{ color: "#0f172a" }]
    }
];

// DOM Elements
const activeCountEl = document.getElementById('active-count');
const lastUpdatedEl = document.getElementById('last-updated-time');
const searchInput = document.getElementById('search-input');
const routeFilter = document.getElementById('route-filter');
const countyFilter = document.getElementById('county-filter');
const cameraList = document.getElementById('camera-list');
const cameraGallery = document.getElementById('camera-gallery');
const galleryHeaderTitle = document.getElementById('gallery-header-title');

// Modal Elements
const cameraModal = document.getElementById('camera-modal');
const modalImage = document.getElementById('modal-image');
const modalTitle = document.getElementById('modal-camera-title');
const modalRoute = document.getElementById('modal-route');
const modalDirection = document.getElementById('modal-direction');
const modalCounty = document.getElementById('modal-county');
const modalNearby = document.getElementById('modal-nearby');
const modalCloseBtn = document.getElementById('modal-close-btn');

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

// Fetch Camera List from Local API
async function fetchCameras() {
    showLoadingState();
    try {
        const response = await fetch('/api/cameras');
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
        <div class="shimmer" style="height: 60px; border-radius: 8px; margin-bottom: 0.5rem;"></div>
        <div class="shimmer" style="height: 60px; border-radius: 8px; margin-bottom: 0.5rem;"></div>
        <div class="shimmer" style="height: 60px; border-radius: 8px; margin-bottom: 0.5rem;"></div>
    `;
    cameraGallery.innerHTML = `
        <div class="camera-card shimmer" style="height: 280px; border-radius: 12px;"></div>
        <div class="camera-card shimmer" style="height: 280px; border-radius: 12px;"></div>
        <div class="camera-card shimmer" style="height: 280px; border-radius: 12px;"></div>
    `;
}

// Show Error Message
function showErrorState() {
    const errorHTML = `<div class="empty-state">Failed to load camera feeds. Please check the backend server.</div>`;
    cameraList.innerHTML = errorHTML;
    cameraGallery.innerHTML = errorHTML;
}

// Populate Filter Options
function populateFilters(camList) {
    const routes = new Set();
    const counties = new Set();
    
    camList.forEach(cam => {
        if (cam.route) routes.add(cam.route);
        if (cam.county) counties.add(cam.county);
    });
    
    const sortedRoutes = Array.from(routes).sort((a, b) => {
        const aNum = parseInt(a.replace(/\D/g, ''));
        const bNum = parseInt(b.replace(/\D/g, ''));
        if (isNaN(aNum) || isNaN(bNum)) return a.localeCompare(b);
        return aNum - bNum;
    });
    
    const sortedCounties = Array.from(counties).sort();
    
    routeFilter.innerHTML = '<option value="all">All Routes</option>';
    countyFilter.innerHTML = '<option value="all">All Counties</option>';
    
    sortedRoutes.forEach(route => {
        routeFilter.innerHTML += `<option value="${route}">${route}</option>`;
    });
    
    sortedCounties.forEach(county => {
        countyFilter.innerHTML += `<option value="${county}">${county}</option>`;
    });
}

// Setup Event Listeners
function setupEventListeners() {
    searchInput.addEventListener('input', filterCameras);
    routeFilter.addEventListener('change', filterCameras);
    countyFilter.addEventListener('change', filterCameras);
    
    modalCloseBtn.addEventListener('click', closeModal);
    cameraModal.addEventListener('click', (e) => {
        if (e.target === cameraModal) closeModal();
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    setInterval(refreshImages, 120000);
}

// Filter Cameras based on Sidebar Inputs
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
    
    galleryHeaderTitle.textContent = searchQuery || selectedRoute !== 'all' || selectedCounty !== 'all' 
        ? `Filtered Feeds (${filteredCameras.length})` 
        : `Live Feeds (${filteredCameras.length})`;
        
    renderApp();
}

// Main Render Function
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
            const proxiedImg = `/api/proxy?url=${encodeURIComponent(cam.img_url)}`;
            
            const isSelected = selectedCameraId === index;
            
            const marker = new google.maps.Marker({
                position: latLng,
                map: map,
                title: cam.name,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    fillColor: isSelected ? '#6366f1' : '#06b6d4',
                    fillOpacity: 0.9,
                    strokeColor: '#ffffff',
                    strokeWeight: 1.5,
                    scale: isSelected ? 8 : 6
                }
            });
            
            const popupContent = `
                <div style="font-family: var(--font-sans); width: 220px; display: flex; flex-direction: column; gap: 4px; padding: 2px;">
                    <strong style="color: #0f172a; font-size: 0.85rem; line-height: 1.2;">${cam.name}</strong>
                    <span style="color: #64748b; font-size: 0.75rem;">Nearby: ${cam.nearby}</span>
                    <img src="${proxiedImg}" alt="${cam.name}" style="width: 100%; height: 130px; object-fit: cover; border-radius: 6px; margin-top: 4px; border: 1px solid rgba(0,0,0,0.1);" />
                    <button onclick="window.selectCameraFromMap(${index})" style="background: #06b6d4; border: none; padding: 5px 8px; border-radius: 4px; font-size: 0.75rem; color: #000; font-weight: 600; cursor: pointer; margin-top: 6px; text-align: center; width: 100%;">Focus Card</button>
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

    // Make selectCameraFromMap accessible globally for InfoWindow button click
    window.selectCameraFromMap = (idx) => {
        selectCamera(idx, false);
    };
}

// Render Left Sidebar List
function renderListView() {
    if (filteredCameras.length === 0) {
        cameraList.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 1rem;">No cameras match the filters.</div>`;
        return;
    }
    
    cameraList.innerHTML = '';
    filteredCameras.forEach((cam, idx) => {
        const item = document.createElement('div');
        item.className = `camera-list-item ${selectedCameraId === idx ? 'selected' : ''}`;
        item.innerHTML = `
            <div class="item-name">${cam.name}</div>
            <div class="item-meta">
                <span>Route: ${cam.route} (${cam.direction})</span>
                <span>${cam.nearby}</span>
            </div>
        `;
        item.addEventListener('click', () => selectCamera(idx, true));
        cameraList.appendChild(item);
    });
}

// Render Card Gallery
function renderGalleryView() {
    if (filteredCameras.length === 0) {
        cameraGallery.innerHTML = `<div class="empty-state">No cameras matched your search criteria. Please adjust filters.</div>`;
        return;
    }
    
    cameraGallery.innerHTML = '';
    
    filteredCameras.forEach((cam, idx) => {
        const card = document.createElement('div');
        card.className = 'camera-card';
        card.id = `cam-card-${idx}`;
        if (selectedCameraId === idx) {
            card.style.borderColor = 'var(--accent-cyan)';
            card.style.boxShadow = 'var(--shadow-glow)';
        }
        
        const proxiedImg = `/api/proxy?url=${encodeURIComponent(cam.img_url)}`;
        
        card.innerHTML = `
            <div class="card-img-wrapper" onclick="openModal(${idx})">
                <img src="${proxiedImg}" alt="Live feed for ${cam.name}" class="card-img" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22><rect width=%22100%22 height=%22100%22 fill=%22%23222%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23777%22>Feed Offline</text></svg>';" />
                <div class="card-badge">Live</div>
            </div>
            <div class="card-body">
                <div class="card-title">${cam.name}</div>
                <div class="card-meta">
                    <span>${cam.nearby}</span>
                    <span>Route ${cam.route}</span>
                </div>
            </div>
        `;
        cameraGallery.appendChild(card);
    });
}

// Select a Camera and focus it
function selectCamera(idx, panToMarker = true) {
    selectedCameraId = idx;
    
    // Highlight list item and card
    renderListView();
    renderGalleryView();
    
    const cam = filteredCameras[idx];
    if (cam) {
        const marker = markers[idx];
        if (marker) {
            if (panToMarker) {
                map.panTo(marker.getPosition());
                map.setZoom(12);
            }
            
            // Trigger marker click to open InfoWindow
            google.maps.event.trigger(marker, 'click');
        }
        
        // Scroll card into view
        const card = document.getElementById(`cam-card-${idx}`);
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

// Open Detail Modal
function openModal(idx) {
    const cam = filteredCameras[idx];
    if (!cam) return;
    
    const timestamp = new Date().getTime();
    const proxiedImg = `/api/proxy?url=${encodeURIComponent(cam.img_url)}&t=${timestamp}`;
    
    modalImage.src = proxiedImg;
    modalImage.alt = cam.name;
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
    modalImage.src = '';
}

// Refresh all camera cards
function refreshImages() {
    console.log('[App] Refreshing live camera feeds...');
    fetchCameras();
}
