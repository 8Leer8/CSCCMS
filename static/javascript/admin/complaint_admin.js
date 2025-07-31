// Handles loading and displaying complaints with filter and modal preview

function initComplaintsPage() {
    const complaintsTableBody = document.querySelector('#complaintsTable tbody');
    const complaintTypeFilter = document.getElementById('complaintTypeFilter');
    const defaultImg = document.getElementById('defaultComplaintImg')?.value || '';
    if (!complaintsTableBody || !complaintTypeFilter) return;
    let complaintsData = [];

    // Fetch complaint types for filter
    fetch('/cscadmin/complaints/list/?types_only=1', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.json())
        .then(data => {
            if (data.types) {
                data.types.forEach(type => {
                    const opt = document.createElement('option');
                    opt.value = type.id;
                    opt.textContent = type.type;
                    complaintTypeFilter.appendChild(opt);
                });
            }
        });

    // Fetch and render complaints
    function loadComplaints() {
        const type = complaintTypeFilter.value;
        fetch(`/cscadmin/complaints/list/?type=${type}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(res => res.json())
            .then(data => {
                complaintsData = data.complaints || [];
                renderTable();
            });
    }

    function truncate(text, max = 50) {
        return text.length > max ? text.slice(0, max) + '...' : text;
    }

    function formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    }

    function renderTable() {
        complaintsTableBody.innerHTML = '';
        if (complaintsData.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 5;
            td.className = 'text-center text-gray-500 py-6';
            td.textContent = 'No complaints found';
            tr.appendChild(td);
            complaintsTableBody.appendChild(tr);
            return;
        }
        complaintsData.forEach(complaint => {
            const tr = document.createElement('tr');
            tr.style.height = '72px'; // fixed row height
            // Image
            const imgTd = document.createElement('td');
            imgTd.className = 'px-6 py-2';
            const img = document.createElement('img');
            img.src = complaint.image || defaultImg;
            img.alt = 'Complaint Image';
            img.style.width = '48px';
            img.style.height = '48px';
            img.style.objectFit = 'cover';
            img.className = 'rounded';
            imgTd.appendChild(img);
            // Description
            const descTd = document.createElement('td');
            descTd.className = 'px-6 py-2 align-middle';
            descTd.textContent = truncate(complaint.description, 60);
            // Type
            const typeTd = document.createElement('td');
            typeTd.className = 'px-6 py-2 align-middle';
            typeTd.textContent = complaint.complaint_type;
            // Date & Time
            const dateTd = document.createElement('td');
            dateTd.className = 'px-6 py-2 align-middle text-sm text-gray-500';
            dateTd.textContent = formatDate(complaint.created_at);
            // Action
            const actionTd = document.createElement('td');
            actionTd.className = 'text-right px-6 py-2 align-middle';
            const btn = document.createElement('button');
            btn.className = 'text-blue-600 hover:text-blue-900 font-medium';
            btn.innerHTML = '<i class="fas fa-eye"></i>';
            btn.title = 'Preview';
            btn.addEventListener('click', () => showPreview(complaint));
            actionTd.appendChild(btn);

            tr.appendChild(imgTd);
            tr.appendChild(descTd);
            tr.appendChild(typeTd);
            tr.appendChild(dateTd);
            tr.appendChild(actionTd);
            complaintsTableBody.appendChild(tr);
        });
    }

    function showPreview(complaint) {
        document.getElementById('previewImg').src = complaint.image || defaultImg;
        document.getElementById('previewType').textContent = complaint.complaint_type;
        document.getElementById('previewDescription').textContent = complaint.description;
        document.getElementById('complaintModal').classList.remove('hidden');
    }

    // Modal close logic
    window.closeModal = function(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    };

    complaintTypeFilter.addEventListener('change', loadComplaints);
    loadComplaints();

    // --- Manage Complaint Type Modal Logic ---
    const manageBtn = document.getElementById('manageComplaintTypeBtn');
    const manageModal = document.getElementById('manageComplaintTypeModal');
    const typeListDiv = document.getElementById('complaintTypeList');
    const addTypeForm = document.getElementById('addComplaintTypeForm');
    const newTypeInput = document.getElementById('newComplaintType');

    manageBtn.addEventListener('click', function() {
        loadComplaintTypes();
        manageModal.classList.remove('hidden');
    });

    function loadComplaintTypes() {
        fetch('/cscadmin/complaints/types/list/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
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
                        nameInput.value = type.type;
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
                            fetch(`/cscadmin/complaints/types/${type.id}/edit/`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCookie('csrftoken'),
                                    'X-Requested-With': 'XMLHttpRequest'
                                },
                                body: JSON.stringify({ type: newName })
                            })
                            .then(res => res.json())
                            .then(data => {
                                if (data.success) {
                                    nameInput.value = data.type.type;
                                    updateTypeDropdown(type.id, data.type.type);
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
                            fetch(`/cscadmin/complaints/types/${type.id}/delete/`, {
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
        fetch('/cscadmin/complaints/types/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ type: typeName })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                newTypeInput.value = '';
                loadComplaintTypes();
                addTypeToDropdown(data.type.id, data.type.type);
                complaintTypeFilter.value = data.type.id;
                complaintTypeFilter.dispatchEvent(new Event('change'));
            } else {
                alert(data.error || 'Failed to add type');
            }
        })
        .catch(() => alert('Failed to add type'));
    });

    function addTypeToDropdown(id, name) {
        if ([...complaintTypeFilter.options].some(opt => opt.value == id)) return;
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = name;
        complaintTypeFilter.appendChild(opt);
    }
    function updateTypeDropdown(id, name) {
        [...complaintTypeFilter.options].forEach(opt => {
            if (opt.value == id) opt.textContent = name;
        });
    }
    function removeTypeFromDropdown(id) {
        [...complaintTypeFilter.options].forEach(opt => {
            if (opt.value == id) opt.remove();
        });
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
} 