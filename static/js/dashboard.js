/*
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
*/

// photovault/static/js/dashboard.js
// Dashboard functionality
let stream = null;

async function uploadFiles(files) {
    if (!files || files.length === 0) {
        console.warn('No files provided to uploadFiles function.');
        // Optionally, show a user-friendly message
        const progressElement = document.getElementById('uploadProgress');
        if (progressElement) {
             progressElement.style.display = 'block';
             progressElement.textContent = 'No files selected.';
             progressElement.className = 'alert alert-warning';
             setTimeout(() => { progressElement.style.display = 'none'; }, 3000);
        }
        return; // Exit early if no files
    }

    const formData = new FormData();

    for (let file of files) {
        formData.append('files[]', file);
    }

    const progressElement = document.getElementById('uploadProgress');
    if (progressElement) {
        progressElement.style.display = 'block';
        progressElement.textContent = 'Uploading photos...';
        progressElement.className = 'alert alert-info'; // Reset class
    }

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (data.success) {
            console.log('Upload successful:', data.files);
            // Provide feedback before reload
            if (progressElement) {
                 let successMessage = 'Upload successful!';
                 if (data.message) {
                     successMessage = data.message; // Use server message if provided
                 }
                 progressElement.className = 'alert alert-success';
                 progressElement.textContent = successMessage;
                 // Reload to show new photos after a short delay
                 setTimeout(() => {
                     location.reload();
                 }, 1500);
            } else {
                 location.reload(); // Fallback reload
            }
        } else {
            // Handle explicit failure from server
            console.error('Upload failed:', data);
            let errorMessage = 'Upload failed.';
            if (data.message) {
                errorMessage = data.message;
            }
            if (data.errors && data.errors.length > 0) {
                errorMessage += ' Errors: ' + data.errors.join('; ');
            }
            if (progressElement) {
                 progressElement.className = 'alert alert-danger';
                 progressElement.textContent = errorMessage;
                 // Keep error visible longer or until user interacts
                 // setTimeout(() => { progressElement.style.display = 'none'; }, 5000);
            } else {
                 alert(errorMessage); // Fallback if no progress element
            }
            // Do not reload on failure
        }
    } catch (error) {
        // Handle network errors or unexpected JS errors
        console.error('Upload error:', error);
        const errorMessage = 'Upload error: ' + (error.message || 'Network or unexpected error occurred.');
        if (progressElement) {
             progressElement.className = 'alert alert-danger';
             progressElement.textContent = errorMessage;
        } else {
             alert(errorMessage); // Fallback
        }
        // Do not reload on error
    } finally {
        // Ensure progress is hidden if it was a simple success that triggered reload
        // The timeout in the success block handles this.
        // If hiding is needed for other cases, add logic here.
    }
}

async function deletePhoto(photoId) {
    if (!confirm('Are you sure you want to delete this photo?')) {
        return;
    }

    try {
        const response = await fetch(`/api/delete/${photoId}`, {
            method: 'DELETE',
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Remove the photo element from the DOM
            const photoElement = document.getElementById(`photo-${photoId}`);
            if (photoElement) {
                photoElement.remove();
                // Optional: Show a brief confirmation message
                // e.g., using a toast or updating a status area
            }
        } else {
            const errorMsg = data.error || data.message || 'Unknown error';
            alert('Failed to delete photo: ' + errorMsg);
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('Delete error: ' + (error.message || 'Network error'));
    }
}

async function startCamera() {
    const modalElement = document.getElementById('cameraModal');
    if (!modalElement) {
        console.warn('Camera modal not found - feature not available on this page');
        return;
    }
    
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap not loaded');
        return;
    }
    
    const modal = new bootstrap.Modal(modalElement);
    const video = document.getElementById('video');

    if (!video) {
        alert('Video element not found.');
        return;
    }

    try {
        // Stop any existing stream first
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        modal.show();
    } catch (error) {
        console.error('Camera access error:', error);
        alert('Could not access camera: ' + (error.message || 'Permission denied or device not found.'));
    }
}

function capturePhoto() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const modalElement = document.getElementById('cameraModal');

    if (!video || !canvas || !modalElement) {
         alert('Required elements for capture not found.');
         return;
    }

    const context = canvas.getContext('2d');

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    if (canvas.width === 0 || canvas.height === 0) {
         alert('Could not determine video dimensions.');
         return;
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
        if (!blob) {
             alert('Failed to capture photo.');
             return;
        }
        const file = new File([blob], 'captured_photo.jpg', { type: 'image/jpeg' });
        uploadFiles([file]); // Upload the captured photo

        // Close modal and stop stream
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null; // Clear reference
        }
    }, 'image/jpeg');
}

// Optional: Add event listener for file input change if not handled inline
// document.addEventListener('DOMContentLoaded', function() {
//     const fileInput = document.getElementById('fileInput');
//     if (fileInput) {
//         fileInput.addEventListener('change', function(e) {
//             if (e.target.files.length > 0) {
//                 uploadFiles(e.target.files);
//                 // Clear the input to allow selecting the same file again later
//                 e.target.value = '';
//             }
//         });
//     }
// });
