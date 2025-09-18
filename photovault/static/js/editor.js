/*
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
*/

// Photo Editor functionality
let currentTool = 'move';
let isDrawing = false;
let lastX = 0;
let lastY = 0;
let startX = 0;
let startY = 0;
let canvas, ctx, image;
let brightness = 0, contrast = 0, saturation = 0, rotation = 0;
let imageData = null;

function initEditor() {
    canvas = document.getElementById('canvas');
    ctx = canvas.getContext('2d');
    
    const img = document.getElementById('sourceImage');
    image = new Image();
    image.onload = function() {
        resizeCanvas();
        applyFilters();
    };
    image.src = img.src;
    
    // Add event listeners
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);
    
    // Add touch support for mobile
    canvas.addEventListener('touchstart', handleTouchStart);
    canvas.addEventListener('touchmove', handleTouchMove);
    canvas.addEventListener('touchend', handleTouchEnd);
    
    // Setup filter controls
    document.getElementById('brightness').addEventListener('input', updateFilter);
    document.getElementById('contrast').addEventListener('input', updateFilter);
    document.getElementById('saturation').addEventListener('input', updateFilter);
    document.getElementById('rotation').addEventListener('input', updateFilter);
    
    // Setup color and line width
    document.getElementById('drawColor').addEventListener('input', updateDrawingStyle);
    document.getElementById('lineWidth').addEventListener('input', updateLineWidth);
    document.getElementById('fontSize').addEventListener('input', updateFontSize);
    
    // Add window resize listener for responsive canvas
    window.addEventListener('resize', function() {
        if (image) {
            setTimeout(() => {
                resizeCanvas();
                applyFilters();
            }, 100); // Small delay to allow layout to stabilize
        }
    });
    
    // Note: Editor initialization happens via the global DOMContentLoaded listener at bottom of file
}

function handleTouchStart(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
}

function handleTouchMove(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
}

function handleTouchEnd(e) {
    e.preventDefault();
    const mouseEvent = new MouseEvent('mouseup', {});
    canvas.dispatchEvent(mouseEvent);
}

function setTool(tool) {
    currentTool = tool;
    // Update UI to show active tool
    document.querySelectorAll('.btn-outline-primary').forEach(btn => {
        btn.classList.remove('active', 'tool-active');
    });
    event.target.classList.add('active', 'tool-active');
    
    // Show/hide text input for text tool
    const textInput = document.getElementById('textInput');
    if (tool === 'text') {
        textInput.style.display = 'block';
        textInput.focus();
    } else {
        textInput.style.display = 'none';
    }
}

function startDrawing(e) {
    if (currentTool === 'move') return;
    
    isDrawing = true;
    [lastX, lastY] = getMousePos(canvas, e);
    [startX, startY] = [lastX, lastY];
    
    // Save canvas state for shape drawing
    if (['rectangle', 'circle', 'arrow'].includes(currentTool)) {
        imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    }
    
    // Handle text tool
    if (currentTool === 'text') {
        addText(lastX, lastY);
        isDrawing = false;
        return;
    }
}

function draw(e) {
    if (!isDrawing) return;
    
    const [x, y] = getMousePos(canvas, e);
    const color = document.getElementById('drawColor').value;
    const lineWidth = parseInt(document.getElementById('lineWidth').value);
    const fillShapes = document.getElementById('fillShapes').checked;
    
    // Restore canvas for shape tools
    if (['rectangle', 'circle', 'arrow'].includes(currentTool)) {
        ctx.putImageData(imageData, 0, 0);
    }
    
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    switch (currentTool) {
        case 'pen':
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(x, y);
            ctx.stroke();
            [lastX, lastY] = [x, y];
            break;
            
        case 'highlight':
            ctx.globalAlpha = 0.3;
            ctx.lineWidth = lineWidth * 3;
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(x, y);
            ctx.stroke();
            ctx.globalAlpha = 1.0;
            [lastX, lastY] = [x, y];
            break;
            
        case 'rectangle':
            drawRectangle(startX, startY, x - startX, y - startY, fillShapes);
            break;
            
        case 'circle':
            drawCircle(startX, startY, Math.sqrt((x - startX) ** 2 + (y - startY) ** 2), fillShapes);
            break;
            
        case 'arrow':
            drawArrow(startX, startY, x, y);
            break;
    }
}

