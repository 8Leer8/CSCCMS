// Global variables for accomplishment management
let currentAccomplishmentId = null;
let showingDeletedAccomplishments = false;
let itemIdToDelete = null;
let accomplishmentIdToDelete = null;

function showAccomplishmentForm(mode = 'create', accomplishmentId = null) {
    showLoading();
    currentAccomplishmentId = accomplishmentId;
    
    $.ajax({
        url: '/cscadmin/accomplishments/form-data/',
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        success: function(response) {
            // Load the accomplishment form template
            $.ajax({
                url: '/cscadmin/?page=accomplishment_form',
                method: 'GET',
                success: function(html) {
                    $('#accomplishmentModalBody').html(html);
                    
                    // Populate select options
                    populateSelectOptions('#accomplishmentCategory', response.categories);
                    populateSelectOptions('#accomplishmentStatus', response.status_choices);
                    
                    // Set modal title
                    $('#accomplishmentModalTitle').text(mode === 'edit' ? 'Edit Accomplishment' : 'Create New Accomplishment');
                    
                    // Update submit button
                    updateAccomplishmentSubmitButton(mode);
                    
                    // Show/hide status field
                    if (mode === 'edit' && accomplishmentId) {
                        $('#accomplishmentStatusWrapper').show();
                        loadAccomplishmentData(accomplishmentId);
                    
                        // Hide status field and set status to 'active' by default
                        $('#accomplishmentStatusWrapper').hide();
                        // If status choices are available, set to 'active' if exists
                        const statusSelect = $('#accomplishmentStatus');
                        if (statusSelect.length > 0) {
                            const activeOption = statusSelect.find('option').filter(function() {
                                return $(this).text().toLowerCase() === 'active';
                            }).val();
                            if (activeOption) {
                                statusSelect.val(activeOption);
                            }
                        }
                        hideLoading();
                    }
                    
                    openModal('accomplishmentModal');
                    hideLoading();
                    
                    // Initialize image upload preview
                    $('#accomplishmentImages').on('change', function() {
                        $('#uploadedImages').empty();
                        Array.from(this.files).forEach(file => {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                $('#uploadedImages').append(`
                                    <div class="relative">
                                        <img src="${e.target.result}" class="h-32 w-full object-cover rounded">
                                        <button type="button" onclick="$(this).parent().remove()" class="absolute top-0 right-0 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center">
                                            <i class="fas fa-times text-xs"></i>
                                        </button>
                                    </div>
                                `);
                            };
                            reader.readAsDataURL(file);
                        });
                    });
                },
                error: function(xhr) {
                    hideLoading();
                    showAlert('danger', 'Failed to load accomplishment form');
                    console.error('Failed to load accomplishment form', xhr);
                }
            });
        },
        error: function(xhr) {
            hideLoading();
            showAlert('danger', 'Failed to load form data');
            console.error('Failed to load form data', xhr);
        }
    });
}

function populateSelectOptions(selector, options) {
    let html = '';
    options.forEach(option => {
        html += `<option value="${option.id}">${option.name || option.category || option.type}</option>`;
    });
    $(selector).html(html);
}

function updateAccomplishmentSubmitButton(mode) {
    const $btn = $('#accomplishmentModalSubmitBtn');
    if (mode === 'edit') {
        $('#accomplishmentSubmitBtnIcon').removeClass('fa-plus-circle').addClass('fa-save');
        $('#accomplishmentSubmitBtnText').text('Save Changes');
    } else {
        $('#accomplishmentSubmitBtnIcon').removeClass('fa-save').addClass('fa-plus-circle');
        $('#accomplishmentSubmitBtnText').text('Add Accomplishment');
    }
}

