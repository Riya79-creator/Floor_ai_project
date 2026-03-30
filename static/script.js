/**
 * script.js - FloorAI Frontend with 3D Visualization
 */

// DOM Elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const previewContainer = document.getElementById('previewContainer');
const previewImg = document.getElementById('previewImg');
const clearPreview = document.getElementById('clearPreview');
const fallbackToggle = document.getElementById('fallbackToggle');
const processBtn = document.getElementById('processBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const heroUploadBtn = document.getElementById('heroUploadBtn');

// Tabs
const tab2dBtn = document.getElementById('tab2dBtn');
const tab3dBtn = document.getElementById('tab3dBtn');
const tabAnalysisBtn = document.getElementById('tabAnalysisBtn');
const tab2dContent = document.getElementById('tab2dContent');
const tab3dContent = document.getElementById('tab3dContent');
const tabAnalysisContent = document.getElementById('tabAnalysisContent');

// Stats elements
const statWallsSpan = document.getElementById('statWalls');
const statLBSpan = document.getElementById('statLB');
const statRoomsSpan = document.getElementById('statRooms');
const statAreaSpan = document.getElementById('statArea');
const analysisCommentSpan = document.getElementById('analysisComment');
const detectionStatusP = document.getElementById('detectionStatus');
const wallCanvas = document.getElementById('wallOverlayCanvas');
const iframeWrapper = document.getElementById('iframeWrapper');
const materialGrid = document.getElementById('materialCardsGrid');
const furnitureGrid = document.getElementById('furnitureGrid');

let currentFile = null;
let currentModelUrl = null;

// Reset UI
function resetUI() {
    statWallsSpan.innerText = '—';
    statLBSpan.innerText = '—';
    statRoomsSpan.innerText = '—';
    statAreaSpan.innerText = '—';
    analysisCommentSpan.innerText = 'Upload a floor plan to see structural analysis.';
    detectionStatusP.innerText = 'Waiting for floor plan upload. AI will detect walls & rooms.';
    
    materialGrid.innerHTML = `<div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm text-center text-slate-400">
        <i class="fas fa-box-open text-2xl mb-2 block"></i> Upload to see recommendations
    </div>`;
    
    furnitureGrid.innerHTML = `<div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm text-center text-slate-400">
        <i class="fas fa-couch text-2xl mb-2 block"></i> Upload to see furniture placement
    </div>`;
    
    if (currentModelUrl) {
        iframeWrapper.innerHTML = `<div class="text-center text-slate-300">
            <i class="fas fa-cube fa-3x mb-2 opacity-50"></i>
            <p class="text-sm">3D model will appear here after processing</p>
        </div>`;
        currentModelUrl = null;
    }
    
    wallCanvas.style.display = 'none';
    const ctx = wallCanvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, wallCanvas.width, wallCanvas.height);
}

// File handling
function handleFile(file) {
    if (!file || !file.type.startsWith('image/')) return;
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewContainer.classList.remove('hidden');
        resetUI();
    };
    reader.readAsDataURL(file);
}

dropzone.addEventListener('click', () => fileInput.click());
selectFileBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('border-blue-400', 'bg-blue-50');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('border-blue-400', 'bg-blue-50'));
dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('border-blue-400', 'bg-blue-50');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) handleFile(file);
});

clearPreview.addEventListener('click', () => {
    previewContainer.classList.add('hidden');
    currentFile = null;
    resetUI();
});
heroUploadBtn.addEventListener('click', () => fileInput.click());

// Tab switching
function setActiveTab(tabId) {
    [tab2dBtn, tab3dBtn, tabAnalysisBtn].forEach(btn => {
        btn.classList.remove('tab-active');
        btn.classList.add('tab-inactive');
    });
    
    if (tabId === '2d') {
        tab2dBtn.classList.add('tab-active');
        tab2dContent.classList.remove('hidden');
        tab3dContent.classList.add('hidden');
        tabAnalysisContent.classList.add('hidden');
    } else if (tabId === '3d') {
        tab3dBtn.classList.add('tab-active');
        tab2dContent.classList.add('hidden');
        tab3dContent.classList.remove('hidden');
        tabAnalysisContent.classList.add('hidden');
    } else {
        tabAnalysisBtn.classList.add('tab-active');
        tab2dContent.classList.add('hidden');
        tab3dContent.classList.add('hidden');
        tabAnalysisContent.classList.remove('hidden');
    }
}

tab2dBtn.addEventListener('click', () => setActiveTab('2d'));
tab3dBtn.addEventListener('click', () => setActiveTab('3d'));
tabAnalysisBtn.addEventListener('click', () => setActiveTab('analysis'));

