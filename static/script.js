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

function draw2DPlan(walls, rooms) {
    if (!wallCanvas) return;
    
    wallCanvas.style.display = 'block';
    const ctx = wallCanvas.getContext('2d');
    const w = 500, h = 400;
    wallCanvas.width = w;
    wallCanvas.height = h;
    ctx.clearRect(0, 0, w, h);
    
    // Draw background grid
    ctx.save();
    ctx.strokeStyle = '#E2E8F0';
    ctx.lineWidth = 0.5;
    
    // Draw grid lines every 50 pixels
    for (let x = 0; x <= w; x += 50) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
    }
    for (let y = 0; y <= h; y += 50) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }
    
    if (!walls || walls.length === 0) {
        ctx.fillStyle = '#94A3B8';
        ctx.font = '14px Inter';
        ctx.fillText('No walls detected. Try a clearer image or enable fallback mode.', 50, h/2);
        ctx.restore();
        return;
    }
    
    // Find bounds with padding
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    walls.forEach(wall => {
        minX = Math.min(minX, wall.start[0], wall.end[0]);
        maxX = Math.max(maxX, wall.start[0], wall.end[0]);
        minY = Math.min(minY, wall.start[1], wall.end[1]);
        maxY = Math.max(maxY, wall.start[1], wall.end[1]);
    });
    
    // Add padding to bounds
    const padding = 40;
    const rangeX = maxX - minX;
    const rangeY = maxY - minY;
    const scaleX = (w - padding * 2) / (rangeX || 1);
    const scaleY = (h - padding * 2) / (rangeY || 1);
    
    // Draw walls with proper scaling
    walls.forEach(wall => {
        const sx = padding + (wall.start[0] - minX) * scaleX;
        const sy = h - padding - (wall.start[1] - minY) * scaleY;
        const ex = padding + (wall.end[0] - minX) * scaleX;
        const ey = h - padding - (wall.end[1] - minY) * scaleY;
        
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
        
        // Draw endpoints for debugging
        ctx.fillStyle = wall.is_load_bearing ? '#FF6B6B' : '#C9AE8C';
        ctx.beginPath();
        ctx.arc(sx, sy, 2, 0, 2 * Math.PI);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(ex, ey, 2, 0, 2 * Math.PI);
        ctx.fill();
    });
    
    // Draw room boundaries if available
    if (rooms && rooms.length) {
        rooms.forEach(room => {
            if (room.polygon && room.polygon.length) {
                ctx.beginPath();
                const points = room.polygon;
                const sx = padding + (points[0][0] - minX) * scaleX;
                const sy = h - padding - (points[0][1] - minY) * scaleY;
                ctx.moveTo(sx, sy);
                
                for (let i = 1; i < points.length; i++) {
                    const x = padding + (points[i][0] - minX) * scaleX;
                    const y = h - padding - (points[i][1] - minY) * scaleY;
                    ctx.lineTo(x, y);
                }
                ctx.closePath();
                ctx.strokeStyle = '#4ECDC4';
                ctx.lineWidth = 2;
                ctx.stroke();
                ctx.fillStyle = 'rgba(78, 205, 196, 0.1)';
                ctx.fill();
            }
        });
    }
    
    // Draw coordinate labels
    ctx.fillStyle = '#64748B';
    ctx.font = '10px monospace';
    ctx.fillText(`${minX.toFixed(1)}m`, padding - 5, h - padding + 10);
    ctx.fillText(`${maxX.toFixed(1)}m`, w - padding - 20, h - padding + 10);
    ctx.fillText(`${minY.toFixed(1)}m`, padding - 5, padding - 5);
    
    ctx.restore();
}

function displayMaterialRecommendations(recommendations) {
    if (!recommendations) return;
    
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
                        <h3 class="font-semibold text-slate-800">${titles[key] || key.replace('_', ' ')}</h3>
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
    if (!furniturePlacement) return;
    
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
        
        // Draw 2D plan with both walls and rooms
        if (data.walls && data.walls.length) {
            draw2DPlan(data.walls, data.rooms || []);
        }

        // Load 3D model
        if (data.model_url) {
            currentModelUrl = data.model_url;
            iframeWrapper.innerHTML = `<iframe src="${data.model_url}" class="w-full h-full rounded-lg border-0" style="min-height: 380px; width:100%; height: 500px;" allowfullscreen></iframe>`;
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

processBtn.addEventListener('click', processFloorPlan);
setActiveTab('2d');
resetUI();
