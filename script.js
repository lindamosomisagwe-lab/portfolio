document.addEventListener('DOMContentLoaded', () => {

  // ========================================
  // Scroll Reveal Observer
  // ========================================
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, {
    root: null,
    rootMargin: '0px 0px -60px 0px',
    threshold: 0.1
  });

  document.querySelectorAll('.reveal').forEach(el => {
    revealObserver.observe(el);
  });

  // ========================================
  // Sticky Header — add border on scroll
  // ========================================
  const header = document.getElementById('site-header');
  if (header) {
    let lastScroll = 0;
    window.addEventListener('scroll', () => {
      const scrollY = window.scrollY;
      if (scrollY > 40) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
      lastScroll = scrollY;
    }, { passive: true });
  }

  // ========================================
  // Mobile Menu Toggle
  // ========================================
  const menuToggle = document.getElementById('menu-toggle');
  const navLinks = document.getElementById('nav-links');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      menuToggle.classList.toggle('active');
    });

    // Close menu on link click
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
        menuToggle.classList.remove('active');
      });
    });

    // Close menu on outside click
    document.addEventListener('click', (e) => {
      if (!navLinks.contains(e.target) && !menuToggle.contains(e.target)) {
        navLinks.classList.remove('open');
        menuToggle.classList.remove('active');
      }
    });
  }

  // ========================================
  // Smooth Scroll for Anchor Links
  // ========================================
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;

      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        const headerOffset = header ? header.offsetHeight + 20 : 80;
        const elementPosition = targetElement.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.scrollY - headerOffset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // ========================================
  // Animate stat numbers on scroll
  // ========================================
  const statNumbers = document.querySelectorAll('.stat-number');
  if (statNumbers.length > 0) {
    const statObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseInt(el.textContent, 10);
          if (isNaN(target)) return;

          let current = 0;
          const duration = 1200;
          const start = performance.now();

          const animate = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            current = Math.round(eased * target);
            el.textContent = current;

            if (progress < 1) {
              requestAnimationFrame(animate);
            }
          };

          el.textContent = '0';
          requestAnimationFrame(animate);
          statObserver.unobserve(el);
        }
      });
    }, { threshold: 0.5 });

    statNumbers.forEach(el => statObserver.observe(el));
  }

  // ========================================
  // Parallax effect on hero (subtle)
  // ========================================
  const hero = document.querySelector('.hero');
  if (hero) {
    window.addEventListener('scroll', () => {
      const scrollY = window.scrollY;
      if (scrollY < window.innerHeight) {
        const opacity = 1 - (scrollY / (window.innerHeight * 0.7));
        const translateY = scrollY * 0.15;
        hero.style.opacity = Math.max(0, opacity);
        hero.style.transform = `translateY(${translateY}px)`;
      }
    }, { passive: true });
  }

  // ========================================
  // Designs Gallery Nav Filtering
  // ========================================
  const navLinksList = document.querySelectorAll('.nav-links a[data-target], .filter-link[data-target]');
  const masonryItems = document.querySelectorAll('.masonry-item');
  const categoryHeroes = document.querySelectorAll('.category-statement');
  const isDesignsPage = window.location.pathname.includes('designs.html');

  if (navLinksList.length > 0 && isDesignsPage) {
    const filterByCategory = (targetCategory) => {
      // Update active links (both in nav and on page)
      navLinksList.forEach(l => {
        l.classList.remove('active');
        if (l.getAttribute('data-target') === targetCategory) {
          l.classList.add('active');
        }
      });

      // Update active hero statement
      categoryHeroes.forEach(hero => {
        hero.classList.remove('active');
        if (hero.id === `hero-${targetCategory}`) {
          hero.classList.add('active');
        }
      });

      // Filter masonry items and sections
      const sections = document.querySelectorAll('section[id]');
      masonryItems.forEach(item => {
        const itemCategory = item.getAttribute('data-category');
        if (targetCategory === 'all' || itemCategory === targetCategory) {
          item.style.display = 'block';
        } else {
          item.style.display = 'none';
        }
      });

      // Hide/Show entire sections if filtering
      sections.forEach(section => {
        if (targetCategory === 'all' || section.id === targetCategory) {
          section.style.display = 'block';
        } else {
          section.style.display = 'none';
        }
      });
    };

    navLinksList.forEach(link => {
      link.addEventListener('click', (e) => {
        const targetCategory = link.getAttribute('data-target');
        
        if (targetCategory) {
          e.preventDefault();
          filterByCategory(targetCategory);
          // Scroll to top
          window.scrollTo({ top: 0, behavior: 'smooth' });
          // Update URL hash without jumping
          history.pushState(null, null, `#${targetCategory}`);
        }
      });
    });

    // Handle initial load with hash
    const initialHash = window.location.hash.replace('#', '');
    if (initialHash && ['ventures', 'roles', 'impact', 'all'].includes(initialHash)) {
      filterByCategory(initialHash);
    }
  }
});
