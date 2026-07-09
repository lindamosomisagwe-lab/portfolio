/**
 * Vanilla JS SPA Page Router for Editorial Transition Slides
 */

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('page-container');
  if (!container) return;

  // Intercept local link clicks
  document.body.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (!link) return;

    const href = link.getAttribute('href');
    if (!href) return;

    // Check if it's an internal page link (ends with .html or is index/work/etc)
    const isLocal = href.endsWith('.html') || href.startsWith('/') || (!href.includes('://') && !href.startsWith('#'));
    const isTargetBlank = link.getAttribute('target') === '_blank';

    if (isLocal && !isTargetBlank) {
      e.preventDefault();
      navigateTo(href);
    }
  });

  // Handle browser back/forward buttons
  window.addEventListener('popstate', () => {
    loadPage(window.location.pathname + window.location.search, false);
  });

  // Track active page links
  updateActiveNav(window.location.pathname);

  function navigateTo(url) {
    loadPage(url, true);
  }

  async function loadPage(url, push = true) {
    try {
      // Normalize URL for fetch (fallback index.html if blank)
      let fetchUrl = url;
      if (url === '/' || url === '') {
        fetchUrl = 'index.html';
      }

      const response = await fetch(fetchUrl);
      if (!response.ok) {
        // Fallback to normal navigation
        window.location.href = url;
        return;
      }

      const htmlText = await response.text();
      const parser = new DOMParser();
      const newDoc = parser.parseFromString(htmlText, 'text/html');
      
      const newContent = newDoc.getElementById('page-content');
      const currentContent = document.getElementById('page-content');

      if (!newContent || !currentContent) {
        window.location.href = url;
        return;
      }

      // 1. Append the new page content
      container.appendChild(newContent);

      // 2. Set transition classes
      container.classList.add('transitioning');
      
      // Force repaint
      container.offsetHeight;

      // 3. Perform slide transition
      container.classList.add('slide-next');

      // 4. Update URL and metadata
      if (push) {
        window.history.pushState({}, '', url);
      }
      document.title = newDoc.title;
      updateActiveNav(url);

      // 5. Cleanup after transition completes (600ms matches CSS transition)
      setTimeout(() => {
        // Remove the old content
        if (currentContent.parentNode === container) {
          container.removeChild(currentContent);
        }
        // Reset classes
        container.classList.remove('transitioning');
        container.classList.remove('slide-next');

        // Re-run scripts (animations, click events, observers)
        if (window.initializeScripts) {
          window.initializeScripts();
        }
      }, 600);

    } catch (err) {
      console.error('Failed to load page dynamically, falling back.', err);
      window.location.href = url;
    }
  }

  function updateActiveNav(url) {
    const page = url.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
      const linkPage = link.getAttribute('href').split('/').pop();
      if (linkPage === page || (page === 'index.html' && linkPage === '') || (page === '' && linkPage === 'index.html')) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }
});
