document.addEventListener('DOMContentLoaded', () => {
    const toggles = document.querySelectorAll('.password-toggle');
    if (!toggles.length) return;

    for (const btn of toggles) {
        const targetId = btn.getAttribute('data-target');
        const input = document.getElementById(targetId);
        if (!input) continue;

        btn.addEventListener('click', () => {
            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            btn.setAttribute('aria-pressed', String(!showing));
            btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
            const icon = btn.querySelector('[aria-hidden="true"]');
            if (icon) icon.textContent = showing ? '👁️' : '🙈';
        });
    }
});