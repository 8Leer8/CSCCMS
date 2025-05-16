// Global variables for post management
let currentPostId = null;

function showPostForm(mode = 'create', postId = null) {
    showLoading();
    currentPostId = postId;
    
    $.ajax({
        url: '/cscadmin/posts/form-data/',
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        success: function(response) {
            if (response.success) {
                // Populate select options
                populateSelectOptions('#postCategory', response.categories);
                populateSelectOptions('#postStatus', response.status_choices);
                
                // Set modal title
                $('#postModalTitle').text(mode === 'edit' ? 'Edit Post' : 'Create New Post');
                
                // Show/hide status field based on mode
                if (mode === 'edit') {
                    $('#postStatusField').show();
                } else {
                    $('#postStatusField').hide();
                }
                
                // Update submit button
                updatePostSubmitButton(mode);
                
                // If edit mode, load post data
                if (mode === 'edit' && postId) {
                    loadPostData(postId);
                } else {
                    hideLoading();
                }
                
                openModal('postModal');
            } else {
                hideLoading();
                showAlert('danger', response.error || 'Failed to load post form data');
            }
        },
        error: function() {
            hideLoading();
            showAlert('danger', 'Failed to load post form data');
        }
    });
}

function updatePostSubmitButton(mode) {
    const submitBtn = $('#postModalSubmitBtn');
    const submitBtnIcon = $('#postSubmitBtnIcon');
    const submitBtnText = $('#postSubmitBtnText');
    
    if (mode === 'edit') {
        submitBtnIcon.removeClass('fa-plus-circle').addClass('fa-save');
        submitBtnText.text('Update Post');
    } else {
        submitBtnIcon.removeClass('fa-save').addClass('fa-plus-circle');
        submitBtnText.text('Add Post');
    }
}

function loadPostData(postId) {
    showLoading();
    $.ajax({
        url: `/cscadmin/posts/${postId}/`,
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        success: function(response) {
            if (response.success) {
                const post = response.post;
                $('#postId').val(post.id);
                $('#postTitle').val(post.title);
                $('#postContent').val(post.content);
                $('#postContext').val(post.context);
                $('#postCategory').val(post.category_id);
                $('#postStatus').val(post.status);
                $('#postPublishStart').val(post.start_publish_on);
                $('#postPublishEnd').val(post.end_publish_on);
                
                // Handle images
                const existingImagesContainer = $('#existingImages');
                existingImagesContainer.empty();
                if (post.images && post.images.length > 0) {
                    post.images.forEach(image => {
                        existingImagesContainer.append(`
                            <div class="relative inline-block">
                                <img src="${image.url}" class="w-20 h-20 object-cover rounded" alt="Post image">
                                <button type="button" onclick="deletePostImage(${image.id})" class="absolute top-0 right-0 bg-red-500 text-white rounded-full p-1">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        `);
                    });
                }
            } else {
                showAlert('danger', response.error || 'Failed to load post data');
                closeModal('postModal');
            }
        },
        error: function() {
            showAlert('danger', 'Failed to load post data');
            closeModal('postModal');
        },
        complete: function() {
            hideLoading();
        }
    });
}

function submitPostForm() {
    showLoading();
    
    // Validate required fields
    const requiredFields = ['title', 'content', 'context'];
    const missingFields = [];
    requiredFields.forEach(field => {
        if (!$(`#post${field.charAt(0).toUpperCase() + field.slice(1)}`).val()) {
            missingFields.push(field);
        }
    });
    
    if (missingFields.length > 0) {
        hideLoading();
        showAlert('danger', `Missing required fields: ${missingFields.join(', ')}`);
        return;
    }
    
    const formData = new FormData();
    formData.append('title', $('#postTitle').val());
    formData.append('content', $('#postContent').val());
    formData.append('context', $('#postContext').val());
    const categoryVal = $('#postCategory').val();
    if (categoryVal && categoryVal !== 'null') {
        formData.append('category', categoryVal);
    }
    formData.append('status', $('#postStatus').val());
    
    // Add dates if they have values
    const startDate = $('#postPublishStart').val();
    const endDate = $('#postPublishEnd').val();
    if (startDate) formData.append('start_publish_on', startDate);
    if (endDate) formData.append('end_publish_on', endDate);
    
    // Append images
    const fileInput = $('#postImages')[0];
    if (fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('images', fileInput.files[i]);
        }
    }
    
    // Determine URL based on mode
    const url = currentPostId ? 
        `/cscadmin/posts/${currentPostId}/update/` : 
        '/cscadmin/posts/create/';
    
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
                showAlert('success', response.message || 'Post saved successfully');
                closeModal('postModal');
                loadPageContent('posts'); // Refresh the post list
            } else {
                showAlert('danger', response.error || 'Failed to save post');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to save post';
            showAlert('danger', error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

function deletePostImage(imageId) {
    if (!confirm('Are you sure you want to delete this image?')) {
        return;
    }
    
    showLoading();
    $.ajax({
        url: `/cscadmin/posts/images/${imageId}/delete/`,
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Image deleted successfully');
                // Remove the image element from the DOM
                $(`#postImage-${imageId}`).parent().remove();
            } else {
                showAlert('danger', response.error || 'Failed to delete image');
            }
        },
        error: function() {
            showAlert('danger', 'Failed to delete image');
        },
        complete: function() {
            hideLoading();
        }
    });
}

// Preview uploaded images
$('#postImages').on('change', function() {
    const fileInput = this;
    const previewContainer = $('#uploadedImages');
    previewContainer.empty();
    
    if (fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
            const file = fileInput.files[i];
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewContainer.append(`
                    <div class="relative">
                        <img src="${e.target.result}" class="w-20 h-20 object-cover rounded" alt="Preview">
                    </div>
                `);
            };
            
            reader.readAsDataURL(file);
        }
    }
});

function populateSelectOptions(selector, options) {
    const $select = $(selector);
    $select.empty();
    if (selector === '#postCategory') {
        $select.append('<option value="">Select a category</option>');
        options.forEach(opt => {
            $select.append(`<option value="${opt.id}">${opt.category}</option>`);
        });
    } else {
        options.forEach(opt => {
            $select.append(`<option value="${opt.value}">${opt.label}</option>`);
        });
    }
} 