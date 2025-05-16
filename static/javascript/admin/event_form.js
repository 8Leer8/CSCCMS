// Event Form JavaScript

// Function to update the file name display
function updateFileName(input) {
    const fileNameDisplay = document.getElementById('fileName');
    if (input.files.length > 0) {
        fileNameDisplay.textContent = input.files[0].name;
        fileNameDisplay.classList.remove('text-gray-500');
        fileNameDisplay.classList.add('text-gray-700', 'font-medium');
        
        // Preview the new image
        const preview = document.getElementById('currentImage');
        if (preview) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.src = e.target.result;
                document.getElementById('currentImageContainer').classList.remove('hidden');
            }
            reader.readAsDataURL(input.files[0]);
        }
    } else {
        fileNameDisplay.textContent = 'No file chosen';
        fileNameDisplay.classList.add('text-gray-500');
        fileNameDisplay.classList.remove('text-gray-700', 'font-medium');
    }
}

// Form validation and submission
const eventForm = document.getElementById('eventForm');
if (eventForm) {
    eventForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Clear previous errors
        document.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        document.querySelectorAll('.invalid-feedback').forEach(el => {
            el.classList.add('hidden');
        });

        // Validate required fields
        const requiredFields = [
            'eventName', 'eventDate',
            'eventStartTime', 'eventEndTime', 'eventLocation',
            'eventContext', 'eventDescription'
        ];
        
        let isValid = true;
        let firstErrorField = null;
        
        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field && !field.value) {
                field.classList.add('is-invalid');
                const feedback = field.nextElementSibling;
                if (feedback && feedback.classList.contains('invalid-feedback')) {
                    feedback.classList.remove('hidden');
                }
                isValid = false;
                
                if (!firstErrorField) {
                    firstErrorField = field;
                }
            }
        });
        
        // Validate time
        const startTime = document.getElementById('eventStartTime')?.value;
        const endTime = document.getElementById('eventEndTime')?.value;
        if (startTime && endTime && startTime >= endTime) {
            const endTimeField = document.getElementById('eventEndTime');
            if (endTimeField) {
                endTimeField.classList.add('is-invalid');
                const feedback = endTimeField.nextElementSibling;
                if (feedback && feedback.classList.contains('invalid-feedback')) {
                    feedback.textContent = 'End time must be after start time';
                    feedback.classList.remove('hidden');
                }
                isValid = false;
                
                if (!firstErrorField) {
                    firstErrorField = endTimeField;
                }
            }
        }
        
        if (!isValid) {
            // Scroll to first error field
            if (firstErrorField) {
                firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstErrorField.focus();
            }
            return;
        }
        
        // Submit the form
        submitEventForm();
    });
}

// Function to close modal
function closeModal() {
  const modal = document.getElementById('eventModal');
  if (modal) {
    modal.classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
  }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function handleFormErrors(data) {
    if (data.errors) {
        Object.entries(data.errors).forEach(([field, errors]) => {
            const fieldElement = document.getElementById(field);
            if (fieldElement) {
                fieldElement.classList.add('is-invalid');
                const feedback = fieldElement.nextElementSibling;
                if (feedback && feedback.classList.contains('invalid-feedback')) {
                    feedback.textContent = Array.isArray(errors) ? errors.join(', ') : errors;
                    feedback.classList.remove('hidden');
                }
            }
        });
        
        const firstError = document.querySelector('.is-invalid');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
    }
    showAlert && showAlert('danger', data.message || data.error || 'Failed to save event');
}

// Helper function to show alerts
function showAlert(type, message) {
    const messagesContainer = document.getElementById('messages-container');
    if (!messagesContainer) {
        console.error('Messages container not found');
        return;
    }
    
    const alertHtml = `
        <div class="border-l-4 ${type === 'success' ? 'bg-green-100 border-green-400 text-green-700' : 'bg-red-100 border-red-400 text-red-700'} p-4 mb-4 rounded">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    ${type === 'success' ? '<svg class="h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>' : '<svg class="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>'}
                </div>
                <div class="ml-3">
                    <p class="text-sm">${message}</p>
                </div>
                <div class="ml-auto pl-3">
                    <button type="button" class="text-gray-500 hover:text-gray-700" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
                    </button>
                </div>
            </div>
        </div>
    `;
    messagesContainer.innerHTML = alertHtml;
}

// Modal open logic (example)
// When Add Event button is clicked, load the form from the correct view
$("#addEventBtn").on("click", function() {
     $.get('/cscadmin/events/event_form/', function(html) {
         $('#eventModalBody').html(html);
     });
 }); 