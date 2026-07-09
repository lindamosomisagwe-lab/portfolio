/**
 * Editorial Portfolio Interactive Animations and Layout Scripts
 */

// Define work database for split screen details
const WORK_DATABASE = [
  {
    company: "Go Yapp",
    role: "Marketing & Fundraising Intern",
    date: "May 2026 - Jun 2026 | Remote",
    bullets: [
      "Led marketing strategy for an AI video content platform.",
      "Supported beta validation with <span class='stat-highlight'>1,001</span> users.",
      "Prepared investor-facing fundraising documentation for growth-stage conversations."
    ]
  },
  {
    company: "Fishlist",
    role: "Marketing Intern",
    date: "Jan 2026 - Feb 2026 | Singapore",
    bullets: [
      "Executed multi-platform content strategy across TikTok, Reddit, Instagram, and LinkedIn.",
      "Edited short-form video and built weekly performance reports for the ornamental fish trade."
    ]
  },
  {
    company: "Tech Safari",
    role: "Operations Intern",
    date: "Sep 2025 - Dec 2025 | Nairobi",
    bullets: [
      "Reduced staff workload and improved response times by building and deploying a Chatbase AI chatbot for a live international clientele event.",
      "Rebuilt the company CRM on Notion from scratch, giving leadership operational visibility they did not have before.",
      "Built Zapier automations to cut manual overhead.",
      "Wrote SOPs for onboarding and finance workflows."
    ]
  },
  {
    company: "Differ",
    role: "Consultant",
    date: "May 2025 - Jun 2025 | Oslo / Remote",
    bullets: [
      "Conducted SWOT and competitor analysis to propose a market expansion and pricing strategy."
    ]
  },
  {
    company: "LifeSmart Learning",
    role: "Digital Operations",
    date: "Jan 2024 - Apr 2024 | Nairobi",
    bullets: [
      "Built website, managed community, and ran email/flyer campaigns.",
      "Achieved <span class='stat-highlight'>+40%</span> engagement and <span class='stat-highlight'>90%</span> user satisfaction."
    ]
  }
];

// Define projects database for side drawer overlay
const PROJECTS_DATABASE = [
  {
    title: "Anti-Gravity App",
    status: "Beta",
    statusClass: "beta",
    desc: "A spatial note-taking application designed for infinite canvas brainstorming. Rebuilt core canvas calculations to achieve sub-millisecond redraw updates, giving beta testers operational fluidity they didn't have before.",
    highlights: [
      "Sub-millisecond redraw updates",
      "Infinite canvas coordinate matrix",
      "Operational fluidity for beta testers"
    ]
  },
  {
    title: "LifeSMART Wellness",
    status: "Development",
    statusClass: "development",
    desc: "A personal wellness tracker mapping sleep, steps, and mood metrics in a unified dashboard. Built zapier integrations to aggregate fitness API feeds into Google Sheets automatically.",
    highlights: [
      "Automated Zapier fitness integrations",
      "Unified metrics dashboard mapping sleep/steps",
      "Direct Google Sheets API sync"
    ]
  },
  {
    title: "The Last Code",
    status: "Completed",
    statusClass: "completed",
    desc: "Fully funded Kickstarter board game themed around AI and survival. Prepared production-ready vector assets for card grids and visual packaging. Supported community validation with 420+ global backers.",
    highlights: [
      "420+ global backers on Kickstarter",
      "100% funded campaign goal",
      "Production-ready vector cards and box packaging"
    ]
  },
  {
    title: "Mozaic Bags",
    status: "Completed",
    statusClass: "completed",
    desc: "Direct-to-consumer bag brand concept and operations launch in Gurugram, India. Structured inventory databases, ran manufacturer negotiations, integrated Shopify backends, and set up customer retention systems.",
    highlights: [
      "50 Daily Inquiries pipeline",
      "40% customer engagement",
      "30% shop conversions"
    ]
  }
];

