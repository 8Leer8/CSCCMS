// Global variable for the currently edited achievement
let currentAchievementId = null;
let showingDeletedAchievements = false;

// All achievement management functions from achievement_list.html
// (excluding duplicate 'let itemToDelete' and only keeping achievement-related code)

function initializeAchievementList() {
    // Set up event handlers
    $(document).on('click', '#addAchievementBtn', showAchievementForm);
    $(document).on('click', '.edit-achievement-btn', function() {
        const achievementId = $(this).data('id');
        showAchievementForm('edit', achievementId);
    });
    $(document).on('click', '.delete-achievement-btn', function() {
        const achievementId = $(this).data('id');
        const achievementTitle = $(this).closest('tr').find('.text-sm.font-medium').text();
        itemToDelete = { type: 'achievement', id: achievementId };
        $('#deleteAchievementTitle').text(achievementTitle);
        openModal('deleteModal');
    });
    $(document).on('click', '.view-achievement-btn', function() {
        const achievementId = $(this).data('id');
        viewAchievement(achievementId);
    });

    // Attach delete confirmation handler
    $(document).off('click', '#confirmDeleteBtn').on('click', '#confirmDeleteBtn', function(e) {
        console.log('Delete button clicked');
        confirmDeleteachievement();
    });
    console.log('Delete handler attached');

    // Filter handling
    $('#categoryFilter, #dateFromFilter').on('change', function() { loadAchievements(); });
    $('#searchFilter').on('keyup', function(e) {
        if (e.key === 'Enter') loadAchievements();
    });

    // Initial load
    loadAchievements();
}

function showAchievementForm(mode = 'create', achievementId = null) {
    showLoading();
    currentAchievementId = achievementId;
    
    $.ajax({
        url: '/cscadmin/achievements/form-data/',
        method: 'GET',
        success: function(response) {
            // Load the form template
            $.ajax({
                url: '/cscadmin/?page=achievement_form',
                method: 'GET',
                success: function(html) {
                    $('#achievementModalBody').html(html);
                    
                    // Populate select options
                    populateSelectOptions('#achievementCategory', response.categories);
                    
                    // Set modal title
                    $('#achievementModalTitle').text(mode === 'edit' ? 'Edit Achievement' : 'Add New Achievement');
                    
                    // Update submit button
                    updateAchievementSubmitButton(mode);
                    
                    // Initialize location dropdown
                    initializeLocationDropdown();
                    
                    // If editing, load the achievement data
                    if (mode === 'edit' && achievementId) {
                        loadAchievementData(achievementId);
                    } else {
                        hideLoading();
                    }
                    
                    openModal('achievementModal');
                },
                error: function() {
                    hideLoading();
                    showAlert('danger', 'Failed to load achievement form');
                }
            });
        },
        error: function() {
            hideLoading();
            showAlert('danger', 'Failed to load form data');
        }
    });
}

function populateSelectOptions(selector, options) {
    let html = '';
    options.forEach(option => {
        html += `<option value="${option.id || option.value}">${option.category || option.label || option.type}</option>`;
    });
    $(selector).html(html);
}

function updateAchievementSubmitButton(mode) {
    const $btn = $('#achievementModalSubmitBtn');
    if (mode === 'edit') {
        $('#achievementSubmitBtnIcon').removeClass('fa-plus-circle').addClass('fa-save');
        $('#achievementSubmitBtnText').text('Save Changes');
    } else {
        $('#achievementSubmitBtnIcon').removeClass('fa-save').addClass('fa-plus-circle');
        $('#achievementSubmitBtnText').text('Add Achievement');
    }
}