function stopDrawing() {
    isDrawing = false;
}

function getMousePos(canvas, evt) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    return [
        (evt.clientX - rect.left) * scaleX,
        (evt.clientY - rect.top) * scaleY
    ];
}

function updateFilter() {
    brightness = parseInt(document.getElementById('brightness').value);
    contrast = parseInt(document.getElementById('contrast').value);
    saturation = parseInt(document.getElementById('saturation').value);
    rotation = parseInt(document.getElementById('rotation').value);
    applyFilters();
}

function updateDrawingStyle() {
    // This is handled in the draw function
}

function applyFilters() {
    if (!image) return;
    
    resizeCanvas();
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Save context
    ctx.save();
    
    // Apply rotation
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.rotate(rotation * Math.PI / 180);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);
    
    // Draw image scaled to fit canvas
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    
    // Apply filters if needed (for more advanced filters, you'd use getImageData)
    if (brightness !== 0 || contrast !== 0 || saturation !== 0) {
        // Simple brightness adjustment
        if (brightness !== 0) {
            ctx.fillStyle = `rgba(255, 255, 255, ${brightness / 100})`;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
    }
    
    // Restore context
    ctx.restore();
}

function resizeCanvas() {
    if (!image) return;
    
    // Get the container dimensions (considering the col-md-8 layout)
    const container = canvas.parentElement;
    const containerWidth = container.clientWidth - 20; // Account for padding
    
    // Calculate available height more accurately
    const containerRect = container.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const availableHeight = viewportHeight - containerRect.top - 100; // Account for bottom margins
    const containerHeight = Math.max(300, availableHeight); // Minimum height of 300px
    
    // Calculate the scale factor to fit the image within the container
    const scaleX = containerWidth / image.width;
    const scaleY = containerHeight / image.height;
    const scale = Math.min(scaleX, scaleY, 1); // Don't scale up, only scale down
    
    // Set canvas dimensions to scaled image size
    canvas.width = image.width * scale;
    canvas.height = image.height * scale;
    
    // Store scale factor for coordinate conversion
    canvas.dataset.scale = scale;
    
    // Apply CSS styling to ensure proper display
    canvas.style.maxWidth = '100%';
    canvas.style.maxHeight = '80vh';
    canvas.style.border = '2px solid #ddd';
    canvas.style.borderRadius = '8px';
    canvas.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    canvas.style.display = 'block';
    canvas.style.margin = '0 auto';
}

function saveEdit() {
    if (!canvas) {
        alert('Editor not initialized');
        return;
    }
    
    const dataURL = canvas.toDataURL('image/jpeg', 0.9);
    
    // Get CSRF token from meta tag if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    fetch(`/api/photos/${photoId}/annotate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(csrfToken && { 'X-CSRFToken': csrfToken })
        },
        body: JSON.stringify({
            imageData: dataURL
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Changes saved successfully!');
            // Optionally redirect back to dashboard or reload the page
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } else {
            alert('Failed to save changes: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Save error:', error);
        alert('Save error: ' + error.message);
    });
}

function resetImage() {
    // Reset all controls
    document.getElementById('brightness').value = 0;
    document.getElementById('contrast').value = 0;
    document.getElementById('saturation').value = 0;
    document.getElementById('rotation').value = 0;
    
    brightness = 0;
    contrast = 0;
    saturation = 0;
    rotation = 0;
    
    // Reload image
    const img = document.getElementById('sourceImage');
    image.src = img.src;
}

// Initialize editor when page loads
document.addEventListener('DOMContentLoaded', initEditor);
