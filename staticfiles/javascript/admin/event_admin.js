// Event Admin JavaScript (combined)

// Utility functions
function showAlert(type, message) {
    const alertTypes = {
        'success': 'bg-green-100 border-green-400 text-green-700',
        'danger': 'bg-red-100 border-red-400 text-red-700',
        'warning': 'bg-yellow-100 border-yellow-400 text-yellow-700',
        'info': 'bg-blue-100 border-blue-400 text-blue-700'
    };
    const alertHtml = `
        <div class="border-l-4 ${alertTypes[type]} p-4 mb-4 rounded">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    ${type === 'success' ? '<i class="fas fa-check-circle text-green-500"></i>' : ''}
                    ${type === 'danger' ? '<i class="fas fa-exclamation-circle text-red-500"></i>' : ''}
                    ${type === 'warning' ? '<i class="fas fa-exclamation-triangle text-yellow-500"></i>' : ''}
                    ${type === 'info' ? '<i class="fas fa-info-circle text-blue-500"></i>' : ''}
                </div>
                <div class="ml-3">
                    <p class="text-sm">${message}</p>
                </div>
                <div class="ml-auto pl-3">
                    <button type="button" class="text-gray-500 hover:text-gray-700" onclick="$(this).parent().parent().parent().remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    $('#messages-container').html(alertHtml);
    setTimeout(() => {
        $('#messages-container').empty();
    }, 5000);
}
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
function closeModal() {
    const modal = document.getElementById('eventModal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }
}

// File name update and image preview
function updateFileName(input) {
    const fileNameDisplay = document.getElementById('fileName');
    if (input.files.length > 0) {
        fileNameDisplay.textContent = input.files[0].name;
        fileNameDisplay.classList.remove('text-gray-500');
        fileNameDisplay.classList.add('text-gray-700', 'font-medium');
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

// Modal open logic
$(document).on('click', '#addEventBtn', function() {
    showEventForm('create');
});
$(document).on('click', '.edit-event-btn', function() {
    const eventId = $(this).data('id');
    showEventForm('edit', eventId);
});

function showEventForm(mode = 'create', eventId = null) {
    showLoading();
    $.ajax({
        url: '/cscadmin/events/event_form',
        method: 'GET',
        success: function(html) {
            $('#eventModalBody').html(html);
            $('#eventModalTitle').text(mode === 'edit' ? 'Edit Event' : 'Create New Event');
            updateEventSubmitButton(mode);
            if (mode === 'edit' && eventId) {
                loadEventData(eventId);
            } else {
                hideLoading();
            }
            openModal('eventModal');
        },
        error: function() {
            hideLoading();
            showAlert('danger', 'Failed to load event form');
        }
    });
}
function openModal(modalId) {
    $('#' + modalId).removeClass('hidden');
}
function updateEventSubmitButton(mode) {
    const $btn = $('#eventModalSubmitBtn');
    if (mode === 'edit') {
        $('#eventSubmitBtnIcon').removeClass('fa-plus-circle').addClass('fa-save');
        $('#eventSubmitBtnText').text('Save Changes');
    } else {
        $('#eventSubmitBtnIcon').removeClass('fa-save').addClass('fa-plus-circle');
        $('#eventSubmitBtnText').text('Add Event');
    }
}

// Load event data for editing
function loadEventData(eventId) {
    showLoading();
    $.ajax({
        url: `/cscadmin/events/${eventId}/update/`,
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            if (response.success && response.event) {
                $('#eventId').val(response.event.id);
                $('#eventName').val(response.event.name);
                $('#eventDate').val(response.event.date_event);
                $('#eventStartTime').val(response.event.start_at);
                $('#eventEndTime').val(response.event.end_at);
                $('#eventLocation').val(response.event.location);
                $('#eventLandmark').val(response.event.landmark);
                $('#eventPublishStart').val(response.event.start_publish_on);
                $('#eventPublishEnd').val(response.event.end_publish_on);
                $('#eventContext').val(response.event.context);
                $('#eventDescription').val(response.event.description);
                if (Array.isArray(response.event.labels)) {
                    response.event.labels.forEach(function(id) {
                        $(`input[name="eventLabels"][value="${id}"]`).prop('checked', true);
                    });
                }
                if (Array.isArray(response.event.types)) {
                    response.event.types.forEach(function(id) {
                        $(`input[name="eventTypes"][value="${id}"]`).prop('checked', true);
                    });
                }
                if (Array.isArray(response.event.audiences)) {
                    response.event.audiences.forEach(function(id) {
                        $(`input[name="eventAudiences"][value="${id}"]`).prop('checked', true);
                    });
                }
                if (response.event.event_img) {
                    $('#currentImage').attr('src', response.event.event_img);
                    $('#currentImageContainer').removeClass('hidden');
                    $('#fileName').text('Current image');
                } else {
                    $('#currentImageContainer').addClass('hidden');
                    $('#fileName').text('No file chosen');
                }
            }
            hideLoading();
        },
        error: function() {
            hideLoading();
            showAlert('danger', 'Failed to load event data');
        }
    });
}

// Form validation and submission
$(document).on('submit', '#eventForm', function(e) {
    e.preventDefault();
    // Clear previous errors
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').addClass('hidden');
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
        if (firstErrorField) {
            firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstErrorField.focus();
        }
        return;
    }
    submitEventForm();
});

// Form submission handler
function submitEventForm() {
    const form = document.getElementById('eventForm');
    if (!form) {
        console.error('Form not found');
        return;
    }
    const formData = new FormData(form);
    const eventId = document.getElementById('eventId')?.value;
    const isEdit = !!eventId;
    const url = isEdit ? `/cscadmin/events/${eventId}/update/` : '/cscadmin/events/create/';

    // Collect checked values for checkboxes
    const selectedLabels = Array.from(document.querySelectorAll('input[name="eventLabels"]:checked')).map(cb => cb.value);
    const selectedTypes = Array.from(document.querySelectorAll('input[name="eventTypes"]:checked')).map(cb => cb.value);
    const selectedAudiences = Array.from(document.querySelectorAll('input[name="eventAudiences"]:checked')).map(cb => cb.value);

    // Remove any existing category data
    formData.delete('eventLabels');
    formData.delete('eventTypes');
    formData.delete('eventAudiences');

    // Add the selected categories
    selectedLabels.forEach(value => formData.append('eventLabels', value));
    selectedTypes.forEach(value => formData.append('eventTypes', value));
    selectedAudiences.forEach(value => formData.append('eventAudiences', value));

    showLoading();
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            closeModal();
            showAlert('success', data.message || (isEdit ? 'Event updated successfully!' : 'Event created successfully!'));
            if (!isEdit) {
                form.reset();
                document.getElementById('fileName').textContent = 'No file chosen';
                document.getElementById('currentImageContainer').classList.add('hidden');
            }
            if (typeof loadEvents === 'function') {
                loadEvents();
            }
        } else {
            handleFormErrors(data);
        }
    })
    .catch(error => {
        console.error('Error saving event:', error);
        showAlert('danger', error.message || 'An error occurred while saving the event');
    })
    .finally(() => {
        hideLoading();
    });
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
    showAlert('danger', data.message || data.error || 'Failed to save event');
} 