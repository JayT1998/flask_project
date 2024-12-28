function setupCarousel(container) {
    // Identify elements
    const genre = container.dataset.genre;
    const prevBtn = container.querySelector('.prevBtn');
    const nextBtn = container.querySelector('.nextBtn');
    const carouselWrapper = container.querySelector('.carousel-wrapper');
    const sentinel = container.querySelector('.loadMoreSentinel');

    // State
    let currentPage = 1;
    let currentSlideIndex = 0;
    let fetchedImages = [];

    // 1) Load images from server (specific to this genre)
    async function loadImages(page) {
      try {
        const response = await fetch(`/api/carousel-images?page=${page}&genre=${encodeURIComponent(genre)}`);
        const data = await response.json();
        const images = data.images;

        if (!images || images.length === 0) {
          // If there are no more iamges stop observing
          observer.disconnect();
          return;
        }

        // Append to local array
        fetchedImages = [...fetchedImages, ...images];

        // Re-render to show new images
        renderCarouselSlides();
      } catch (error) {
        console.error("Error loading images:", error);
      }
    }

    // 2) Render the current 3 slides in the carousel
    function renderCarouselSlides() {
      carouselWrapper.innerHTML = '';

      for (let i = currentSlideIndex; i < currentSlideIndex + 3; i++) {
        if (i >= 0 && i < fetchedImages.length) {
            const { image_url, title, description } = fetchedImages[i];

            const slide = document.createElement('div');
            slide.classList.add('carousel-slide');
                // loads image from static file
            const gameImage = document.createElement('img');
            gameImage.dataset.src = image_url; // lazy load
            gameImage.alt = title;
            gameImage.classList.add('carousel-image', 'lazy-image');
                // creates title using genre
            const titleEl = document.createElement('h3');
            titleEl.textContent = title;
                // creates descrition
            const descEl = document.createElement('p');
            descEl.textContent = description;

            slide.appendChild(gameImage);
            slide.appendChild(titleEl);
            slide.appendChild(descEl);

            carouselWrapper.appendChild(slide);
        }
      }

      // Activate lazy loading for newly rendered images
      lazyLoadImages(carouselWrapper);
    }

    // 3) Button logic
    nextBtn.addEventListener('click', () => {
      if (currentSlideIndex + 3 < fetchedImages.length) {
        currentSlideIndex += 3;
      }
      // else, we might decide to load more, or wrap around, etc.
      renderCarouselSlides();
    });

    prevBtn.addEventListener('click', () => {
      currentSlideIndex = Math.max(0, currentSlideIndex - 3);
      renderCarouselSlides();
    });

    // 4) Infinite scroll observer for this genre
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          currentPage++;
          loadImages(currentPage);
        }
      });
    });

    observer.observe(sentinel);

    // 5) Lazy load images (IntersectionObserver)
    function lazyLoadImages(wrapper) {
      const lazyImages = wrapper.querySelectorAll('img.lazy-image');
      const lazyObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            img.classList.remove('lazy-image');
            lazyObserver.unobserve(img);
          }
        });
      });
      lazyImages.forEach(img => lazyObserver.observe(img));
    }

    // Initialize by loading the first page
    loadImages(currentPage);
  }

  // On DOMContentLoaded, find all genre carousels and initialize each
  window.addEventListener('DOMContentLoaded', () => {
    const carouselContainers = document.querySelectorAll('.carousel-container');
    carouselContainers.forEach(container => {
      setupCarousel(container);
    });
  });