function loadAccomplishmentData(accomplishmentId) {
    showLoading();
    
    $.ajax({
        url: `/cscadmin/accomplishments/${accomplishmentId}/detail/`,
        method: 'GET',
        success: function(response) {
            if (response.success) {
                // Populate form fields
                $('#accomplishmentId').val(response.accomplishment.id);
                $('#accomplishmentTitle').val(response.accomplishment.title);
                $('#accomplishmentContext').val(response.accomplishment.context);
                $('#accomplishmentContent').val(response.accomplishment.content);
                $('#accomplishmentCategory').val(response.accomplishment.category_id);
                $('#accomplishmentStatus').val(response.accomplishment.status_id);
                $('#accomplishmentImpact').val(response.accomplishment.impact);
                $('#accomplishmentRecognition').val(response.accomplishment.recognition);
                $('#accomplishmentDate').val(response.accomplishment.accomplish_on);
                
                // Show current images if exists
                const existingImages = $('#existingImages');
                existingImages.empty();
                
                if (response.accomplishment.images && response.accomplishment.images.length > 0) {
                    response.accomplishment.images.forEach(image => {
                        existingImages.append(`
                            <div class="relative inline-block m-2">
                                <img src="${image.url}" class="h-32 w-32 object-cover rounded cursor-pointer image-preview-btn" data-src="${image.url}">
                                <button onclick="deleteAccomplishmentImage(${image.id}, ${response.accomplishment.id})" 
                                        class="absolute top-0 right-0 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center">
                                    <i class="fas fa-times text-xs"></i>
                                </button>
                            </div>
                        `);
                    });
                    existingImages.removeClass('hidden');
                }
                
                hideLoading();
            } else {
                showAlert('danger', response.error || 'Failed to load accomplishment data');
                hideLoading();
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to load accomplishment data';
            showAlert('danger', error);
            hideLoading();
        }
    });
}

function submitAccomplishmentForm() {
    showLoading();
    
    const formData = new FormData();
    formData.append('id', $('#accomplishmentId').val());
    formData.append('title', $('#accomplishmentTitle').val());
    formData.append('context', $('#accomplishmentContext').val());
    formData.append('content', $('#accomplishmentContent').val());
    formData.append('category', $('#accomplishmentCategory').val());
    formData.append('status', $('#accomplishmentStatus').val());
    formData.append('impact', $('#accomplishmentImpact').val());
    formData.append('recognition', $('#accomplishmentRecognition').val());
    formData.append('accomplish_on', $('#accomplishmentDate').val());
    
    // Append new images
    const fileInput = $('#accomplishmentImages')[0];
    if (fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('images', fileInput.files[i]);
        }
    }
    
    // Determine URL based on mode
    const url = currentAccomplishmentId ? 
        `/cscadmin/accomplishments/${currentAccomplishmentId}/update/` : 
        '/cscadmin/accomplishments/create/';
    
    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Accomplishment saved successfully');
                closeModal('accomplishmentModal');
                loadAccomplishments();
            } else {
                showAlert('danger', response.error || 'Failed to save accomplishment');
            }
        },
        error: function(xhr) {
            let error = 'Failed to save accomplishment';
            try {
                const response = JSON.parse(xhr.responseText);
                error = response.error || error;
            } catch (e) {
                error = xhr.responseText || error;
            }
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function deleteAccomplishmentImage(imageId, accomplishmentId) {
    if (!confirm('Are you sure you want to delete this image?')) return;
    
    showLoading();
    
    $.ajax({
        url: `/cscadmin/accomplishment-images/${imageId}/delete/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Image deleted successfully');
                loadAccomplishmentData(accomplishmentId); // Reload the accomplishment data to update the images list
            } else {
                showAlert('danger', response.error || 'Failed to delete image');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to delete image';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function loadAccomplishments(page = 1) {
    showLoading();
    
    const params = {
        status: $('#statusFilter').val(),
        category: $('#categoryFilter').val(),
        date_from: $('#dateFromFilter').val(),
        search: $('#searchFilter').val(),
        page: page
    };
    
    $.ajax({
        url: '/cscadmin/accomplishments/list/',
        method: 'GET',
        data: params,
        success: function(response) {
            renderAccomplishmentsTable(response);
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to load accomplishments';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function renderAccomplishmentsTable(data) {
    if (!data || !data.accomplishments || data.accomplishments.length === 0) {
        $('#accomplishmentsTableBody').html(`
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-sm text-gray-500">
                    No accomplishments found
                </td>
            </tr>
        `);
        return;
    }
    
    let tableRows = '';
    data.accomplishments.forEach(accomplishment => {
        const statusClass = accomplishment.is_active ? 
            'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
        
        const accomplishmentDate = accomplishment.accomplish_on ? 
            new Date(accomplishment.accomplish_on).toLocaleDateString() : 'N/A';
            
        const featuredImage = accomplishment.featured_image ? 
            `<img src="${accomplishment.featured_image}" class="h-10 w-10 rounded-full object-cover cursor-pointer image-preview-btn" data-src="${accomplishment.featured_image}">` : 
            '<div class="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center"><i class="fas fa-trophy text-gray-400"></i></div>';
        
        tableRows += `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            ${featuredImage}
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${escapeHtml(accomplishment.title) || 'Untitled Accomplishment'}</div>
                            <div class="text-sm text-gray-500">${accomplishment.category || 'Uncategorized'}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${accomplishmentDate}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-500">
                        ${accomplishment.impact ? accomplishment.impact.substring(0, 50) + (accomplishment.impact.length > 50 ? '...' : '') : 'N/A'}
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button class="text-yellow-600 hover:text-yellow-900 edit-accomplishment-btn mr-3" data-id="${accomplishment.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="text-red-600 hover:text-red-900 delete-accomplishment-btn" data-id="${accomplishment.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    $('#accomplishmentsTableBody').html(tableRows);
    renderAccomplishmentPagination(data);
}

function initializeAccomplishmentList() {
    // Bind filter events
    $('#statusFilter, #categoryFilter, #dateFromFilter').on('change', function() {
        loadAccomplishments();
    });
    $('#searchFilter').on('keyup', function(e) {
        if (e.key === 'Enter') loadAccomplishments();
    });
    // Bind add button
    $('#addAccomplishmentBtn').on('click', function() {
        showAccomplishmentForm('create');
    });
    // Bind edit/delete buttons (delegated)
    $(document).on('click', '.edit-accomplishment-btn', function() {
        const id = $(this).data('id');
        showAccomplishmentForm('edit', id);
    });
    $(document).on('click', '.delete-accomplishment-btn', function() {
        accomplishmentIdToDelete = $(this).data('id');
        openModal('deleteAccomplishmentModal');
    });
    // Initial load
    loadAccomplishments();
}

function renderAccomplishmentPagination(data) {
    if (!data || data.total_pages <= 1) {
        $('#paginationContainer').empty();
        return;
    }

    let paginationHtml = `
        <nav class="flex items-center justify-between">
            <div class="flex-1 flex justify-between sm:hidden">
                ${data.has_previous ? 
                    `<a href="#" onclick="loadAccomplishments(${data.previous_page_number}); return false;" class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                        Previous
                    </a>` : 
                    `<span class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-300 bg-white cursor-not-allowed">
                        Previous
                    </span>`}
                ${data.has_next ? 
                    `<a href="#" onclick="loadAccomplishments(${data.next_page_number}); return false;" class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                        Next
                    </a>` : 
                    `<span class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-300 bg-white cursor-not-allowed">
                        Next
                    </span>`}
            </div>
            <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div class="text-sm text-gray-700">
                    Showing <span class="font-medium">${(data.current_page - 1) * 10 + 1}</span> to 
                    <span class="font-medium">${Math.min(data.current_page * 10, data.total_items)}</span> of 
                    <span class="font-medium">${data.total_items}</span> results
                </div>
                <div>
                    <ul class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
    `;

    // Page numbers
    const startPage = Math.max(1, data.current_page - 2);
    const endPage = Math.min(data.total_pages, data.current_page + 2);

    for (let i = startPage; i <= endPage; i++) {
        if (i === data.current_page) {
            paginationHtml += `
                <li>
                    <span aria-current="page" class="z-10 bg-blue-50 border-blue-500 text-blue-600 relative inline-flex items-center px-4 py-2 border text-sm font-medium">
                        ${i}
                    </span>
                </li>
            `;
        } else {
            paginationHtml += `
                <li>
                    <a href="#" onclick="loadAccomplishments(${i}); return false;" class="bg-white border-gray-300 text-gray-500 hover:bg-gray-50 relative inline-flex items-center px-4 py-2 border text-sm font-medium">
                        ${i}
                    </a>
                </li>
            `;
        }
    }

    paginationHtml += `
                    </ul>
                </div>
            </div>
        </nav>
    `;

    $('#paginationContainer').html(paginationHtml);
}

$(document).on('click', '#showDeletedBtn', function() {
    showLoading();
    $.ajax({
        url: '/cscadmin/accomplishments/list/',
        method: 'GET',
        data: { status: '', category: '', date_from: '', search: '', page: 1, show_deleted: true },
        success: function(response) {
            renderDeletedAccomplishmentsModal(response.accomplishments || []);
            openModal('deletedAccomplishmentsModal');
        },
        error: function(xhr) {
            showAlert('danger', 'Failed to load deleted accomplishments');
        },
        complete: function() {
            hideLoading();
        }
    });
});

function renderDeletedAccomplishmentsModal(deletedAccomplishments) {
    let html = '';
    if (!deletedAccomplishments.length) {
        html = '<div class="text-center text-gray-500 py-8">No deleted accomplishments found.</div>';
    } else {
        html = '<table class="min-w-full divide-y divide-gray-200"><thead><tr>' +
            '<th class="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Title</th>' +
            '<th class="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Category</th>' +
            '<th class="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>' +
            '<th class="px-4 py-2 text-right text-xs font-semibold text-gray-600 uppercase">Actions</th>' +
            '</tr></thead><tbody>';
        deletedAccomplishments.forEach(acc => {
            html += `<tr>
                <td class="px-4 py-2">${escapeHtml(acc.title) || 'Untitled'}</td>
                <td class="px-4 py-2">${acc.category || 'Uncategorized'}</td>
                <td class="px-4 py-2">${acc.accomplish_on ? new Date(acc.accomplish_on).toLocaleDateString() : 'N/A'}</td>
                <td class="px-4 py-2 text-right">
                    <button class="restore-accomplishment-btn text-green-600 hover:text-green-900 font-semibold" data-id="${acc.id}"><i class="fas fa-undo"></i> Restore</button>
                </td>
            </tr>`;
        });
        html += '</tbody></table>';
    }
    $('#deletedAccomplishmentsList').html(html);
}

$(document).on('click', '.restore-accomplishment-btn', function() {
    const id = $(this).data('id');
    showLoading();
    $.ajax({
        url: `/cscadmin/accomplishments/${id}/restore/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Accomplishment restored successfully');
                closeModal('deletedAccomplishmentsModal');
                loadAccomplishments();
            } else {
                showAlert('danger', response.error || 'Failed to restore accomplishment');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to restore accomplishment';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
});

$(document).on('click', '#confirmDeleteAccomplishmentBtn', function() {
    if (!accomplishmentIdToDelete) return;
    showLoading();
    $.ajax({
        url: `/cscadmin/accomplishments/${accomplishmentIdToDelete}/delete/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Accomplishment deleted successfully');
                loadAccomplishments();
                closeModal('deleteAccomplishmentModal');
            } else {
                showAlert('danger', response.error || 'Failed to delete accomplishment');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to delete accomplishment';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
            accomplishmentIdToDelete = null;
        }
    });
}); 