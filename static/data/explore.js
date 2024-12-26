document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("explore-container");
  const sentinel = document.getElementById("sentinel");

  /**
   * Lazy Load Observer:
   * Observes each .explore-section with data-src. 
   * When intersecting, we swap out placeholder with real background image.
   */
  const lazyObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const section = entry.target;
        const realSrc = section.getAttribute("data-src");
        if (realSrc) {
          section.style.backgroundImage = `url('${realSrc}')`;
          section.removeAttribute("data-src");
          section.classList.remove("placeholder");
        }
        // Unobserve once loaded
        lazyObserver.unobserve(section);
      }
    });
  }, {
    root: null,      // entire window
    threshold: 0.1
  });

  // Observe any existing sections on page load
  const existingSections = container.querySelectorAll(".explore-section.placeholder[data-src]");
  existingSections.forEach(sec => lazyObserver.observe(sec));

  /**
   * Function to create a new .explore-section DOM element
   * from the JSON object { title, description, image_url }.
   */
  function createSection(imageObj) {
    const section = document.createElement("div");
    section.classList.add("explore-section", "placeholder");
    // data-src holds the real background for lazy load
    section.setAttribute("data-src", imageObj.image_url);

    // Add overlay for text
    const overlay = document.createElement("div");
    overlay.classList.add("explore-overlay");

    const h2 = document.createElement("h2");
    h2.textContent = imageObj.title;

    const p = document.createElement("p");
    p.textContent = imageObj.description;

    overlay.appendChild(h2);
    overlay.appendChild(p);
    section.appendChild(overlay);

    // Observe with lazyObserver
    lazyObserver.observe(section);
    return section;
  }

  /**
   * Infinite Scroll Observer:
   * Observes the #sentinel. When it appears, fetch more images from /load_images
   * and append them to the container.
   */
  let loading = false;
  const sentinelObserver = new IntersectionObserver(async (entries) => {
    const entry = entries[0];
    if (entry.isIntersecting && !loading) {
      loading = true;
      try {
        // Load 1 or 5 images at a time - your choice
        const response = await fetch("/load_images?limit=1");
        if (response.ok) {
          const data = await response.json(); // e.g., [{title, description, image_url}, ...]

          data.forEach((imgObj) => {
            // Create a new .explore-section for each item
            const newSection = createSection(imgObj);
            // Insert above the sentinel
            sentinel.before(newSection);
          });
        } else {
          console.error("Failed to fetch images:", response.status);
        }
      } catch (err) {
        console.error("Error loading images:", err);
      }
      loading = false;
    }
  }, {
    root: null,  // entire window
    threshold: 0.1
  });

  sentinelObserver.observe(sentinel);
});