// Process floor plan
async function processFloorPlan() {
    if (!currentFile) {
        alert("Please upload a floor plan image first.");
        return;
    }
    
    loadingIndicator.classList.remove('hidden');
    processBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('floor_plan', currentFile);
    formData.append('use_fallback', fallbackToggle.checked ? 'true' : 'false');
    
    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const data = await response.json();
        
        if (!data.success) throw new Error(data.error || "Processing failed");
        
        // Update stats
        if (data.stats) {
            statWallsSpan.innerText = data.stats.total_walls ?? '—';
            statLBSpan.innerText = data.stats.load_bearing ?? '—';
            statRoomsSpan.innerText = data.stats.total_rooms ?? '—';
            statAreaSpan.innerText = data.stats.total_area ? `${data.stats.total_area.toFixed(1)} m²` : '—';
            analysisCommentSpan.innerText = `Detected ${data.stats.total_rooms} rooms, ${data.stats.load_bearing} load-bearing walls, ${data.stats.total_doors} doors, ${data.stats.total_windows} windows.`;
            detectionStatusP.innerText = `✅ Detected ${data.walls.length} walls, ${data.rooms.length} rooms, ${data.doors.length} doors, ${data.windows.length} windows`;
        }
        
        // Draw 2D plan
        if (data.walls && data.walls.length) {
            draw2DPlan(data.walls);
        }
        
        // Load 3D model
        if (data.model_url) {
            currentModelUrl = data.model_url;
            iframeWrapper.innerHTML = `<iframe src="${data.model_url}" class="w-full h-full rounded-lg border-0" style="min-height: 380px; width:100%;" allowfullscreen></iframe>`;
        }
        
        // Display material recommendations
        if (data.recommendations) {
            displayMaterialRecommendations(data.recommendations);
        }
        
        // Display furniture suggestions
        if (data.furniture_placement) {
            displayFurnitureSuggestions(data.furniture_placement);
        }
        
        // Switch to 3D tab
        setActiveTab('3d');
        
    } catch (err) {
        console.error(err);
        alert("Error: " + err.message);
        detectionStatusP.innerText = "❌ AI processing failed. Try manual mode or different image.";
    } finally {
        loadingIndicator.classList.add('hidden');
        processBtn.disabled = false;
    }
}

function draw2DPlan(walls) {
    wallCanvas.style.display = 'block';
    const ctx = wallCanvas.getContext('2d');
    const w = 500, h = 400;
    wallCanvas.width = w;
    wallCanvas.height = h;
    ctx.clearRect(0, 0, w, h);
    
    // Find bounds
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    walls.forEach(wall => {
        minX = Math.min(minX, wall.start[0], wall.end[0]);
        maxX = Math.max(maxX, wall.start[0], wall.end[0]);
        minY = Math.min(minY, wall.start[1], wall.end[1]);
        maxY = Math.max(maxY, wall.start[1], wall.end[1]);
    });
    
    const pad = 30;
    const scaleX = (w - pad * 2) / (maxX - minX || 1);
    const scaleY = (h - pad * 2) / (maxY - minY || 1);
    
    walls.forEach(wall => {
        const sx = pad + (wall.start[0] - minX) * scaleX;
        const sy = h - pad - (wall.start[1] - minY) * scaleY;
        const ex = pad + (wall.end[0] - minX) * scaleX;
        const ey = h - pad - (wall.end[1] - minY) * scaleY;
        
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(ex, ey);
        
        if (wall.is_load_bearing) {
            ctx.strokeStyle = '#FF6B6B';
            ctx.lineWidth = 4;
        } else {
            ctx.strokeStyle = '#C9AE8C';
            ctx.lineWidth = 3;
        }
        ctx.stroke();
    });
}

function displayMaterialRecommendations(recommendations) {
    let cardsHtml = '';
    const titles = {
        load_bearing_wall: '🧱 Load-Bearing Wall',
        partition_wall: '🚪 Partition Wall',
        slab: '🏗️ Slab',
        column: '📐 Column'
    };
    
    for (const [key, recs] of Object.entries(recommendations)) {
        if (recs && recs.length) {
            const top = recs[0];
            cardsHtml += `
                <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm card-hover">
                    <div class="flex justify-between items-start mb-2">
                        <h3 class="font-semibold text-slate-800">${titles[key] || key}</h3>
                        <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Score ${top.score}</span>
                    </div>
                    <p class="text-lg font-bold text-slate-900">${top.material}</p>
                    <div class="flex justify-between text-sm mt-2">
                        <span><i class="fas fa-dollar-sign text-slate-400"></i> ${top.cost}/m²</span>
                        <span><i class="fas fa-weight-hanging"></i> ${top.strength} MPa</span>
                        <span><i class="fas fa-shield-alt"></i> Dur:${top.durability}/10</span>
                    </div>
                    <p class="text-xs text-slate-500 mt-3 border-t pt-2">${top.justification.substring(0, 100)}</p>
                </div>
            `;
        }
    }
    
    if (cardsHtml) {
        materialGrid.innerHTML = cardsHtml;
    }
}

function displayFurnitureSuggestions(furniturePlacement) {
    let furnitureHtml = '';
    
    for (const [roomType, placement] of Object.entries(furniturePlacement)) {
        if (placement.furniture && placement.furniture.length) {
            furnitureHtml += `
                <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                    <h3 class="font-semibold text-slate-800 mb-3 capitalize">${roomType.replace('_', ' ')}</h3>
                    <div class="space-y-2">
            `;
            
            placement.furniture.forEach(item => {
                furnitureHtml += `
                    <div class="flex items-center justify-between text-sm p-2 bg-slate-50 rounded-lg">
                        <div>
                            <span class="font-medium">${item.name}</span>
                            <span class="text-xs text-slate-400 block">${item.size[0]}m x ${item.size[1]}m x ${item.size[2]}m</span>
                        </div>
                        <div class="text-right">
                            <span class="font-semibold text-green-600">₹${item.price.toLocaleString()}</span>
                            <span class="text-xs text-slate-400 block">${item.reason}</span>
                        </div>
                    </div>
                `;
            });
            
            furnitureHtml += `
                        <div class="mt-3 pt-2 border-t">
                            <span class="text-sm font-semibold">Total: ₹${placement.total_cost.toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    if (furnitureHtml) {
        furnitureGrid.innerHTML = furnitureHtml;
    }
}

processBtn.addEventListener('click', processFloorPlan);
setActiveTab('2d');
resetUI();