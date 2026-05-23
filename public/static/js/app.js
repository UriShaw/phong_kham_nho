/**
 * MedPro - JavaScript chính
 * Xử lý: Navbar scroll, animations, realtime polling
 */

// ============== Navbar Scroll Effect ==============
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('navbar');
    if (navbar) {
        if (window.scrollY > 10) {
            navbar.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
        } else {
            navbar.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
        }
    }
});

// ============== Scroll Animation (Intersection Observer) ==============
document.addEventListener('DOMContentLoaded', function() {
    // Animate elements khi scroll vào viewport
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    // Áp dụng cho các card
    document.querySelectorAll('.card, .glass-card, .doctor-card').forEach(el => {
        if (!el.closest('.animate-stagger')) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'all 0.5s ease-out';
            observer.observe(el);
        }
    });

    // Cập nhật thông báo realtime
    updateNotificationCount();
    setInterval(updateNotificationCount, 30000); // 30 giây
});

// ============== Cập nhật badge thông báo ==============
async function updateNotificationCount() {
    try {
        const res = await fetch('/api/thong-bao/count');
        if (res.ok) {
            const data = await res.json();
            const badges = document.querySelectorAll('.notification-badge');
            const count = data.data ? data.data.count : 0;
            badges.forEach(badge => {
                if (count > 0) {
                    badge.textContent = count;
                    badge.style.display = 'flex';
                } else {
                    badge.style.display = 'none';
                }
            });
        }
    } catch (e) {
        // Người dùng chưa đăng nhập
    }
}

// ============== Format số tiền VNĐ ==============
function formatVND(amount) {
    return new Intl.NumberFormat('vi-VN').format(amount) + 'đ';
}

// ============== Confirm Dialog ==============
function confirmAction(message) {
    return confirm(message || 'Bạn chắc chắn muốn thực hiện?');
}

// ============== Loading State ==============
function setLoading(btn, loading = true) {
    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;"></div> Đang xử lý...';
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalText;
    }
}

// ============== Copy Text ==============
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Đã sao chép!', 'success');
    }).catch(() => {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Đã sao chép!', 'success');
    });
}

// ============== Toast Notification ==============
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'error' : ''}`;

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    const colors = {
        success: 'var(--primary)',
        error: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--info)'
    };

    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info}" style="color: ${colors[type] || colors.info}; font-size: 1.2rem;"></i>
        <span>${message}</span>
    `;
    toast.style.cursor = 'pointer';
    toast.onclick = () => toast.remove();

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease-out reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

console.log('🏥 MedPro - Hệ thống chăm sóc sức khỏe');
