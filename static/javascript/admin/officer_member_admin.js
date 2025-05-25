// Officer Member CRUD JS
$(document).ready(function() {
    initializeOfficerMemberPage();
});

function initializeOfficerMemberPage() {
    // Load officer members on page load
    loadOfficerMembers();

    // Open modal on add button
    $(document).off('click', '#addOfficerMemberBtn').on('click', '#addOfficerMemberBtn', function() {
        clearOfficerMemberForm();
        $('#officerMemberModalTitle').text('Add Officer Member');
        $('#officerMemberModal').removeClass('hidden');
        loadOfficerMemberFormOptions();
        $('#officerMemberStatusWrapper').addClass('hidden');
    });

    // Save officer member
    $(document).off('click', '#saveOfficerMemberBtn').on('click', '#saveOfficerMemberBtn', function() {
        saveOfficerMember();
    });

    // Close modal
    window.closeModal = function(modalId) {
        $('#' + modalId).addClass('hidden');
    };

    // Edit officer member
    $(document).off('click', '.edit-officer-member-btn').on('click', '.edit-officer-member-btn', function() {
        const id = $(this).data('id');
        $.get(`/cscadmin/officer_members/${id}/detail/`, function(response) {
            if (response.success) {
                const m = response.member;
                $('#officerMemberId').val(m.id);
                $('#officerMemberName').val(m.name);
                $('#officerMemberStartTerm').val(m.start_term);
                $('#officerMemberEndTerm').val(m.end_term);
                $('#officerMemberBio').val(m.bio || '');
                $('#officerMemberStatus').val(m.status);
                $('#officerMemberModalTitle').text('Edit Officer Member');
                $('#officerMemberModal').removeClass('hidden');
                loadOfficerMemberFormOptions(function() {
                    $('#officerMemberPosition').val(m.position_id);
                    $('#officerMemberDepartment').val(m.department_id);
                });
                $('#officerMemberStatusWrapper').removeClass('hidden');

                // Show existing image preview if available
                if (m.profile_img) {
                    const previewHtml = `
                        <div class="mt-2">
                            <img src="${m.profile_img}" alt="Current profile image" class="h-32 w-32 object-cover rounded-lg border border-gray-200">
                        </div>
                    `;
                    $('#officerMemberProfileImg').after(previewHtml);
                }
            } else {
                showAlert('danger', response.error || 'Failed to load officer member');
            }
        });
    });

    // Delete officer member
    $(document).off('click', '.delete-officer-member-btn').on('click', '.delete-officer-member-btn', function() {
        const id = $(this).data('id');
        if (confirm('Are you sure you want to deactivate this officer member?')) {
            $.post(`/cscadmin/officer_members/${id}/delete/`, function(response) {
                if (response.success) {
                    showAlert('success', response.message || 'Officer member deactivated');
                    loadOfficerMembers();
                } else {
                    showAlert('danger', response.error || 'Failed to deactivate officer member');
                }
            });
        }
    });

    // Populate department and term filters on page load
    populateOfficerMemberDepartmentFilter();
    populateOfficerMemberTermFilter();

    // Filter logic
    $('#officerMemberDepartmentFilter, #officerMemberTermFilter').off('change').on('change', function() {
        loadOfficerMembers();
    });
    $('#officerMemberSearchFilter').off('keyup').on('keyup', function(e) {
        if (e.key === 'Enter') loadOfficerMembers();
    });
}

function populateOfficerMemberDepartmentFilter() {
    $.get('/cscadmin/officer_members/form-data/', function(response) {
        if (response.success) {
            let html = '<option value="">All Departments</option>';
            response.departments.forEach(function(dept) {
                html += `<option value="${dept.id}">${escapeHtml(dept.name)}</option>`;
            });
            $('#officerMemberDepartmentFilter').html(html);
        }
    });
}

