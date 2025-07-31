function initFeedbackPage() {
    const feedbackTableBody = document.querySelector('#feedbackTable tbody');
    const feedbackTypeFilter = document.getElementById('feedbackTypeFilter');
    const ratingFilter = document.getElementById('ratingFilter');
    if (!feedbackTableBody || !feedbackTypeFilter || !ratingFilter) return;
    let feedbackData = [];

    // Fetch feedback types for filter
    fetch('/cscadmin/feedback/list/?types_only=1', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.json())
        .then(data => {
            if (data.types) {
                data.types.forEach(type => {
                    const opt = document.createElement('option');
                    opt.value = type.id;
                    opt.textContent = type.name;
                    feedbackTypeFilter.appendChild(opt);
                });
            }
        });

    // Fetch and render feedback
    function loadFeedback() {
        const type = feedbackTypeFilter.value;
        const rating = ratingFilter.value;
        let url = `/cscadmin/feedback/list/?type=${type}`;
        if (rating) {
            url += `&rating=${rating}`;
        }
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(res => res.json())
            .then(data => {
                feedbackData = data.feedback || [];
                renderTable();
            });
    }

    function renderTable() {
        feedbackTableBody.innerHTML = '';
        if (feedbackData.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 5;
            td.className = 'text-center text-gray-500 py-6';
            td.textContent = 'No feedback found';
            tr.appendChild(td);
            feedbackTableBody.appendChild(tr);
            return;
        }
        feedbackData.forEach(feedback => {
            const tr = document.createElement('tr');
            tr.style.height = '72px';
            // Rating
            const ratingTd = document.createElement('td');
            ratingTd.className = 'px-6 py-2 align-middle';
            ratingTd.innerHTML = getRatingStars(feedback.rating);
            // Comment
            const commentTd = document.createElement('td');
            commentTd.className = 'px-6 py-2 align-middle';
            commentTd.textContent = feedback.comment || '-';
            // Type
            const typeTd = document.createElement('td');
            typeTd.className = 'px-6 py-2 align-middle';
            typeTd.textContent = feedback.feedback_type;
            // Date
            const dateTd = document.createElement('td');
            dateTd.className = 'px-6 py-2 align-middle text-sm text-gray-500';
            dateTd.textContent = formatDate(feedback.created_at);
            // Action
            const actionTd = document.createElement('td');
            actionTd.className = 'text-right px-6 py-2 align-middle';
            const btn = document.createElement('button');
            btn.className = 'text-blue-600 hover:text-blue-900 font-medium';
            btn.innerHTML = '<i class="fas fa-eye"></i>';
            btn.title = 'Preview';
            btn.addEventListener('click', () => showPreview(feedback));
            actionTd.appendChild(btn);

            tr.appendChild(ratingTd);
            tr.appendChild(commentTd);
            tr.appendChild(typeTd);
            tr.appendChild(dateTd);
            tr.appendChild(actionTd);
            feedbackTableBody.appendChild(tr);
        });
    }

    function getRatingStars(rating) {
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                stars += '<i class="fas fa-star text-yellow-400"></i>';
            } else {
                stars += '<i class="far fa-star text-gray-300"></i>';
            }
        }
        return stars;
    }

    function formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function showPreview(feedback) {
        document.getElementById('previewRating').innerHTML = getRatingStars(feedback.rating);
        document.getElementById('previewFeedbackType').textContent = feedback.feedback_type;
        document.getElementById('previewDate').textContent = formatDate(feedback.created_at);
        document.getElementById('previewComment').textContent = feedback.comment || '-';
        document.getElementById('feedbackModal').classList.remove('hidden');
    }

    // Modal close logic
    window.closeModal = function(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    };

    feedbackTypeFilter.addEventListener('change', loadFeedback);
    ratingFilter.addEventListener('change', loadFeedback);
    loadFeedback();

    // --- Manage Feedback Type Modal Logic ---
    const manageBtn = document.getElementById('manageFeedbackTypeBtn');
    const manageModal = document.getElementById('manageFeedbackTypeModal');
    const typeListDiv = document.getElementById('feedbackTypeList');
    const addTypeForm = document.getElementById('addFeedbackTypeForm');
    const newTypeInput = document.getElementById('newFeedbackType');

    manageBtn.addEventListener('click', function() {
        loadFeedbackTypes();
        manageModal.classList.remove('hidden');
    });

    function loadFeedbackTypes() {
        fetch('/cscadmin/feedback/types/list/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(res => res.json())
            .then(data => {
                typeListDiv.innerHTML = '';
                if (data.types && data.types.length) {
                    data.types.forEach(type => {
                        const row = document.createElement('div');
                        row.className = 'flex items-center justify-between mb-2 group';
                        // Editable name
                        const nameInput = document.createElement('input');
                        nameInput.type = 'text';
                        nameInput.value = type.name;
                        nameInput.className = 'flex-1 border border-transparent rounded px-2 py-1 text-sm bg-transparent group-hover:border-gray-300 focus:border-primary-dark focus:bg-white';
                        nameInput.disabled = true;
                        // Edit button
                        const editBtn = document.createElement('button');
                        editBtn.innerHTML = '<i class="fas fa-edit"></i>';
                        editBtn.className = 'text-blue-600 hover:text-blue-900 px-2';
                        // Save button
                        const saveBtn = document.createElement('button');
                        saveBtn.innerHTML = '<i class="fas fa-save"></i>';
                        saveBtn.className = 'text-green-600 hover:text-green-900 px-2 hidden';
                        // Delete button
                        const delBtn = document.createElement('button');
                        delBtn.innerHTML = '<i class="fas fa-trash"></i>';
                        delBtn.className = 'text-red-600 hover:text-red-900 px-2';
                        // Edit logic
                        editBtn.onclick = function() {
                            nameInput.disabled = false;
                            nameInput.focus();
                            editBtn.classList.add('hidden');
                            saveBtn.classList.remove('hidden');
                        };
                        saveBtn.onclick = function() {
                            const newName = nameInput.value.trim();
                            if (!newName) return;
                            fetch(`/cscadmin/feedback/types/${type.id}/edit/`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCookie('csrftoken'),
                                    'X-Requested-With': 'XMLHttpRequest'
                                },
                                body: JSON.stringify({ name: newName })
                            })
                            .then(res => res.json())
                            .then(data => {
                                if (data.success) {
                                    nameInput.value = data.type.name;
                                    updateTypeDropdown(type.id, data.type.name);
                                    nameInput.disabled = true;
                                    editBtn.classList.remove('hidden');
                                    saveBtn.classList.add('hidden');
                                } else {
                                    alert(data.error || 'Failed to update type');
                                }
                            });
                        };
                        // Delete logic
                        delBtn.onclick = function() {
                            if (!confirm('Delete this type?')) return;
                            fetch(`/cscadmin/feedback/types/${type.id}/delete/`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCookie('csrftoken'),
                                    'X-Requested-With': 'XMLHttpRequest'
                                }
                            })
                            .then(res => res.json())
                            .then(data => {
                                if (data.success) {
                                    row.remove();
                                    removeTypeFromDropdown(type.id);
                                } else {
                                    alert(data.error || 'Failed to delete type');
                                }
                            });
                        };
                        row.appendChild(nameInput);
                        row.appendChild(editBtn);
                        row.appendChild(saveBtn);
                        row.appendChild(delBtn);
                        typeListDiv.appendChild(row);
                    });
                } else {
                    typeListDiv.innerHTML = '<div class="text-gray-400 text-sm">No types found.</div>';
                }
            });
    }

    addTypeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const typeName = newTypeInput.value.trim();
        if (!typeName) return;
        fetch('/cscadmin/feedback/types/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ name: typeName })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                newTypeInput.value = '';
                loadFeedbackTypes();
                addTypeToDropdown(data.type.id, data.type.name);
                feedbackTypeFilter.value = data.type.id;
                feedbackTypeFilter.dispatchEvent(new Event('change'));
            } else {
                alert(data.error || 'Failed to add type');
            }
        })
        .catch(() => alert('Failed to add type'));
    });

    function addTypeToDropdown(id, name) {
        if ([...feedbackTypeFilter.options].some(opt => opt.value == id)) return;
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = name;
        feedbackTypeFilter.appendChild(opt);
    }
    function updateTypeDropdown(id, name) {
        [...feedbackTypeFilter.options].forEach(opt => {
            if (opt.value == id) opt.textContent = name;
        });
    }
    function removeTypeFromDropdown(id) {
        [...feedbackTypeFilter.options].forEach(opt => {
            if (opt.value == id) opt.remove();
        });
    }
} 