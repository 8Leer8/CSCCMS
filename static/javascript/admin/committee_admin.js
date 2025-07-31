let currentCommitteeId = null;
let currentMemberId = null;

$(document).ready(function() {
    // Only initialize if on the committee page
    if (currentPage === 'committee') {
        initializeCommitteePage();
    }
});

function initializeCommitteePage() {
    // Clear any existing filters on page load to ensure a clean state
    $('#searchFilter').val('');
    $('#committeeFilter').val('');

    loadCommitteeMembers();

    // Event listeners for committee members
    $(document).on('click', '#addCommitteeMemberBtn', function() { // Updated button ID
        openAddMemberModal();
    });
    $(document).on('click', '.edit-member-btn', function() {
        const memberId = $(this).data('id');
        editMember(memberId);
    });
    $(document).on('click', '.delete-member-btn', function() {
        currentMemberId = $(this).data('id');
        itemToDelete = { type: 'member', id: currentMemberId };
        openModal('deleteModal');
    });
    $(document).on('click', '.restore-member-btn', function() {
        const memberId = $(this).data('id');
        restoreMember(memberId);
    });

    // Search and filter event listeners
    $(document).on('keyup', '#searchFilter', function(e) {
        if (e.key === 'Enter') {
            loadCommitteeMembers();
        }
    });
    $(document).on('change', '#committeeFilter', function() {
        loadCommitteeMembers();
    });

    // Restrict contact number to numbers only
    $(document).on('input', '#contactNumber', function() {
        this.value = this.value.replace(/[^0-9]/g, '');
    });
}

