    function toggleDropdown(id) {
        const dropdown = document.getElementById(id);
        const isVisible = dropdown.style.display === 'block';
        document.querySelectorAll('.dropdown-options').forEach(option => option.style.display = 'none');
        dropdown.style.display = isVisible ? 'none' : 'block';
    }