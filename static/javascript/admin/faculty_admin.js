let currentFacultyId = null;

$(document).ready(function() {
    if (typeof initializeFacultyList === 'function') {
        initializeFacultyList();
    }
});

function initializeFacultyList() {
    // Clear filters
    $('#searchFilter').val('');
    $('#departmentFilter').val('');
    $('#positionFilter').val('');

    loadFaculty();

    // Event listeners
    $(document).on('click', '#addFacultyBtn', function() {
        openAddFacultyModal();
    });
    $(document).on('click', '.edit-faculty-btn', function() {
        const facultyId = $(this).data('id');
        editFaculty(facultyId);
    });
    $(document).on('click', '.delete-faculty-btn', function() {
        currentFacultyId = $(this).data('id');
        itemToDelete = { type: 'faculty', id: currentFacultyId };
        openModal('deleteModal');
    });
    $(document).on('click', '.restore-faculty-btn', function() {
        const facultyId = $(this).data('id');
        restoreFaculty(facultyId);
    });
    // Filters
    $(document).on('keyup', '#searchFilter', function(e) {
        if (e.key === 'Enter') {
            loadFaculty();
        }
    });
    $(document).on('change', '#departmentFilter, #positionFilter', function() {
        loadFaculty();
    });
    // Event delegation for pagination buttons
    $(document).on('click', '.pagination-btn', function() {
        const page = $(this).data('page');
        if (page && !$(this).is(':disabled')) {
            loadFaculty(page);
        }
    });
}

