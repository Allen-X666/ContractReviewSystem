/**
 * 智能合同审查助手 - 着陆页交互脚本
 */

document.addEventListener('DOMContentLoaded', function() {
    // 导航栏滚动效果
    initNavbarScroll();
    
    // 平滑滚动
    initSmoothScroll();
    
    // 移动端菜单
    initMobileMenu();
    
    // 滚动显示动画
    initScrollReveal();
    
    // 联系弹框
    initContactModal();
});

/**
 * 导航栏滚动效果
 */
function initNavbarScroll() {
    const navbar = document.getElementById('navbar');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

/**
 * 平滑滚动
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const headerOffset = 80;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * 移动端菜单
 */
function initMobileMenu() {
    const menuToggle = document.getElementById('mobileMenuToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            this.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // 点击菜单项后关闭菜单
        navMenu.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                menuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }
}

/**
 * 滚动显示动画
 */
function initScrollReveal() {
    const revealElements = document.querySelectorAll(
        '.feature-card, .workflow-step, .scenario-card, .tech-category, .arch-layer'
    );
    
    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const elementVisible = 100;
        
        revealElements.forEach((element, index) => {
            const elementTop = element.getBoundingClientRect().top;
            
            if (elementTop < windowHeight - elementVisible) {
                setTimeout(() => {
                    element.classList.add('reveal-active');
                }, index * 100);
            }
        });
    };
    
    // 添加初始样式
    revealElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });
    
    // 添加激活样式
    const style = document.createElement('style');
    style.textContent = `
        .reveal-active {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
    
    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // 初始检查
}

/**
 * 联系弹框
 */
function initContactModal() {
    // 创建弹框HTML
    const modalHTML = `
        <div id="contactModal" class="contact-modal">
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <button class="modal-close" aria-label="关闭">&times;</button>
                <div class="modal-icon">📧</div>
                <h3 class="modal-title">联系我们</h3>
                <p class="modal-desc">联系邮箱：</p>
                <div class="email-box">
                    <span class="email-text">xjl20041115@126.com</span>
                </div>
                <button class="btn-copy" id="copyBtn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                    <span>复制邮箱</span>
                </button>
                <div class="copy-toast" id="copyToast">已复制到剪贴板</div>
            </div>
        </div>
    `;
    
    // 插入弹框到body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // 获取弹框元素
    const modal = document.getElementById('contactModal');
    const overlay = modal.querySelector('.modal-overlay');
    const closeBtn = modal.querySelector('.modal-close');
    const copyBtn = document.getElementById('copyBtn');
    const copyToast = document.getElementById('copyToast');
    const emailText = 'xjl20041115@126.com';
    
    // 打开弹框
    function openModal(e) {
        if (e) e.preventDefault();
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    // 关闭弹框
    function closeModal() {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    // 复制功能
    async function copyEmail() {
        try {
            await navigator.clipboard.writeText(emailText);
            showToast();
        } catch (err) {
            // 降级方案
            const textarea = document.createElement('textarea');
            textarea.value = emailText;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast();
        }
    }
    
    // 显示提示
    function showToast() {
        copyToast.classList.add('show');
        setTimeout(() => {
            copyToast.classList.remove('show');
        }, 2000);
    }
    
    // 绑定事件
    overlay.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);
    copyBtn.addEventListener('click', copyEmail);
    
    // ESC键关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });
    
    // 为mailto链接绑定弹框
    document.querySelectorAll('a[href^="mailto:"]').forEach(link => {
        link.addEventListener('click', openModal);
    });
}

/**
 * 数字计数动画
 */
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = target + (element.dataset.suffix || '');
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(start) + (element.dataset.suffix || '');
        }
    }, 16);
}

// 统计数字动画
const statObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = entry.target.querySelectorAll('.stat-number');
            statNumbers.forEach(stat => {
                const text = stat.textContent;
                const num = parseInt(text);
                const suffix = text.replace(/[0-9]/g, '');
                stat.dataset.suffix = suffix;
                stat.textContent = '0';
                animateCounter(stat, num);
            });
            statObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const heroStats = document.querySelector('.hero-stats');
if (heroStats) {
    statObserver.observe(heroStats);
}
