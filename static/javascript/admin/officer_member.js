window.initializeOfficersPage = function() {
    let currentPage = 1;
    let searchTimeout;
    const searchInput = document.getElementById('officerSearchFilter');
    const tableBody = document.getElementById('officersTableBody');
    const paginationContainer = document.getElementById('paginationContainer');
    const addOfficerBtn = document.getElementById('addOfficerBtn');
    const showInactiveOfficersBtn = document.getElementById('showInactiveOfficersBtn');
    let showInactive = false;

    if (!searchInput) return; // Don't run if not on the right page

    // Load initial data
    loadOfficers();

    // Event listeners
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            loadOfficers();
        }, 500);
    });

    showInactiveOfficersBtn.addEventListener('click', function() {
        showInactive = !showInactive;
        currentPage = 1;
        loadOfficers();
        this.classList.toggle('bg-gray-200');
        this.classList.toggle('bg-primary-dark');
        this.classList.toggle('text-primary-dark');
        this.classList.toggle('text-white');
    });

    function loadOfficers() {
        const searchQuery = searchInput.value;
        fetch(`/cscadmin/get-officers/?search=${searchQuery}&page=${currentPage}&show_inactive=${showInactive}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    renderOfficers(data.officers);
                    renderPagination(data.current_page, data.total_pages);
                } else {
                    showError(data.message);
                }
            })
            .catch(error => {
                showError('Error loading officers');
                console.error('Error:', error);
            });
    }

    function renderOfficers(officers) {
        tableBody.innerHTML = '';
        officers.forEach(officer => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">${officer.name}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${officer.position}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${officer.contact}</div>
                    <div class="text-sm text-gray-500">${officer.email}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${officer.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${officer.status}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="editOfficer(${officer.id})" class="text-primary-dark hover:text-primary-darker mr-3">
                        <i class="fas fa-edit"></i>
                    </button>
                    ${officer.status === 'active' ? 
                        `<button onclick="deleteOfficer(${officer.id})" class="text-red-600 hover:text-red-900">
                            <i class="fas fa-trash"></i>
                        </button>` :
                        `<button onclick="restoreOfficer(${officer.id})" class="text-green-600 hover:text-green-900">
                            <i class="fas fa-undo"></i>
                        </button>`
                    }
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    function renderPagination(currentPage, totalPages) {
        paginationContainer.innerHTML = '';
        if (totalPages <= 1) return;

        const pagination = document.createElement('div');
        pagination.className = 'flex items-center space-x-2';

        // Previous button
        const prevButton = document.createElement('button');
        prevButton.className = `px-3 py-1 rounded-md ${currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'}`;
        prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevButton.disabled = currentPage === 1;
        prevButton.onclick = () => {
            if (currentPage > 1) {
                currentPage--;
                loadOfficers();
            }
        };
        pagination.appendChild(prevButton);

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                const pageButton = document.createElement('button');
                pageButton.className = `px-3 py-1 rounded-md ${i === currentPage ? 'bg-primary-dark text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`;
                pageButton.textContent = i;
                pageButton.onclick = () => {
                    currentPage = i;
                    loadOfficers();
                };
                pagination.appendChild(pageButton);
            } else if (i === currentPage - 3 || i === currentPage + 3) {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'px-2 text-gray-500';
                ellipsis.textContent = '...';
                pagination.appendChild(ellipsis);
            }
        }

        // Next button
        const nextButton = document.createElement('button');
        nextButton.className = `px-3 py-1 rounded-md ${currentPage === totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'}`;
        nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextButton.disabled = currentPage === totalPages;
        nextButton.onclick = () => {
            if (currentPage < totalPages) {
                currentPage++;
                loadOfficers();
            }
        };
        pagination.appendChild(nextButton);

        paginationContainer.appendChild(pagination);
    }

    function showError(message) {
        // Implement your error notification system here
        console.error(message);
    }
};

// Global functions for officer actions
function editOfficer(id) {
    // Implement edit officer functionality
    console.log('Edit officer:', id);
}

function deleteOfficer(id) {
    if (confirm('Are you sure you want to deactivate this officer?')) {
        fetch(`/cscadmin/officer-delete/${id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                if (typeof window.initializeOfficersPage === 'function') window.initializeOfficersPage();
            } else {
                showError(data.message);
            }
        })
        .catch(error => {
            showError('Error deleting officer');
            console.error('Error:', error);
        });
    }
}

function restoreOfficer(id) {
    fetch(`/cscadmin/officer-restore/${id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            if (typeof window.initializeOfficersPage === 'function') window.initializeOfficersPage();
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        showError('Error restoring officer');
        console.error('Error:', error);
    });
}

// Utility function to get CSRF token
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