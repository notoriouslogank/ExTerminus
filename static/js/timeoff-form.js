document.addEventListener('DOMContentLoaded', () => {
    const start = document.getElementById('start_date');
    const end = document.getElementById('end_date');
    if (!start || !end) return;

    let endTouched = false;
    end.addEventListener('input', () => { endTouched = true; });

    // Initial default
    if (!end.value) end.value = start.value;

    // Keep in sync until edited
    start.addEventListener('input', () => {
        if (!endTouched) end.value = start.value;
    });
});