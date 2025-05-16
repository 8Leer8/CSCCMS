let accountIdToDelete = null;

function initializeAccountList() {
    // Remove status filter logic
    $('#accountSearchFilter').on('keyup', function(e) {
        if (e.key === 'Enter') loadAccountList();
    });
    $('#addAccountBtn').on('click', function() {
        showAccountForm('create');
    });
    $('#showInactiveAccountsBtn').on('click', function() {
        showInactiveAccountsModal();
    });
    // Initial load
    loadAccountList();
}

function loadAccountList() {
    const search = $('#accountSearchFilter').val();
    $.ajax({
        url: '/cscadmin/accounts/list/',
        method: 'GET',
        data: {
            is_active: 'true',
            search: search,
            account_type: 'user'
        },
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        beforeSend: function() {
            $('#accountsTableBody').html('<tr><td colspan="5" class="text-center py-6"><div class="loader"></div></td></tr>');
        },
        success: function(response) {
            if (response.success) {
                renderAccountList(response.accounts);
                renderAccountPagination(response);
            } else {
                $('#accountsTableBody').html('<tr><td colspan="5" class="text-center text-red-500">Failed to load accounts.</td></tr>');
            }
        },
        error: function() {
            $('#accountsTableBody').html('<tr><td colspan="5" class="text-center text-red-500">Error loading accounts.</td></tr>');
        }
    });
}

function renderAccountList(accounts) {
    const tbody = $('#accountsTableBody');
    tbody.empty();
    if (!accounts || accounts.length === 0) {
        tbody.append('<tr><td colspan="5" class="text-center text-gray-500 py-8">No accounts found.</td></tr>');
        return;
    }
    accounts.forEach(account => {
        tbody.append(`
            <tr class="hover:bg-gray-50 transition">
                <td class="px-6 py-4 whitespace-nowrap flex items-center gap-3">
                    <div class="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
                        ${account.profile_img ? `<img src="${account.profile_img}" alt="Profile" class="h-10 w-10 rounded-full object-cover">` : `<i class='fas fa-user text-gray-400 text-xl'></i>`}
                    </div>
                    <div>
                        <div class="font-semibold text-gray-900">${account.firstname} ${account.lastname}</div>
                        <div class="text-xs text-gray-400">${account.email}</div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${account.contact_number || ''}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-xs text-gray-500">${account.created_at || ''}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-xs text-gray-500">${account.last_login || ''}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right">
                    <button class="inline-flex items-center px-2 py-1 text-blue-600 hover:text-blue-800" title="Edit" onclick="showAccountForm('edit', ${account.id})"><i class="fas fa-edit"></i></button>
                    <button class="inline-flex items-center px-2 py-1 text-red-600 hover:text-red-800" title="Delete" onclick="deleteAccount(${account.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `);
    });
}

function renderAccountPagination(data) {
    // Implement pagination rendering if needed
    // Example: $('#paginationContainer').html(...)
}

function showAccountForm(mode, id = null) {
    showLoading();
    // Load the form HTML using the admin_dashboard endpoint
    $.ajax({
        url: '/cscadmin/?page=account_form',
        method: 'GET',
        dataType: 'html',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        success: function(html) {
            $('#accountModalBody').html(html);
            $('#accountModalTitle').text(mode === 'edit' ? 'Edit Account' : 'Add New Account');
            $('#accountSubmitBtnText').text(mode === 'edit' ? 'Save Changes' : 'Add Account');
            if (mode === 'edit' && id) {
                $('#accountStatusWrapper').show();
                // Fetch account data
                $.ajax({
                    url: `/cscadmin/accounts/${id}/detail/`,
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    success: function(response) {
                        if (response.success && response.account) {
                            $('#accountId').val(response.account.id);
                            $('#accountEmail').val(response.account.email);
                            $('#accountFirstname').val(response.account.firstname);
                            $('#accountLastname').val(response.account.lastname);
                            $('#accountMiddlename').val(response.account.middlename);
                            $('#accountContact').val(response.account.contact_number);
                            $('#accountType').val(response.account.account_type);
                            $('#accountStatus').val(response.account.is_active ? 'true' : 'false');
                            // Show password as plain text in edit mode
                            $('#accountPassword').attr('type', 'text');
                            $('#accountPassword').val(response.account.password || '');
                            $('#passwordFieldContainer').show();
                        }
                        hideLoading();
                        openModal('accountModal');
                    },
                    error: function() {
                        hideLoading();
                        showAlert('danger', 'Failed to load account data.');
                    }
                });
            } else {
                // Show password field for add, hide status
                $('#passwordFieldContainer').show();
                $('#accountStatusWrapper').hide();
                $('#accountPassword').val('');
                $('#accountPassword').attr('type', 'password');
                hideLoading();
                openModal('accountModal');
            }
        },
        error: function() {
            hideLoading();
            showAlert('danger', 'Failed to load account form.');
        }
    });
}

function deleteAccount(id) {
    accountIdToDelete = id;
    openModal('deleteAccountModal');
}