function loadAchievementData(achievementId) {
    showLoading();
    
    $.ajax({
        url: `/cscadmin/achievements/${achievementId}/detail/`,
        method: 'GET',
        success: function(response) {
            if (response.success) {
                // Populate form fields
                $('#achievementHeading').val(response.achievement.heading || '');
                $('#achievementPersonInCharge').val(response.achievement.person_in_charge || '');
                $('#achievementId').val(response.achievement.id);
                $('#achievementTitle').val(response.achievement.title);
                $('#achievementContext').val(response.achievement.context);
                $('#achievementContent').val(response.achievement.content);
                $('#achievementAwardedBy').val(response.achievement.awarded_by);
                $('#achievementTeamName').val(response.achievement.team_name || '');
                $('#achievementLocation').val(response.achievement.location).trigger('change');
                $('#achievementAwardedOn').val(response.achievement.awarded_on);
                $('#achievementStartDate').val(response.achievement.start_date || '');
                $('#achievementEndDate').val(response.achievement.end_date || '');
                $('#achievementCategory').val(response.achievement.category_id);
                
                // Show current images if exists
                const existingImages = $('#existingImages');
                existingImages.empty();
                
                if (response.achievement.images && response.achievement.images.length > 0) {
                    response.achievement.images.forEach(image => {
                        existingImages.append(`
                            <div class="relative inline-block m-2">
                                <img src="${image.url}" class="h-32 w-32 object-cover rounded">
                                <button onclick="deleteAchievementImage(${image.id}, ${response.achievement.id})" 
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
                showAlert('danger', response.error || 'Failed to load achievement data');
                hideLoading();
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to load achievement data';
            showAlert('danger', error);
            hideLoading();
        }
    });
}

function submitAchievementForm() {
    showLoading();
    
    const formData = new FormData();
    formData.append('heading', $('#achievementHeading').val());
    formData.append('person_in_charge', $('#achievementPersonInCharge').val());
    formData.append('id', $('#achievementId').val());
    formData.append('title', $('#achievementTitle').val());
    formData.append('context', $('#achievementContext').val());
    formData.append('content', $('#achievementContent').val());
    formData.append('awarded_by', $('#achievementAwardedBy').val());
    formData.append('team_name', $('#achievementTeamName').val());
    formData.append('location', $('#achievementLocation').val());
    formData.append('awarded_on', $('#achievementAwardedOn').val());
    formData.append('start_date', $('#achievementStartDate').val());
    formData.append('end_date', $('#achievementEndDate').val());
    formData.append('category', $('#achievementCategory').val());
    
    // Append new images
    const fileInput = $('#achievementImages')[0];
    if (fileInput && fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('images', fileInput.files[i]);
        }
    }
    
    // Determine URL based on mode
    const url = currentAchievementId ? 
        `/cscadmin/achievements/${currentAchievementId}/update/` : 
        '/cscadmin/achievements/create/';
    
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
                showAlert('success', response.message || 'Achievement saved successfully');
                closeModal('achievementModal');
                loadAchievements();
            } else {
                showAlert('danger', response.error || 'Failed to save achievement');
            }
        },
        error: function(xhr) {
            let error = 'Failed to save achievement';
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

function loadAchievements(page = 1) {
    showLoading();
    
    const params = {
        category: $('#categoryFilter').val(),
        date_from: $('#dateFromFilter').val(),
        search: $('#searchFilter').val(),
        page: page,
        show_deleted: showingDeletedAchievements
    };
    
    $.ajax({
        url: '/cscadmin/achievements/list/',
        method: 'GET',
        data: params,
        success: function(response) {
            // Update the category filter dropdown with the latest categories from the backend
            if (response.categories) {
                var $dropdown = $('#categoryFilter');
                var currentVal = $dropdown.val();
                $dropdown.empty();
                $dropdown.append('<option value="">All Categories</option>');
                response.categories.forEach(function(cat) {
                    $dropdown.append('<option value="' + cat.id + '">' + cat.category + '</option>');
                });
                // Always set the value back, even if not present
                $dropdown.val(currentVal);
            }
            renderAchievementsTable(response);
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to load achievements';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function renderAchievementsTable(data) {
    if (!data || !data.achievements || data.achievements.length === 0) {
        $('#achievementsTableBody').html(`
            <tr>
                <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">
                    No achievements found
                </td>
            </tr>
        `);
        return;
    }
    
    let tableRows = '';
    data.achievements.forEach(achievement => {
        const awardedDate = achievement.awarded_on ? new Date(achievement.awarded_on).toLocaleDateString() : 'N/A';
        const featuredImage = achievement.featured_image ? 
            `<img src="${achievement.featured_image}" class="h-12 w-12 object-cover rounded cursor-pointer achievement-image-preview" data-src="${achievement.featured_image}">` : 
            '<div class="h-12 w-12 bg-gray-100 rounded flex items-center justify-center"><i class="fas fa-image text-gray-400"></i></div>';
        
        tableRows += `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            ${featuredImage}
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${achievement.title || 'Untitled Achievement'}</div>
                            <div class="text-sm text-gray-500">${achievement.team_name ? 'Team: ' + achievement.team_name : ''}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${achievement.awarded_by || 'N/A'}</div>
                    <div class="text-sm text-gray-500">${achievement.person_in_charge ? 'Person in Charge: ' + achievement.person_in_charge : ''}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-500">${awardedDate}</div>
                    ${achievement.location ? `<div class="text-xs text-gray-400">${achievement.location}</div>` : ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="showAchievementForm('edit', ${achievement.id})" class="text-primary-dark hover:text-primary-darker mr-3">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-achievement-btn text-red-600 hover:text-red-900" data-id="${achievement.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    $('#achievementsTableBody').html(tableRows);
    renderAchievementPagination(data);
    
    // Attach image preview handlers
    $('.achievement-image-preview').click(function() {
        const imgSrc = $(this).data('src');
        $('#largeAchievementImage').attr('src', imgSrc);
        openModal('imagePreviewModal');
    });
}

function renderAchievementPagination(data) {
    if (data.total_pages <= 1) {
        $('#paginationContainer').empty();
        return;
    }
    
    let paginationHtml = `
        <nav class="flex items-center justify-between">
            <div class="flex-1 flex justify-between sm:hidden">
                ${data.has_previous ? 
                    `<a href="#" onclick="loadAchievements(${data.previous_page_number}); return false;" class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                        Previous
                    </a>` : 
                    `<span class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-300 bg-white cursor-not-allowed">
                        Previous
                    </span>`}
                ${data.has_next ? 
                    `<a href="#" onclick="loadAchievements(${data.next_page_number}); return false;" class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
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
    
    if (data.has_previous) {
        paginationHtml += `
            <li>
                <a href="#" onclick="loadAchievements(${data.previous_page_number}); return false;" class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">
                    <span class="sr-only">Previous</span>
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    }
    
    // Show page numbers
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
                    <a href="#" onclick="loadAchievements(${i}); return false;" class="bg-white border-gray-300 text-gray-500 hover:bg-gray-50 relative inline-flex items-center px-4 py-2 border text-sm font-medium">
                        ${i}
                    </a>
                </li>
            `;
        }
    }
    
    if (data.has_next) {
        paginationHtml += `
            <li>
                <a href="#" onclick="loadAchievements(${data.next_page_number}); return false;" class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">
                    <span class="sr-only">Next</span>
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }
    
    paginationHtml += `
                    </ul>
                </div>
            </div>
        </nav>
    `;
    
    $('#paginationContainer').html(paginationHtml);
}

function viewAchievement(achievementId) {
    showLoading();
    
    $.ajax({
        url: `/cscadmin/achievements/${achievementId}/detail/`,
        method: 'GET',
        success: function(response) {
            if (response.success) {
                // Create a modal to display the achievement details
                let imagesHtml = '';
                if (response.achievement.images && response.achievement.images.length > 0) {
                    imagesHtml = `<div class="grid grid-cols-3 gap-4 mt-4">`;
                    response.achievement.images.forEach(image => {
                        imagesHtml += `
                            <div class="relative">
                                <img src="${image.url}" class="w-full h-32 object-cover rounded cursor-pointer hover:opacity-75" 
                                     onclick="$('#largeAchievementImage').attr('src', '${image.url}'); openModal('imagePreviewModal');">
                            </div>
                        `;
                    });
                    imagesHtml += `</div>`;
                }
                
                const html = `
                    <div class="bg-white rounded-lg shadow-lg overflow-hidden">
                        <div class="p-6">
                            <div class="flex items-start">
                                ${response.achievement.featured_image ? 
                                    `<div class="flex-shrink-0 mr-4">
                                        <img src="${response.achievement.featured_image}" class="h-32 w-32 object-cover rounded-lg cursor-pointer hover:opacity-75" 
                                             onclick="$('#largeAchievementImage').attr('src', '${response.achievement.featured_image}'); openModal('imagePreviewModal');">
                                    </div>` : ''}
                                <div>
                                    <h3 class="text-xl font-bold text-gray-800">${response.achievement.title || 'Untitled Achievement'}</h3>
                                    <div class="flex items-center mt-2 text-sm text-gray-600">
                                        <span class="mr-4"><i class="fas fa-trophy mr-1"></i> ${response.achievement.category || 'Uncategorized'}</span>
                                        <span><i class="fas fa-calendar-alt mr-1"></i> ${response.achievement.awarded_on || 'N/A'}</span>
                                    </div>
                                    <div class="mt-2">
                                        <span class="text-sm font-medium">Awarded by:</span>
                                        <span class="text-sm ml-2">${response.achievement.awarded_by || 'N/A'}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-6">
                                <h4 class="text-lg font-semibold text-gray-800">Details</h4>
                                <div class="mt-2 text-gray-700">${response.achievement.content || 'No details provided'}</div>
                            </div>
                            
                            ${imagesHtml}
                        </div>
                        <div class="bg-gray-50 px-6 py-4 flex justify-end">
                            <button type="button" onclick="closeModal('viewAchievementModal')" class="px-4 py-2 bg-primary-dark text-white rounded-md hover:bg-primary-darker">
                                Close
                            </button>
                        </div>
                    </div>
                `;
                
                // Create a new modal for viewing
                $('#achievementModalBody').html(html);
                $('#achievementModalTitle').text('Achievement Details');
                $('#achievementModalSubmitBtn').addClass('hidden');
                openModal('achievementModal');
            } else {
                showAlert('danger', response.error || 'Failed to load achievement details');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to load achievement details';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function deleteAchievementImage(imageId, achievementId) {
    if (!confirm('Are you sure you want to delete this image?')) return;
    
    showLoading();
    
    $.ajax({
        url: `/cscadmin/achievement-images/${imageId}/delete/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Image deleted successfully');
                loadAchievementData(achievementId); // Reload the achievement data to update the images list
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

function confirmDeleteachievement() {
    console.log('confirmDelete called', itemToDelete);
    if (itemToDelete.type === 'achievement') {
        deleteAchievement();
    }
}

function deleteAchievement() {
    console.log('deleteAchievement called', itemToDelete);
    showLoading();
    
    $.ajax({
        url: `/cscadmin/achievements/${itemToDelete.id}/delete/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Achievement deleted successfully');
                closeModal('deleteModal');
                loadAchievements();
            } else {
                showAlert('danger', response.error || 'Failed to delete achievement');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to delete achievement';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
            itemToDelete = null;
        }
    });
}

// Handle image preview for new uploads
$(document).on('change', '#achievementImages', function() {
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

// Show deleted achievements (use event delegation for dynamic content)
$(document).off('click', '#showDeletedBtn').on('click', '#showDeletedBtn', function() {
    console.log('Show Deleted clicked');
    showLoading();
    $.ajax({
        url: '/cscadmin/achievements/list/',
        method: 'GET',
        data: { category: '', date_from: '', search: '', page: 1, show_deleted: true },
        success: function(response) {
            renderDeletedAchievementsModal(response.achievements || []);
            openModal('deletedAchievementsModal');
        },
        error: function(xhr) {
            showAlert('danger', 'Failed to load deleted achievements');
        },
        complete: function() {
            hideLoading();
        }
    });
});

function renderDeletedAchievementsModal(deletedAchievements) {
    let html = '';
    if (!deletedAchievements.length) {
        html = '<div class="text-center text-gray-500 py-8">No deleted achievements found.</div>';
    } else {
        html = '<table class="min-w-full divide-y divide-gray-200"><thead><tr>' +
            '<th class="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Title</th>' +
            '<th class="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Category</th>' +
            '<th class="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>' +
            '<th class="px-4 py-2 text-right text-xs font-semibold text-gray-600 uppercase">Actions</th>' +
            '</tr></thead><tbody>';
        deletedAchievements.forEach(acc => {
            html += `<tr>
                <td class="px-4 py-2">${escapeHtml(acc.title) || 'Untitled'}</td>
                <td class="px-4 py-2">${acc.category || 'Uncategorized'}</td>
                <td class="px-4 py-2">${acc.awarded_on ? new Date(acc.awarded_on).toLocaleDateString() : 'N/A'}</td>
                <td class="px-4 py-2 text-right">
                    <button class="restore-achievement-btn text-green-600 hover:text-green-900 font-semibold" data-id="${acc.id}">
                        <i class="fas fa-undo-alt"></i> Restore
                    </button>
                </td>
            </tr>`;
        });
        html += '</tbody></table>';
    }
    $('#deletedAchievementsList').html(html);
}

// Restore achievement
$(document).on('click', '.restore-achievement-btn', function() {
    const id = $(this).data('id');
    showLoading();
    $.ajax({
        url: `/cscadmin/achievements/${id}/restore/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', response.message || 'Achievement restored successfully');
                closeModal('deletedAchievementsModal');
                loadAchievements();
            } else {
                showAlert('danger', response.error || 'Failed to restore achievement');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to restore achievement';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
});

function initializeLocationDropdown() {
    $.getJSON('/static/data/cities.json', function(data) {
        // Extract all unique city/municipality names, appending ' City' if city: true
        let locations = data.map(item => item.city === true ? item.name + ' City' : item.name);
        locations = [...new Set(locations)].sort();

        // Clear and populate the select
        const $select = $('#achievementLocation');
        $select.empty();
        $select.append('<option value="">Select a city...</option>');
        locations.forEach(function(city) {
            $select.append('<option value="' + city + '">' + city + '</option>');
        });

        // Initialize Select2
        $select.select2({
            placeholder: 'Search for a city...',
            allowClear: true,
            width: '100%'
        });
    });
} 