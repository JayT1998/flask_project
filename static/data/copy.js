document.addEventListener("DOMContentLoaded", () => {
  // The container for all images
  const container = document.getElementById("explore-container");
  const sentinel = document.getElementById("sentinel");
  let loading = false;

  /**
   * IntersectionObserver for the sentinel:
   * When the user scrolls and the sentinel enters viewport, load 1 new random image.
   */
  const sentinelObserver = new IntersectionObserver(async (entries) => {
    const entry = entries[0];
    if (entry.isIntersecting && !loading) {
      loading = true;
      // Fetch exactly ONE random image
      const response = await fetch("/api/images_html?limit=1");
      const htmlSnippet = await response.text();
      // Insert new snippet above the sentinel
      sentinel.insertAdjacentHTML("beforebegin", htmlSnippet);

      // Observe newly inserted sections for lazy loading
      const newSections = container.querySelectorAll(".explore-section.placeholder[data-src]");
      newSections.forEach(section => sectionObserver.observe(section));

      loading = false;
    }
  }, {
    root: null,    // if entire page scrolls
    threshold: 0.1 // triggers at 10% visibility
  });
  sentinelObserver.observe(sentinel);

  /**
   * IntersectionObserver for lazy loading:
   * Observe each .explore-section with data-src, load background when in view.
   */
  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const section = entry.target;
        const realSrc = section.getAttribute("data-src");
        if (realSrc) {
          section.style.backgroundImage = `url('${realSrc}')`;
          section.removeAttribute("data-src");
        }
        // Unobserve once it's loaded
        sectionObserver.unobserve(section);
      }
    });
  }, {
    root: null,    // same scroll context as above
    threshold: 0.1
  });

  // If you rendered an initial batch of images in the template, observe them now
  const existingSections = container.querySelectorAll(".explore-section.placeholder[data-src]");
  existingSections.forEach(section => sectionObserver.observe(section));
});