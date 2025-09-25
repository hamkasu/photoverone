/*
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
*/

// Enhanced markup functions for PhotoVault editor

function drawRectangle(x, y, width, height, fill = false) {
    ctx.beginPath();
    ctx.rect(x, y, width, height);
    if (fill) {
        ctx.fill();
    } else {
        ctx.stroke();
    }
}

function drawCircle(x, y, radius, fill = false) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI);
    if (fill) {
        ctx.fill();
    } else {
        ctx.stroke();
    }
}

function drawArrow(fromX, fromY, toX, toY) {
    const headLength = 15;
    const angle = Math.atan2(toY - fromY, toX - fromX);
    
    // Draw line
    ctx.beginPath();
    ctx.moveTo(fromX, fromY);
    ctx.lineTo(toX, toY);
    ctx.stroke();
    
    // Draw arrowhead
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), 
               toY - headLength * Math.sin(angle - Math.PI / 6));
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), 
               toY - headLength * Math.sin(angle + Math.PI / 6));
    ctx.stroke();
}

function addText(x, y) {
    const text = document.getElementById('textInput').value;
    if (!text) return;
    
    const fontSize = document.getElementById('fontSize').value;
    const color = document.getElementById('drawColor').value;
    
    ctx.font = `${fontSize}px Arial, sans-serif`;
    ctx.fillStyle = color;
    ctx.textBaseline = 'top';
    
    // Add text background for better visibility
    const textMetrics = ctx.measureText(text);
    const textHeight = parseInt(fontSize);
    
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.fillRect(x - 2, y - 2, textMetrics.width + 4, textHeight + 4);
    
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
    
    // Clear input after adding text
    document.getElementById('textInput').value = '';
}

function updateLineWidth() {
    const value = document.getElementById('lineWidth').value;
    document.getElementById('lineWidthValue').textContent = value;
}

function updateFontSize() {
    const value = document.getElementById('fontSize').value;
    document.getElementById('fontSizeValue').textContent = value;
}

function updateDrawingStyle() {
    // This function is called when color changes
    // The actual color is applied in the draw function
}

// Add undo/redo functionality
let undoStack = [];
let redoStack = [];
const MAX_UNDO_STEPS = 20;

function saveCanvasState() {
    undoStack.push(canvas.toDataURL());
    if (undoStack.length > MAX_UNDO_STEPS) {
        undoStack.shift();
    }
    redoStack = []; // Clear redo stack when new action is performed
}

function undo() {
    if (undoStack.length > 0) {
        redoStack.push(canvas.toDataURL());
        const previousState = undoStack.pop();
        const img = new Image();
        img.onload = function() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = previousState;
    }
}

function redo() {
    if (redoStack.length > 0) {
        undoStack.push(canvas.toDataURL());
        const nextState = redoStack.pop();
        const img = new Image();
        img.onload = function() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = nextState;
    }
}

// Save canvas state before starting drawing
function saveStateBeforeDrawing() {
    if (currentTool !== 'move') {
        saveCanvasState();
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 'z':
                e.preventDefault();
                if (e.shiftKey) {
                    redo();
                } else {
                    undo();
                }
                break;
            case 'y':
                e.preventDefault();
                redo();
                break;
        }
    }
});