function loadCommitteeMembers(page = 1) {
    showLoading();
    const search = $('#searchFilter').val() || '';
    const committeeId = $('#committeeFilter').val() || '';

    $.ajax({
        url: `/cscadmin/committee-members/list/?search=${search}&committee_id=${committeeId}`,
        method: 'GET',
        success: function(response) {
            if (response.success) {
                renderCommitteeMembersTable(response);
                $('#paginationContainer').empty();
            } else {
                showAlert('danger', response.error || 'Failed to load committee members.');
                $('#paginationContainer').empty();
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred loading committee members.';
            showAlert('danger', error);
            $('#paginationContainer').empty();
        },
        complete: function() {
            hideLoading();
        }
    });
}

function renderCommitteeMembersTable(data) {
    let tableRows = '';
    if (data.members && data.members.length > 0) {
        data.members.forEach(member => {
            tableRows += `
                <tr class="${member.is_active ? 'hover:bg-gray-50' : 'bg-gray-50 text-gray-500'}">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium ${member.is_active ? 'text-gray-900' : 'text-gray-500'}">${escapeHtml(member.firstname)} ${escapeHtml(member.middlename ? member.middlename + ' ' : '')}${escapeHtml(member.lastname)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${escapeHtml(member.committee_name || 'N/A')}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${escapeHtml(member.role || 'N/A')}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>${escapeHtml(member.contact_number || 'N/A')}</div>
                        <div>${escapeHtml(member.email || 'N/A')}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${member.joined_at || 'N/A'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        ${member.is_active ? `
                            <button type="button" class="text-blue-600 hover:text-blue-900 edit-member-btn mr-3" data-id="${member.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button type="button" class="text-red-600 hover:text-red-900 delete-member-btn" data-id="${member.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : `
                            <button type="button" class="text-green-600 hover:text-green-900 restore-member-btn mr-3" data-id="${member.id}">
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
                <td colspan="6" class="px-6 py-12 text-center text-sm text-gray-500">
                    <i class="fas fa-user-times fa-2x mb-2"></i>
                    <p>No committee members found.</p>
                </td>
            </tr>
        `;
    }
    $('#committeeMembersTableBody').html(tableRows);
}

function openAddMemberModal() {
    currentMemberId = null; // Clear for new member
    $('#memberId').val('');
    $('#lastName').val('');
    $('#firstName').val('');
    $('#middleName').val('');
    $('#roleSelect').val(''); // Clear the new role dropdown
    $('#contactNumber').val('');
    $('#email').val('');
    $('#joinedAt').val('');
    $('#memberModalTitle').text('Add New Committee Member');
    loadCommitteesForDropdown(''); // Load all committees and select none
    loadCommitteeRolesForDropdown(''); // Load all roles and select none
    openModal('memberModal');
}

function editMember(memberId) {
    showLoading();
    $.ajax({
        url: `/cscadmin/committees/members/${memberId}/`, // Corrected URL to fetch member details
        method: 'GET',
        success: function(response) {
            if (response.success && response.member) {
                currentMemberId = response.member.id;
                $('#memberId').val(response.member.id);
                $('#lastName').val(response.member.lastname);
                $('#firstName').val(response.member.firstname);
                $('#middleName').val(response.member.middlename);
                $('#contactNumber').val(response.member.contact_number);
                $('#email').val(response.member.email);
                $('#joinedAt').val(response.member.joined_at);
                $('#memberModalTitle').text('Edit Committee Member');
                loadCommitteesForDropdown(response.member.committee_id); // Load and pre-select committee
                loadCommitteeRolesForDropdown(response.member.role_id); // Load and pre-select role
                openModal('memberModal');
            } else {
                showAlert('danger', response.error || 'Failed to load member for editing.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred loading member data.';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function loadCommitteesForDropdown(selectedCommitteeId) {
    $.ajax({
        url: '/cscadmin/committees/all-for-dropdown/',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                let options = '<option value="">Select Committee</option>';
                response.committees.forEach(committee => {
                    options += `<option value="${committee.id}"${committee.id === selectedCommitteeId ? ' selected' : ''}>${escapeHtml(committee.name)}</option>`;
                });
                $('#committeeSelect').html(options);
            } else {
                showAlert('danger', response.error || 'Failed to load committees for dropdown.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred loading committees for dropdown.';
            showAlert('danger', error);
        }
    });
}

function loadCommitteeRolesForDropdown(selectedRoleId) {
    $.ajax({
        url: '/cscadmin/committees/roles/all-for-dropdown/',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                let options = '<option value="">Select Role</option>';
                response.roles.forEach(role => {
                    options += `<option value="${role.id}"${role.id === selectedRoleId ? ' selected' : ''}>${escapeHtml(role.name)}</option>`;
                });
                $('#roleSelect').html(options);
            } else {
                showAlert('danger', response.error || 'Failed to load roles for dropdown.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred loading roles for dropdown.';
            showAlert('danger', error);
        }
    });
}

function saveMember() {
    showLoading();
    const id = $('#memberId').val();
    const committeeId = $('#committeeSelect').val();
    const lastName = $('#lastName').val();
    const firstName = $('#firstName').val();
    const middleName = $('#middleName').val();
    const roleId = $('#roleSelect').val(); // Get selected role ID
    const contactNumber = $('#contactNumber').val();
    const email = $('#email').val();
    const joinedAt = $('#joinedAt').val();

    if (!committeeId) {
        showAlert('danger', 'Please select a committee.');
        hideLoading();
        return;
    }

    if (!roleId) {
        showAlert('danger', 'Please select a role.');
        hideLoading();
        return;
    }

    const url = id ? `/cscadmin/committees/members/${id}/update/` : '/cscadmin/committees/members/create/';
    const method = 'POST';

    $.ajax({
        url: url,
        method: method,
        data: JSON.stringify({
            committee_id: committeeId,
            lastname: lastName,
            firstname: firstName,
            middlename: middleName,
            role_id: roleId, // Send role ID to backend
            contact_number: contactNumber,
            email: email,
            joined_at: joinedAt
        }),
        contentType: 'application/json',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message);
                closeModal('memberModal');
                loadCommitteeMembers(); // Reload the main member list
            } else {
                showAlert('danger', response.error || 'Failed to save member.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred saving member.';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function deleteMember() {
    showLoading();
    $.ajax({
        url: `/cscadmin/committees/members/${itemToDelete.id}/delete/`,
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message);
                closeModal('deleteModal');
                loadCommitteeMembers(); // Reload the main member list
            } else {
                showAlert('danger', response.error || 'Failed to delete member.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred deleting member.';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function restoreMember(memberId) {
    showLoading();
    $.ajax({
        url: `/cscadmin/committees/members/${memberId}/restore/`,
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message);
                loadCommitteeMembers(); // Reload the main member list
            } else {
                showAlert('danger', response.error || 'Failed to restore member.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred restoring member.';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

// Pagination rendering removed

function openAddCommitteeModal() {
    $('#newCommitteeName').val('');
    $('#newCommitteeDescription').val('');
    openModal('addCommitteeModal');
}

function saveNewCommittee() {
    showLoading();
    const name = $('#newCommitteeName').val();
    const description = $('#newCommitteeDescription').val();

    if (!name) {
        showAlert('danger', 'Committee Name is required.');
        hideLoading();
        return;
    }

    $.ajax({
        url: '/cscadmin/committees/create/',
        method: 'POST',
        data: JSON.stringify({ name: name, description: description }),
        contentType: 'application/json',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message);
                closeModal('addCommitteeModal');
                loadCommitteesForDropdown(response.committee.id); // Refresh and select new committee
            } else {
                showAlert('danger', response.error || 'Failed to create committee.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred creating committee.';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function openAddRoleModal() {
    $('#newRoleName').val('');
    $('#newRoleDescription').val('');
    openModal('addRoleModal');
}

function saveNewRole() {
    showLoading();
    const name = $('#newRoleName').val();
    const description = $('#newRoleDescription').val();

    if (!name) {
        showAlert('danger', 'Role Name is required.');
        hideLoading();
        return;
    }

    $.ajax({
        url: '/cscadmin/committees/roles/create/', // This endpoint needs to be created
        method: 'POST',
        data: JSON.stringify({ name: name, description: description }),
        contentType: 'application/json',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message);
                closeModal('addRoleModal');
                loadCommitteeRolesForDropdown(response.role.id); // Refresh and select new role
            } else {
                showAlert('danger', response.error || 'Failed to create role.');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred creating role.';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
} 