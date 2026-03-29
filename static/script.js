// static/script.js - Frontend JavaScript

// DOM Elements
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const previewImg = document.getElementById('preview-img');
const processBtn = document.getElementById('process-btn');
const loading = document.getElementById('loading');
const statsDiv = document.getElementById('stats');
const fallbackMode = document.getElementById('fallback-mode');

// Tab elements
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = {
    model: document.getElementById('tab-model'),
    materials: document.getElementById('tab-materials'),
    explanation: document.getElementById('tab-explanation')
};

// Store current uploaded file
let currentFile = null;

// ========== Drag & Drop Upload ==========
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleFileSelect(file);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    currentFile = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// ========== Tab Switching ==========
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;
        
        // Update active tab button
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update active content
        Object.keys(tabContents).forEach(key => {
            tabContents[key].classList.remove('active');
        });
        tabContents[tabId].classList.add('active');
    });
});

// ========== Process Image ==========
processBtn.addEventListener('click', async () => {
    if (!currentFile) {
        alert('Please upload a floor plan image first');
        return;
    }
    
    // Show loading
    loading.style.display = 'block';
    processBtn.disabled = true;
    statsDiv.style.display = 'none';
    
    // Clear previous results
    document.getElementById('model-container').innerHTML = '<p style="text-align: center; color: #aaa; padding: 40px;">Loading 3D model...</p>';
    document.getElementById('materials-container').innerHTML = '<p style="text-align: center; color: #aaa; padding: 40px;">Analyzing materials...</p>';
    document.getElementById('explanation-container').innerHTML = '<p style="text-align: center; color: #aaa; padding: 40px;">Generating explanation...</p>';
    
    // Prepare form data
    const formData = new FormData();
    formData.append('floor_plan', currentFile);
    formData.append('use_fallback', fallbackMode.checked);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update stats
            document.getElementById('stat-walls').textContent = data.stats.total_walls;
            document.getElementById('stat-lb').textContent = data.stats.load_bearing_walls;
            document.getElementById('stat-rooms').textContent = data.stats.total_rooms;
            document.getElementById('stat-area').textContent = `${data.stats.total_area.toFixed(1)} m²`;
            statsDiv.style.display = 'block';
            
            // Display 3D model in iframe
            document.getElementById('model-container').innerHTML = `
                <iframe src="${data.model_url}" class="model-frame" style="width:100%; height:500px; border:none; border-radius:8px;"></iframe>
            `;
            
            // Display material recommendations
            displayMaterialRecommendations(data.recommendations);
            
            // Display explanation
            displayExplanation(data.explanation, data.spans);
            
            // Switch to model tab
            document.querySelector('.tab-btn[data-tab="model"]').click();
            
        } else {
            alert('Error: ' + data.error);
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error processing image: ' + error.message);
    } finally {
        loading.style.display = 'none';
        processBtn.disabled = false;
    }
});

function displayMaterialRecommendations(recommendations) {
    const container = document.getElementById('materials-container');
    
    if (!recommendations || Object.keys(recommendations).length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #aaa;">No recommendations available</p>';
        return;
    }
    
    const elementNames = {
        'load_bearing_wall': '🏛️ Load-Bearing Walls',
        'partition_wall': '🚪 Partition Walls',
        'slab': '🏗️ Floor Slab',
        'column': '📐 Columns'
    };
    
    let html = '';
    
    for (const [element, recs] of Object.entries(recommendations)) {
        if (!recs || recs.length === 0) continue;
        
        html += `<h3 style="margin-top: 20px; margin-bottom: 10px;">${elementNames[element] || element}</h3>`;
        
        for (const rec of recs) {
            const rankBadge = rec.rank === 1 ? '🥇' : (rec.rank === 2 ? '🥈' : '🥉');
            
            html += `
                <div class="material-card">
                    <div class="material-title">${rankBadge} ${rec.material} <span style="font-size: 12px; color: #44ffaa;">(Score: ${rec.score}/100)</span></div>
                    <div class="material-stats">
                        <span class="stat-badge">💰 $${rec.cost}/m²</span>
                        <span class="stat-badge">💪 ${rec.strength} MPa</span>
                        <span class="stat-badge">🔧 Durability: ${rec.durability}/10</span>
                    </div>
                    <div class="justification">📝 ${rec.justification}</div>
                </div>
            `;
        }
    }
    
    container.innerHTML = html;
}

function displayExplanation(explanation, spans) {
    const container = document.getElementById('explanation-container');
    
    if (!explanation) {
        container.innerHTML = '<p style="text-align: center; color: #aaa;">No explanation available</p>';
        return;
    }
    
    let html = `
        <div class="explanation-box">
            <h3>📋 Executive Summary</h3>
            <p>${explanation.summary || 'Analysis complete'}</p>
        </div>
    `;
    
    // Structural concerns
    if (explanation.structural_concerns && explanation.structural_concerns.length > 0) {
        html += `
            <div class="explanation-box">
                <h3>⚠️ Structural Analysis</h3>
                ${explanation.structural_concerns.map(c => `<p>${c}</p>`).join('')}
            </div>
        `;
    }
    
    // Material rationale
    if (explanation.material_rationale) {
        html += `
            <div class="explanation-box">
                <h3>🧱 Material Selection Rationale</h3>
        `;
        
        for (const [element, data] of Object.entries(explanation.material_rationale)) {
            html += `
                <p><strong>${element.replace('_', ' ').toUpperCase()}:</strong><br>
                ✅ ${data.recommended}<br>
                📝 ${data.why}<br>
                🔄 Alternatives: ${data.alternatives.join(', ')}</p>
                <hr style="opacity:0.2;">
            `;
        }
        
        html += `</div>`;
    }
    
    // Cost analysis
    if (explanation.cost_analysis) {
        html += `
            <div class="explanation-box">
                <h3>💰 Cost Analysis</h3>
                <p><strong>Estimated Total Cost:</strong> ${explanation.cost_analysis.estimated_total}</p>
                <p><strong>Breakdown:</strong> ${explanation.cost_analysis.breakdown}</p>
                <p><strong>💡 Savings Tip:</strong> ${explanation.cost_analysis.savings_tip}</p>
            </div>
        `;
    }
    
    container.innerHTML = html;
}