window.initializeScripts = function() {
  // ========================================
  // 1. Word-by-Word Sequential Reveal
  // ========================================
  document.querySelectorAll('.reveal-word-by-word').forEach(el => {
    if (el.dataset.processed) return;
    el.dataset.processed = "true";
    const text = el.textContent.trim();
    const words = text.split(/\s+/);
    el.innerHTML = words.map((word, i) => {
      return `<span class="reveal-line"><span class="reveal-word" style="transition-delay: ${i * 0.08}s">${word}</span></span>`;
    }).join(' ');

    setTimeout(() => {
      el.querySelectorAll('.reveal-word').forEach(w => w.classList.add('visible'));
    }, 100);
  });

  // Reveal normal elements on scroll
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  // ========================================
  // 2. Animated Number Count-Up
  // ========================================
  const countNumbers = document.querySelectorAll('.highlight-num, .stat-num');
  if (countNumbers.length > 0) {
    const countObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const originalText = el.textContent.trim();
          
          // Extract numeric value and suffix (%, +, x, K, etc.)
          const numMatch = originalText.match(/[\d,]+/);
          if (!numMatch) return;

          const numStr = numMatch[0].replace(/,/g, '');
          const target = parseInt(numStr, 10);
          const prefix = originalText.substring(0, originalText.indexOf(numMatch[0]));
          const suffix = originalText.substring(originalText.indexOf(numMatch[0]) + numMatch[0].length);

          let current = 0;
          const duration = 1500;
          const start = performance.now();

          const animate = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            current = Math.round(eased * target);
            
            // Format with commas if target is large
            const formatted = target > 999 ? current.toLocaleString() : current;
            el.textContent = `${prefix}${formatted}${suffix}`;

            if (progress < 1) {
              requestAnimationFrame(animate);
            }
          };

          el.textContent = `${prefix}0${suffix}`;
          requestAnimationFrame(animate);
          countObserver.unobserve(el);
        }
      });
    }, { threshold: 0.2 });

    countNumbers.forEach(el => countObserver.observe(el));
  }

  // ========================================
  // 3. Work Timeline Page Interaction (/work)
  // ========================================
  const timelineItems = document.querySelectorAll('.timeline-item');
  const detailsPanel = document.getElementById('work-details-panel');
  
  if (timelineItems.length > 0 && detailsPanel) {
    const detailsCompany = document.getElementById('details-company');
    const detailsRole = document.getElementById('details-role');
    const detailsDate = document.getElementById('details-date');
    const detailsBullets = document.getElementById('details-bullets');

    function updateDetails(index) {
      const data = WORK_DATABASE[index];
      if (!data) return;

      // Animate out details
      const inner = document.getElementById('details-inner');
      inner.classList.remove('visible');

      setTimeout(() => {
        // Set new values
        detailsCompany.textContent = data.company;
        detailsRole.textContent = data.role;
        detailsDate.textContent = data.date;
        detailsBullets.innerHTML = data.bullets.map(b => `<li>${b}</li>`).join('');

        // Animate back in
        inner.classList.add('visible');
      }, 250);
    }

    timelineItems.forEach(item => {
      // Handle click or hover
      const handler = () => {
        timelineItems.forEach(t => t.classList.remove('active'));
        item.classList.add('active');
        const index = parseInt(item.getAttribute('data-index'), 10);
        updateDetails(index);
      };

      item.addEventListener('click', handler);
      item.addEventListener('mouseenter', handler);
    });
  }

  // ========================================
  // 4. Projects Expander Drawer (/projects)
  // ========================================
  const projectCards = document.querySelectorAll('.clickable-project');
  const backdrop = document.getElementById('project-backdrop');
  const overlay = document.getElementById('project-overlay');
  const overlayClose = document.getElementById('project-close');
  const overlayContent = document.getElementById('project-overlay-content');

  if (projectCards.length > 0 && overlay && backdrop) {
    projectCards.forEach(card => {
      card.addEventListener('click', () => {
        const index = parseInt(card.getAttribute('data-index'), 10);
        const data = PROJECTS_DATABASE[index];
        if (!data) return;

        overlayContent.innerHTML = `
          <h2 style="font-family: var(--font-serif); font-size: 2.5rem; margin-top: 2rem; line-height: 1.1;">${data.title}</h2>
          <span class="status-badge ${data.statusClass}" style="margin-bottom: var(--space-4); display: inline-block;">${data.status}</span>
          <p style="font-size: 1.05rem; line-height: 1.7; color: var(--color-text-secondary);">${data.desc}</p>
          
          <div class="project-overlay-highlights">
            <h4>Strategic Outcomes</h4>
            <ul style="list-style-type: none; padding-left: 0; margin-top: 1rem;">
              ${data.highlights.map(h => `<li style="position: relative; padding-left: 1.5rem; margin-bottom: 0.75rem; font-size: 0.95rem; color: var(--color-text-secondary);"><span style="position: absolute; left: 0; color: var(--color-teal);">■</span>${h}</li>`).join('')}
            </ul>
          </div>
        `;

        backdrop.classList.add('open');
        overlay.classList.add('open');
      });
    });

    const closeOverlay = () => {
      backdrop.classList.remove('open');
      overlay.classList.remove('open');
    };

    overlayClose.addEventListener('click', closeOverlay);
    backdrop.addEventListener('click', closeOverlay);
  }

  // ========================================
  // 5. Designs Gallery Filters & Lightbox (/designs)
  // ========================================
  const filterBtns = document.querySelectorAll('.filter-btn');
  const designItems = document.querySelectorAll('.designs-item');
  const lightbox = document.getElementById('lightbox');
  const lightboxClose = document.getElementById('lightbox-close');
  const lightboxContent = document.getElementById('lightbox-content');
  const lightboxCaption = document.getElementById('lightbox-caption');

  if (filterBtns.length > 0 && designItems.length > 0) {
    // Filter Items
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.getAttribute('data-filter');
        designItems.forEach(item => {
          const category = item.getAttribute('data-category');
          if (filter === 'all' || category === filter) {
            item.style.display = 'block';
          } else {
            item.style.display = 'none';
          }
        });
      });
    });

    // Lightbox Expand
    designItems.forEach(item => {
      item.addEventListener('click', () => {
        const media = item.querySelector('img, video');
        if (!media) return;

        const isVideo = media.tagName.toLowerCase() === 'video';
        const titleText = item.querySelector('.designs-item-title').textContent;

        if (isVideo) {
          lightboxContent.innerHTML = `<video src="${media.getAttribute('src')}" controls autoplay loop></video>`;
        } else {
          lightboxContent.innerHTML = `<img src="${media.getAttribute('src')}" alt="${titleText}">`;
        }

        lightboxCaption.textContent = titleText;
        lightbox.classList.add('open');
      });
    });

    const closeLightbox = () => {
      lightbox.classList.remove('open');
      lightboxContent.innerHTML = '';
    };

    if (lightboxClose && lightbox) {
      lightboxClose.addEventListener('click', closeLightbox);
      lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox || e.target === lightboxClose) {
          closeLightbox();
        }
      });
    }
  }
};

// Auto-run on page load
document.addEventListener('DOMContentLoaded', window.initializeScripts);
