document.getElementById('profile-edit-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const avatar = document.getElementById('avatar').files[0];

    if (name || email || avatar) {
        alert('Изменения успешно сохранены!');
    } else {
        alert('Пожалуйста, заполните хотя бы одно поле.');
    }
});