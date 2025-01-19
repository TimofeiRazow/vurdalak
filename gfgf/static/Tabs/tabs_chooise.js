function  get_url() {
    id = document.getElementById('task_id').value;
    return '/tab/' + String(id)
}