function populateOfficerMemberTermFilter() {
    // Fetch unique start_term and end_term years from the backend
    $.get('/cscadmin/officer_members/list/', { fetch_terms: 1 }, function(response) {
        let html = '<option value="">All Terms</option>';
        if (response.success && response.terms) {
            response.terms.forEach(function(term) {
                html += `<option value="${term}">${term.replace('-', ' - ')}</option>`;
            });
        }
        $('#officerMemberTermFilter').html(html);
    });
}

function loadOfficerMembers(page = 1) {
    let params = {};
    const dept = $('#officerMemberDepartmentFilter').val();
    const term = $('#officerMemberTermFilter').val();
    const search = $('#officerMemberSearchFilter').val();
    if (dept) params.department = dept;
    if (term) params.term = term;
    if (search) params.search = search;
    params.page = page;
    $.get('/cscadmin/officer_members/list/', params, function(response) {
        if (response.success) {
            // Set results count text for this page
            const start = (response.current_page - 1) * 10 + 1;
            const end = start + response.officer_members.length - 1;
            window.officerMembersResultsCountText = `Showing ${start} to ${end} of ${((response.total_count !== undefined) ? response.total_count : (response.total_pages * 10))} results`;
            renderOfficerMembersTable(response.officer_members);
            renderOfficerMembersPagination(response.current_page, response.total_pages, response.has_previous, response.has_next);
        } else {
            showAlert('danger', response.error || 'Failed to load officer members');
        }
    });
}

function renderOfficerMembersTable(data) {
    let html = '';
    if (data.length === 0) {
        html = `<tr><td colspan="6" class="px-6 py-12 text-center text-gray-400">No officer members found</td></tr>`;
    } else {
        data.forEach(function(member) {
            let imgHtml = member.profile_img ?
                `<img src="${escapeHtml(member.profile_img)}" alt="${escapeHtml(member.name)}" class="h-12 w-12 rounded-full object-cover border border-gray-200">` :
                `<div class="h-12 w-12 rounded-full bg-gray-200 flex items-center justify-center text-gray-400"><i class="fas fa-user"></i></div>`;
            let bio = member.bio ? (member.bio.length > 80 ? member.bio.substring(0, 77) + '...' : member.bio) : '';
            html += `<tr>
                <td class="px-6 py-4">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">${imgHtml}</div>
                        <div class="ml-4">
                            <div class="text-sm font-bold text-gray-900">${escapeHtml(member.name)}</div>
                            <div class="text-xs text-gray-500 max-w-xs truncate">${escapeHtml(bio)}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4">${escapeHtml(member.position)}</td>
                <td class="px-6 py-4">${escapeHtml(member.department)}</td>
                <td class="px-6 py-4">${escapeHtml(member.start_term)} - ${escapeHtml(member.end_term)}</td>
                <td class="px-6 py-4">${escapeHtml(member.status)}</td>
                <td class="px-6 py-4 text-right">
                    <button class="text-blue-600 hover:text-blue-900 edit-officer-member-btn mr-3" data-id="${member.id}"><i class="fas fa-edit"></i></button>
                    <button class="text-red-600 hover:text-red-900 delete-officer-member-btn" data-id="${member.id}"><i class="fas fa-trash"></i></button>
                </td>
            </tr>`;
        });
    }
    $('#officerMembersTableBody').html(html);
    // Set results count if available
    if (window.officerMembersResultsCountText) {
        $('#officerMembersResultsCount').text(window.officerMembersResultsCountText);
    }
}

