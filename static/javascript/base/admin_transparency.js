// Global variables
let currentTransparencyId = null;
let showingDeletedTransparency = false;

// Initialize transparency list
function initializeTransparencyList() {
    // Set up event handlers
    $(document).on('click', '#addTransparencyBtn', showTransparencyForm);
    $(document).on('click', '.edit-transparency-btn', function() {
        const transparencyId = $(this).data('id');
        showTransparencyForm('edit', transparencyId);
    });
    $(document).on('click', '.delete-transparency-btn', function() {
        itemToDelete = { type: 'transparency', id: $(this).data('id') };
        openModal('deleteModal');
    });
    $(document).on('click', '.restore-transparency-btn', function() {
        const transparencyId = $(this).data('id');
        restoreTransparency(transparencyId);
    });

    // Filter handling
    $('#statusFilter, #dateFromFilter, #dateToFilter').on('change', loadTransparency);
    $('#searchFilter').on('keyup', function(e) {
        if (e.key === 'Enter') loadTransparency();
    });

    // Initial load
    loadTransparency();
}

// Load transparency list
function loadTransparency(page = 1) {
    showLoading();
    const params = {
        status: $('#statusFilter').val(),
        date_from: $('#dateFromFilter').val(),
        date_to: $('#dateToFilter').val(),
        search: $('#searchFilter').val(),
        page: page,
        show_deleted: showingDeletedTransparency
    };

    $.ajax({
        url: '/cscadmin/transparency/list/',
        method: 'GET',
        data: params,
        success: function(response) {
            renderTransparencyTable(response);
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to load transparency documents';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

// Show transparency form
function showTransparencyForm(mode = 'create', transparencyId = null) {
    showLoading();
    currentTransparencyId = transparencyId;

    $.ajax({
        url: '/cscadmin/transparency/form/',
        method: 'GET',
        success: function(html) {
            $('#transparencyModalBody').html(html);
            $('#transparencyModalTitle').text(mode === 'edit' ? 'Edit Document' : 'Add New Document');
            updateTransparencySubmitButton(mode);
            if (mode === 'edit' && transparencyId) {
                loadTransparencyData(transparencyId);
            } else {
                hideLoading();
            }
            openModal('transparencyModal');
        },
        error: function() {
            hideLoading();
            showAlert('danger', 'Failed to load transparency form');
        }
    });
}

// Load transparency data for editing
function loadTransparencyData(transparencyId) {
    showLoading();
    $.ajax({
        url: `/cscadmin/transparency/${transparencyId}/update/`,
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            if (response.success && response.transparency) {
                const doc = response.transparency;
                $('#transparencyId').val(doc.id);
                $('#transparencyTitle').val(doc.title);
                $('#transparencyContext').val(doc.context);
                $('#transparencyDescription').val(doc.description);
                $('#transparencyDate').val(doc.date);
                $('#transparencyDocumentUrl').val(doc.document_url);
                $('#transparencyStatus').val(doc.status);
                if (doc.document) {
                    $('#currentDocument').attr('href', doc.document);
                    $('#currentDocumentContainer').removeClass('hidden');
                } else {
                    $('#currentDocumentContainer').addClass('hidden');
                }
            }
            hideLoading();
        },
        error: function() {
            hideLoading();
            showAlert('danger', 'Failed to load transparency data');
        }
    });
}

// Update transparency submit button
function updateTransparencySubmitButton(mode) {
    const $btn = $('#transparencyModalSubmitBtn');
    if (mode === 'edit') {
        $('#transparencySubmitBtnIcon').removeClass('fa-plus-circle').addClass('fa-save');
        $('#transparencySubmitBtnText').text('Save Changes');
    } else {
        $('#transparencySubmitBtnIcon').removeClass('fa-save').addClass('fa-plus-circle');
        $('#transparencySubmitBtnText').text('Add Document');
    }
}

// Submit transparency form
function submitTransparencyForm() {
    showLoading();
    
    const formData = new FormData();
    formData.append('title', $('#transparencyTitle').val());
    formData.append('context', $('#transparencyContext').val());
    formData.append('description', $('#transparencyDescription').val());
    formData.append('date', $('#transparencyDate').val());
    formData.append('document_url', $('#transparencyDocumentUrl').val());
    formData.append('status', $('#transparencyStatus').val());
    
    const fileInput = $('#transparencyDocument')[0];
    if (fileInput && fileInput.files.length > 0) {
        formData.append('document', fileInput.files[0]);
    }
    
    // Determine URL based on mode
    const url = currentTransparencyId ? 
        `/cscadmin/transparency/${currentTransparencyId}/update/` : 
        '/cscadmin/transparency/create/';
    
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
                showAlert('success', response.message || 'Document saved successfully');
                closeModal('transparencyModal');
                loadTransparency();
            } else {
                showAlert('danger', response.error || 'Failed to save document');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to save document';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

// Render transparency table
function renderTransparencyTable(data) {
    let tableRows = '';
    
    if (data.transparency_list && data.transparency_list.length > 0) {
        data.transparency_list.forEach(doc => {
            const statusBadgeClass = {
                'active': 'bg-green-100 text-green-800',
                'expired': 'bg-red-100 text-red-800',
                'scheduled': 'bg-blue-100 text-blue-800'
            }[doc.status] || 'bg-gray-100 text-gray-800';
            
            const date = doc.date ? new Date(doc.date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            }) : 'Not specified';
            
            const documentLink = doc.document
                ? `<a href="${doc.document}" target="_blank" class="text-blue-600 hover:text-blue-900">
                    <i class="fas fa-file-alt mr-1"></i>View Document
                  </a>`
                : '<span class="text-gray-400">No document</span>';
            
            const description = doc.description ? 
                (doc.description.length > 100 ? doc.description.substring(0, 97) + '...' : doc.description) :
                'No description available';
            
            tableRows += `
                <tr class="${doc.is_deleted ? 'bg-gray-50' : 'hover:bg-gray-50'}">
                    <td class="px-6 py-4">
                        <div class="flex items-center">
                            <div class="ml-4">
                                <div class="text-sm font-medium ${doc.is_deleted ? 'text-gray-500' : 'text-gray-900'}">${doc.title || 'Untitled Document'}</div>
                                <div class="text-sm ${doc.is_deleted ? 'text-gray-400' : 'text-gray-500'} max-w-xl">${description}</div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4">
                        ${documentLink}
                    </td>
                    <td class="px-6 py-4">
                        <div class="text-sm ${doc.is_deleted ? 'text-gray-500' : 'text-gray-900'}">${date}</div>
                    </td>
                    <td class="px-6 py-4">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusBadgeClass}">
                            ${(doc.status || 'unknown').charAt(0).toUpperCase() + (doc.status || 'unknown').slice(1)}
                            ${doc.is_deleted ? ' (Deleted)' : ''}
                        </span>
                    </td>
                    <td class="px-6 py-4 text-right text-sm font-medium">
                        ${doc.is_deleted ? `
                            <button class="text-green-600 hover:text-green-900 restore-transparency-btn mr-3" data-id="${doc.id}">
                                <i class="fas fa-trash-restore"></i>
                            </button>
                        ` : `
                            <button class="text-blue-600 hover:text-blue-900 edit-transparency-btn mr-3" data-id="${doc.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="text-red-600 hover:text-red-900 delete-transparency-btn" data-id="${doc.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        `}
                    </td>
                </tr>
            `;
        });
    } else {
        tableRows = `
            <tr>
                <td colspan="5" class="px-6 py-12 text-center">
                    <div class="text-gray-400">
                        <i class="fas fa-file-alt fa-2x mb-2"></i>
                        <p class="text-sm">No documents found</p>
                    </div>
                </td>
            </tr>
        `;
    }
    
    $('#transparencyTableBody').html(tableRows);
    renderPagination(data);
}

// Toggle deleted transparency
function toggleDeletedTransparency() {
    showingDeletedTransparency = !showingDeletedTransparency;
    $('#showDeletedBtn').text(showingDeletedTransparency ? 'Show Active' : 'Show Deleted');
    loadTransparency();
}

// Restore transparency
function restoreTransparency(transparencyId) {
    showLoading();
    
    $.ajax({
        url: `/cscadmin/transparency/${transparencyId}/restore/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Document restored successfully');
                loadTransparency();
            } else {
                showAlert('danger', response.error || 'Failed to restore document');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to restore document';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
} 