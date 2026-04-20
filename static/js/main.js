/* app/static/js/main.js */
// Actualizar contador de notificaciones
function updateNotificationCount() {
    fetch('/notifications/unread_count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            }
        });
}

// Ejecutar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    updateNotificationCount();

    // Actualizar cada 60 segundos
    setInterval(updateNotificationCount, 60000);
});