function renderOfficerMembersPagination(currentPage, totalPages, hasPrevious, hasNext) {
    const container = $('#paginationContainer');
    container.empty();
    if (totalPages <= 1) return;
    let html = '<div class="flex w-full items-center">';
    // Results count left-aligned
    html += '<div id="officerMembersResultsCount" class="text-sm text-gray-600"></div>';
    // Pagination bar right-aligned
    html += '<nav class="inline-flex -space-x-px rounded-md shadow-sm border border-gray-300 bg-white">';
    // Previous button
    html += `<button class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${hasPrevious ? 'text-gray-500 hover:bg-gray-50' : 'text-gray-300 cursor-not-allowed'}" ${hasPrevious ? '' : 'disabled'} data-page="${currentPage - 1}"><span class="sr-only">Previous</span><i class="fas fa-chevron-left"></i></button>`;
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium ${i === currentPage ? 'z-10 bg-blue-50 border-blue-500 text-blue-600' : 'bg-white text-gray-500 hover:bg-gray-50'}" data-page="${i}">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<span class="px-2 text-gray-500">...</span>';
        }
    }
    // Next button
    html += `<button class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${hasNext ? 'text-gray-500 hover:bg-gray-50' : 'text-gray-300 cursor-not-allowed'}" ${hasNext ? '' : 'disabled'} data-page="${currentPage + 1}"><span class="sr-only">Next</span><i class="fas fa-chevron-right"></i></button>`;
    html += '</nav>';
    html += '</div>';
    container.html(html);
}

// Handle pagination button clicks
$(document).off('click', '#paginationContainer [data-page]').on('click', '#paginationContainer [data-page]', function() {
    const page = parseInt($(this).attr('data-page'));
    if (!isNaN(page)) {
        loadOfficerMembers(page);
    }
});

function clearOfficerMemberForm() {
    $('#officerMemberId').val('');
    $('#officerMemberName').val('');
    $('#officerMemberPosition').val('');
    $('#officerMemberDepartment').val('');
    $('#officerMemberStartTerm').val('');
    $('#officerMemberEndTerm').val('');
    $('#officerMemberBio').val('');
    $('#officerMemberProfileImg').val('');
    $('#officerMemberStatus').val('active');
    // Remove any existing image preview
    $('#officerMemberProfileImg').next('.mt-2').remove();
}

function loadOfficerMemberFormOptions(callback) {
    $.get('/cscadmin/officer_members/form-data/', function(response) {
        if (response.success) {
            let posHtml = '<option value="">Select Position</option>';
            response.positions.forEach(function(pos) {
                posHtml += `<option value="${pos.id}">${escapeHtml(pos.name)}</option>`;
            });
            $('#officerMemberPosition').html(posHtml);
            let deptHtml = '<option value="">Select Department</option>';
            response.departments.forEach(function(dept) {
                deptHtml += `<option value="${dept.id}">${escapeHtml(dept.name)}</option>`;
            });
            $('#officerMemberDepartment').html(deptHtml);
            if (typeof callback === 'function') callback();
        }
    });
}

function saveOfficerMember() {
    var formData = new FormData();
    formData.append('name', $('#officerMemberName').val());
    formData.append('position', $('#officerMemberPosition').val());
    formData.append('department', $('#officerMemberDepartment').val());
    formData.append('start_term', $('#officerMemberStartTerm').val());
    formData.append('end_term', $('#officerMemberEndTerm').val());
    formData.append('bio', $('#officerMemberBio').val());
    var fileInput = $('#officerMemberProfileImg')[0];
    if (fileInput.files.length > 0) {
        formData.append('profile_img', fileInput.files[0]);
    }
    var id = $('#officerMemberId').val();
    var url, method;
    if (id) {
        url = `/cscadmin/officer_members/${id}/update/`;
        method = 'POST';
        formData.append('status', $('#officerMemberStatus').val());
    } else {
        url = '/cscadmin/officer_members/create/';
        method = 'POST';
    }
    $.ajax({
        url: url,
        type: method,
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Officer member saved');
                closeModal('officerMemberModal');
                loadOfficerMembers();
            } else {
                showAlert('danger', response.error || 'Failed to save officer member');
            }
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return text.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showAlert(type, message) {
    // Use the admin base showAlert if available
    if (typeof window.showAlert === 'function') {
        window.showAlert(type, message);
    } else {
        alert(message);
    }
} 