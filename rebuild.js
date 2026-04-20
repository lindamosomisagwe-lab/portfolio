const fs = require('fs');
let html = fs.readFileSync('designs.html', 'utf8');

// The items are categorized.
const extractItems = (cat) => {
  const regex = new RegExp('<div class="masonry-item" data-category="' + cat + '">([\\s\\S]*?)</div>\\s*(?=<div class="masonry-item"|</div>)', 'g');
  let match;
  let items = [];
  while ((match = regex.exec(html)) !== null) {
    items.push(match[0]);
  }
  return items.join('\n');
};

const venturesItems = extractItems('ventures');
const rolesItems = extractItems('roles');
const impactItems = extractItems('impact');

// Remove the old content area
html = html.replace(/<div class="category-statement active" id="hero-all"[\s\S]*?<\/section>/, '');

const newContent = `
  <div class="category-statement active" id="hero-all" style="margin-bottom: 4rem;">
    <p>This is a look at everything I’ve built recently. It is a mix of creative marketing for my own businesses, physical layouts for social enterprises, and community-led fundraising projects. Instead of sticking to one narrow niche, I focus on whatever tools are needed to get a project off the ground. It is the full archive of how I bridge the gap between a business idea and a finished product.</p>
  </div>

  <div class="category-statement" id="hero-ventures" style="margin-bottom: 4rem;">
    <p>I treat branding as a business foundation rather than just a visual. This shows how I manage brand equity, whether it is building a new identity for a student venture or handling a brand transition.</p>
  </div>

  <div class="category-statement" id="hero-roles" style="margin-bottom: 4rem;">
    <p>This is where I focus on making things move. High-contrast, vibrant assets designed to cut through the noise during big retail windows or community events.</p>
  </div>

  <div class="category-statement" id="hero-impact" style="margin-bottom: 4rem;">
    <p>This is where design meets real-world logistics. Layouts for physical fundraisers and collateral needed to mobilize large groups.</p>
  </div>

  <section id="ventures" style="margin-bottom: 6rem;">
    <h2 style="font-family: var(--font-serif); font-size: 2.5rem; margin-bottom: 1rem;">Ventures & Identity</h2>
    <p>I treat branding as a business foundation rather than just a visual. This section shows how I manage brand equity, whether it is building a new identity for a student venture or handling a brand transition.</p>
    <div style="position: relative; width: 100%; height: 0; padding-top: 56.2225%; padding-bottom: 0; box-shadow: 0 2px 8px 0 rgba(63,69,81,0.16); margin-top: 2em; margin-bottom: 4em; overflow: hidden; border-radius: 8px; will-change: transform;">
      <iframe loading="lazy" style="position: absolute; width: 100%; height: 100%; top: 0; left: 0; border: none; padding: 0;margin: 0;" src="https://www.canva.com/design/DAHHTof8KZc/T3FXkUav2IEtDC3UBkAWbA/watch?embed" allowfullscreen="allowfullscreen" allow="fullscreen"></iframe>
    </div>
    <div class="masonry-grid">
${venturesItems}
    </div>
  </section>

  <section id="roles" style="margin-bottom: 6rem;">
    <h2 style="font-family: var(--font-serif); font-size: 2.5rem; margin-bottom: 1rem;">Roles & Social</h2>
    <p>This is where I focus on making things move. These are high-contrast, vibrant assets designed to cut through the noise during big retail windows or community events.</p>
    <h3 style="text-align: center; margin-top: 3rem; margin-bottom: 2rem; font-family: var(--font-serif); font-weight: 500; font-size: 1.8rem;">Brand Storytelling</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; justify-items: center; max-width: 1200px; margin: 0 auto; margin-bottom: 4rem;">
      <blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DWKxc9LAtuE/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:400px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"></blockquote>
      <blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DUOJccJgm9J/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:400px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"></blockquote>
      <blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DTsjANvAnOE/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:400px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"></blockquote>
      <blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DJwcbB-Tpo3/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:400px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"></blockquote>
      <blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DJpLrhQC332/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:400px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"></blockquote>
      <blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DIJ4aezi0Cw/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:400px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"></blockquote>
      <blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/C6B31HQoC4D/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:400px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"></blockquote>
      <script async src="https://www.instagram.com/embed.js"></script>
    </div>
    <div class="masonry-grid">
${rolesItems}
    </div>
  </section>

  <section id="impact" style="margin-bottom: 6rem;">
    <h2 style="font-family: var(--font-serif); font-size: 2.5rem; margin-bottom: 1rem;">Impact & Print Designs</h2>
    <p>This is where design meets real-world logistics. You will find the layouts behind a Kshs 200,000 fundraiser and physical collateral needed to mobilize large groups.</p>
    <div class="masonry-grid">
${impactItems}
    </div>
  </section>
`;

html = html.replace(/(<h1 class="reveal reveal-delay-1">Professional Designs\.<\/h1>)/, "$1\n" + newContent);

fs.writeFileSync('designs.html', html, 'utf8');