$(document).on('click', '#confirmDeleteAccountBtn', function() {
    if (!accountIdToDelete) return;
    showLoading();
    $.ajax({
        url: `/cscadmin/accounts/${accountIdToDelete}/delete/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Account deactivated successfully');
                loadAccountList();
                closeModal('deleteAccountModal');
            } else {
                showAlert('danger', response.error || 'Failed to deactivate account');
            }
        },
        error: function(xhr) {
            let error = 'Failed to deactivate account';
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
            accountIdToDelete = null;
        }
    });
});

function submitAccountForm() {
    showLoading();

    const id = $('#accountId').val();
    const isEdit = !!id;
    const url = isEdit
        ? `/cscadmin/accounts/${id}/update/`
        : '/cscadmin/accounts/create/';
    const method = 'POST';

    const formData = new FormData();
    formData.append('email', $('#accountEmail').val());
    formData.append('firstname', $('#accountFirstname').val());
    formData.append('lastname', $('#accountLastname').val());
    formData.append('middlename', $('#accountMiddlename').val());
    formData.append('contact_number', $('#accountContact').val());
    formData.append('account_type', $('#accountType').val());
    if (!isEdit) {
        formData.append('is_active', 'true');
    } else {
        formData.append('is_active', $('#accountStatus').val());
    }
    // Only send password if not blank
    const password = $('#accountPassword').val();
    if (password) {
        formData.append('password', password);
    }
    // Profile image
    const fileInput = $('#accountProfileImg')[0];
    if (fileInput && fileInput.files.length > 0) {
        formData.append('profile_img', fileInput.files[0]);
    }

    $.ajax({
        url: url,
        type: method,
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Account saved successfully');
                closeModal('accountModal');
                loadAccountList();
            } else {
                showAlert('danger', response.error || 'Failed to save account');
            }
        },
        error: function(xhr) {
            let error = 'Failed to save account';
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

function showInactiveAccountsModal() {
    // Fetch inactive accounts (users only)
    $.ajax({
        url: '/cscadmin/accounts/list/',
        method: 'GET',
        data: {
            is_active: 'false',
            search: '',
            account_type: 'user'
        },
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        beforeSend: function() {
            $('#inactiveAccountsModalBody').html('<div class="text-center py-8"><div class="loader"></div></div>');
        },
        success: function(response) {
            if (response.success) {
                renderInactiveAccounts(response.accounts);
            } else {
                $('#inactiveAccountsModalBody').html('<div class="text-center text-red-500">Failed to load inactive accounts.</div>');
            }
        },
        error: function() {
            $('#inactiveAccountsModalBody').html('<div class="text-center text-red-500">Error loading inactive accounts.</div>');
        }
    });
    openModal('inactiveAccountsModal');
}

function renderInactiveAccounts(accounts) {
    if (!accounts || accounts.length === 0) {
        $('#inactiveAccountsModalBody').html('<div class="text-center text-gray-500 py-8">No inactive accounts found.</div>');
        return;
    }
    let html = `<table class=\"w-full divide-y divide-gray-200\">
            <thead class=\"bg-gray-100\">
                <tr>
                    <th class=\"px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider\">Account</th>
                    <th class=\"px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider\">Contact</th>
                    <th class=\"px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider\">Created</th>
                    <th class=\"px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider\">Last Login</th>
                    <th class=\"px-6 py-3 text-right text-xs font-bold text-gray-700 uppercase tracking-wider\">Actions</th>
                </tr>
            </thead>
            <tbody class=\"bg-white divide-y divide-gray-200\">`;
    accounts.forEach(account => {
        html += `
            <tr class=\"hover:bg-gray-50 transition\">
                <td class=\"px-6 py-4 whitespace-nowrap flex items-center gap-3\">
                    <div class=\"flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden\">
                        ${account.profile_img ? `<img src=\"${account.profile_img}\" alt=\"Profile\" class=\"h-10 w-10 rounded-full object-cover\">` : `<i class='fas fa-user text-gray-400 text-xl'></i>`}
                    </div>
                    <div>
                        <div class=\"font-semibold text-gray-900\">${account.firstname} ${account.lastname}</div>
                        <div class=\"text-xs text-gray-400\">${account.email}</div>
                    </div>
                </td>
                <td class=\"px-6 py-4 whitespace-nowrap\">
                    <div class=\"text-sm text-gray-900\">${account.contact_number || ''}</div>
                </td>
                <td class=\"px-6 py-4 whitespace-nowrap\">
                    <div class=\"text-xs text-gray-500\">${account.created_at || ''}</div>
                </td>
                <td class=\"px-6 py-4 whitespace-nowrap\">
                    <div class=\"text-xs text-gray-500\">${account.last_login || ''}</div>
                </td>
                <td class=\"px-6 py-4 whitespace-nowrap text-right\">
                    <button class=\"inline-flex items-center px-3 py-1.5 rounded bg-green-100 text-green-700 hover:bg-green-200 transition\" title=\"Restore\" onclick=\"restoreAccount(${account.id})\"><i class=\"fas fa-undo\"></i> <span class=\"ml-1 hidden md:inline\">Restore</span></button>
                </td>
            </tr>
        `;
    });
    html += '</tbody></table>';
    $('#inactiveAccountsModalBody').html(html);
}

function restoreAccount(id) {
    showLoading();
    $.ajax({
        url: `/cscadmin/accounts/${id}/restore/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Account restored successfully');
                showInactiveAccountsModal(); // Reload the modal
                loadAccountList(); // Refresh main list
            } else {
                showAlert('danger', response.error || 'Failed to restore account');
            }
        },
        error: function(xhr) {
            let error = 'Failed to restore account';
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