function loadFaculty(page = 1) {
    showLoading();
    const search = $('#searchFilter').val() || '';
    const departmentId = $('#departmentFilter').val() || '';
    const positionId = $('#positionFilter').val() || '';
    $.ajax({
        url: `/cscadmin/faculty/?search=${search}&department_id=${departmentId}&position=${positionId}`,
        method: 'GET',
        success: function(response) {
            if (response.success && Array.isArray(response.faculty)) {
                renderFacultyTable(response);
                $('#paginationContainer').empty();
                history.replaceState(null, '', window.location.pathname);
            } else {
                showAlert('danger', response.error || 'Failed to load faculty members.');
                console.error('Faculty load error:', response.error);
                $('#paginationContainer').empty();
                history.replaceState(null, '', window.location.pathname);
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred loading faculty members.';
            showAlert('danger', error);
            console.error('AJAX error:', error, xhr);
            $('#paginationContainer').empty();
            history.replaceState(null, '', window.location.pathname);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function renderFacultyTable(data) {
    let tableRows = '';
    if (data.faculty && data.faculty.length > 0) {
        data.faculty.forEach(faculty => {
            tableRows += `
                <tr class="${faculty.is_active ? 'hover:bg-gray-50' : 'bg-gray-50 text-gray-500'}">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium ${faculty.is_active ? 'text-gray-900' : 'text-gray-500'}">${escapeHtml(faculty.lastname)}, ${escapeHtml(faculty.firstname)} ${escapeHtml(faculty.middlename || '')}</td>
                    <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-500">${escapeHtml(faculty.position || 'N/A')}</td>
                    <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-500">${escapeHtml(faculty.college_name || 'N/A')} / ${escapeHtml(faculty.department_name || 'N/A')}</td>
                    <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>${escapeHtml(faculty.designation || 'N/A')}</div>
                        <div>${escapeHtml(faculty.degree || 'N/A')}</div>
                        <div>${escapeHtml(faculty.specialty || 'N/A')}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        ${faculty.is_active ? `
                            <button type="button" class="text-blue-600 hover:text-blue-900 edit-faculty-btn mr-3" data-id="${faculty.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button type="button" class="text-red-600 hover:text-red-900 delete-faculty-btn" data-id="${faculty.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : `
                            <button type="button" class="text-green-600 hover:text-green-900 restore-faculty-btn mr-3" data-id="${faculty.id}">
                                <i class="fas fa-trash-restore"></i>
                            </button>
                        `}
                    </td>
                </tr>
            `;
        });
    } else {
        tableRows = `
            <tr>
                <td colspan="5" class="px-6 py-12 text-center text-sm text-gray-500">
                    <i class="fas fa-user-times fa-2x mb-2"></i>
                    <p>No faculty members found.</p>
                </td>
            </tr>
        `;
    }
    $('#facultyTableBody').html(tableRows);
}

function openAddFacultyModal() {
    currentFacultyId = null;
    $('#facultyId').val('');
    $('#facultyModalTitle').text('Add New Faculty Member');
    loadFacultyForm('');
    openModal('facultyModal');
}

function editFaculty(facultyId) {
    showLoading();
    $.ajax({
        url: `/cscadmin/faculty/${facultyId}/`,
        method: 'GET',
        success: function(response) {
            if (response.success && response.faculty) {
                currentFacultyId = response.faculty.id;
                loadFacultyForm(response.faculty.id);
                $('#facultyModalTitle').text('Edit Faculty Member');
                openModal('facultyModal');
            } else {
                showAlert('danger', response.error || 'Failed to load faculty for editing.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred loading faculty data.';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function loadFacultyForm(facultyId) {
    showLoading();
    let url = facultyId ? `/cscadmin/faculty/${facultyId}/form/` : '/cscadmin/faculty/form/';
    $.ajax({
        url: url,
        method: 'GET',
        success: function(html) {
            $('#facultyModalBody').html(html);
            hideLoading();
            // If editing, fetch and populate data
            if (facultyId) {
                $.ajax({
                    url: `/cscadmin/faculty/${facultyId}/`,
                    method: 'GET',
                    success: function(response) {
                        if (response.success && response.faculty) {
                            $('#facultyForm [name=lastname]').val(response.faculty.lastname);
                            $('#facultyForm [name=firstname]').val(response.faculty.firstname);
                            $('#facultyForm [name=middlename]').val(response.faculty.middlename);
                            $('#facultyForm [name=position]').val(response.faculty.position);
                            $('#facultyForm [name=college]').val(response.faculty.college);
                            $('#facultyForm [name=department]').val(response.faculty.department);
                            $('#facultyForm [name=designation]').val(response.faculty.designation);
                            $('#facultyForm [name=degree]').val(response.faculty.degree);
                            $('#facultyForm [name=specialty]').val(response.faculty.specialty);
                            $('#facultyForm [name=office_location]').val(response.faculty.office_location);
                            $('#facultyForm [name=contact_number]').val(response.faculty.contact_number);
                            $('#facultyForm [name=email]').val(response.faculty.email);
                            $('#facultyForm [name=is_active]').prop('checked', response.faculty.is_active);
                        }
                    }
                });
            }
        },
        error: function() {
            hideLoading();
            showAlert('danger', 'Failed to load faculty form');
        }
    });
}

function submitFacultyForm() {
    showLoading();
    const formData = new FormData(document.getElementById('facultyForm'));
    const facultyId = $('#facultyId').val();
    let url = facultyId ? `/cscadmin/faculty/${facultyId}/update/` : '/cscadmin/faculty/create/';
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
                showAlert('success', response.message || 'Faculty member saved successfully');
                closeModal('facultyModal');
                loadFaculty();
            } else {
                showAlert('danger', response.error || 'Failed to save faculty member');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to save faculty member';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function restoreFaculty(facultyId) {
    showLoading();
    $.ajax({
        url: `/cscadmin/faculty/${facultyId}/restore/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Faculty member restored successfully');
                loadFaculty();
            } else {
                showAlert('danger', response.error || 'Failed to restore faculty member');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to restore faculty member';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function confirmDelete() {
    if (itemToDelete.type === 'faculty') {
        deleteFaculty();
    } else if (typeof window.confirmDelete === 'function') {
        window.confirmDelete();
    }
}

function deleteFaculty() {
    showLoading();
    $.ajax({
        url: `/cscadmin/faculty/${currentFacultyId}/delete/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Faculty member deleted successfully');
                closeModal('deleteModal');
                loadFaculty();
            } else {
                showAlert('danger', response.error || 'Failed to delete faculty member');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to delete faculty member';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

// Pagination rendering removed