// Wrap the tabpath_runner function to make it globally accessible
(function() {

  // Calculate element center
  function getElementCenter(element) {
    const rect = element.getBoundingClientRect();
    return {
      x: rect.left + rect.width / 2 + window.scrollX,
      y: rect.top + rect.height / 2 + window.scrollY
    };
  }

  // Generate unique identifier once per element
  function getElementIdentifier(element, cache) {
    if (cache.has(element)) {
      return cache.get(element);
    }
    if (element.id) {
      cache.set(element, element.id);
      return element.id;
    }
    const tag = element.tagName.toLowerCase();
    const classes = element.className ? element.className.replace(/\s+/g, '.') : '';
    let path = [];
    let current = element;
    let depth = 0;
    while (current && current !== document.body && depth < 20) {
      const index = Array.from(current.parentElement.children).indexOf(current);
      path.push(`${current.tagName.toLowerCase()}[${index}]`);
      current = current.parentElement;
      depth++;
    }
    const id = `${tag}${classes ? '.' + classes : ''}:${path.reverse().join('>')}`;
    cache.set(element, id);
    return id;
  }

  function getTabOrder(idCache) {
    const elements = [];


    return new Promise(resolve => {

      elements.push(...getFocusableElements());
      resolve(elements);

      // Helper function to get all focusable elements in tab order
      function getFocusableElements() {
        return Array.from(document.querySelectorAll(
          'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), ' +
          'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]), ' +
          '[contenteditable="true"]'
        )).filter(el => {
          const style = window.getComputedStyle(el);
          return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetParent !== null;
        }).sort((a, b) => {
          // Explicitly handle tabindex order:
          // 1. Elements with positive tabindex (sorted in ascending order)
          // 2. Elements with tabindex="0" or naturally focusable without tabindex
          const aTabIndex = a.tabIndex > 0 ? a.tabIndex : 0;
          const bTabIndex = b.tabIndex > 0 ? b.tabIndex : 0;

          if (aTabIndex > 0 && bTabIndex > 0) return aTabIndex - bTabIndex;
          if (aTabIndex > 0) return -1;
          if (bTabIndex > 0) return 1;

          // For elements with same effective tabindex, maintain DOM order
          return 0;
        });
      }
    });
  }

  // Main function
  async function tabpath_runner() {
    console.debug("Tabpath Runner started");
    // Get all potentially focusable elements
    const potentialElements = Array.from(
      document.querySelectorAll('a[href], button, input:not([type="hidden"]), select, textarea, [tabindex]')
    );
    const idCache = new Map();

    // Get tab order using shared idCache
    const tabElements = await getTabOrder(idCache);
    const tabElementIds = new Set(tabElements.map(el => getElementIdentifier(el, idCache)));

    // Collect element info
    const elementInfo = [];
    tabElements.forEach((el, index) => {
      elementInfo.push({
        index: index + 1,
        id: getElementIdentifier(el, idCache),
        tag: el.tagName.toLowerCase(),
        text: el.textContent.trim().slice(0, 50),
        href: el.getAttribute('href') || '',
        class: el.className || '',
        position: getElementCenter(el)
      });
    });

    // Create SVG container
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('data-tabpath', 'true');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.pointerEvents = 'none';
    svg.style.zIndex = '10000';
    document.body.appendChild(svg);

    // Set initial height
    updateSvgHeight();

    // Recalculate height after a short delay to ensure all elements are rendered
    setTimeout(updateSvgHeight, 100);

    // Add a resize handler to update height when window size changes
    window.addEventListener('resize', updateSvgHeight);

    // Function to calculate and set the appropriate SVG height
    function updateSvgHeight() {
      const docHeight = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight,
        document.body.offsetHeight,
        document.documentElement.offsetHeight,
        document.body.clientHeight,
        document.documentElement.clientHeight
      );

      // Add extra buffer to prevent cut-off
      svg.style.height = (docHeight) + 'px';
    }

    // Arrowhead definition
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('data-tabpath', 'true');
    defs.setAttribute('data-tabpath', 'true');
    marker.setAttribute('id', 'arrow');
    marker.setAttribute('viewBox', '0 0 10 10');
    marker.setAttribute('refX', '5');
    marker.setAttribute('refY', '5');
    marker.setAttribute('markerWidth', '6');
    marker.setAttribute('markerHeight', '6');
    marker.setAttribute('orient', 'auto-start-reverse');
    const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('data-tabpath', 'true');
    polyline.setAttribute('points', '0,0 10,5 0,10 2,5');
    polyline.setAttribute('fill', 'rgba(0, 0, 255, 0.7)');
    marker.appendChild(polyline);
    defs.appendChild(marker);
    svg.appendChild(defs);

    // Visualize found elements
    tabElements.forEach((el, index) => {
      el.style.outline = '3px solid yellow';
      el.style.position = 'relative';
      el.setAttribute('data-tabpath-styled', 'true');
      const number = document.createElement('span');
      number.setAttribute('data-tabpath', 'true');
      number.textContent = (index + 1).toString();
      number.style.position = 'absolute';
      number.style.background = 'red';
      number.style.color = 'white';
      number.style.padding = '2px 5px';
      number.style.borderRadius = '50%';
      number.style.fontSize = '12px';
      number.style.zIndex = '10001';
      number.style.left = '-10px';
      number.style.top = '-10px';
      number.style.boxShadow = '2px 2px 4px rgba(0, 0, 0, 0.5)';

      // Position at the element's top-left corner
      const rect = el.getBoundingClientRect();
      number.style.left = (rect.left + window.scrollX - 10) + 'px';
      number.style.top = (rect.top + window.scrollY - 10) + 'px';

      // Add to body instead of the element itself
      document.body.appendChild(number);
    });


    // Draw connecting lines
    const centers = tabElements.map(el => getElementCenter(el));
    // Define an array of colors to iterate through
    const lineColors = [
      'rgba(30, 80, 255, 0.7)',    // bright blue
      'rgba(65, 105, 225, 0.7)',    // royal blue
      'rgba(100, 149, 237, 0.7)'    // cornflower blue
    ];

    for (let i = 0; i < centers.length - 1; i++) {
      // Get color from the array using modulo to cycle through colors
      const colorIndex = i % lineColors.length;
      const currentColor = lineColors[colorIndex];

      // Shadow color should match the line color but with transparency
      const shadowColor = currentColor.replace('0.7', '0.3');

      // Add shadow effect line
      const shadowLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      shadowLine.setAttribute('data-tabpath', 'true');
      shadowLine.setAttribute('x1', centers[i].x);
      shadowLine.setAttribute('y1', centers[i].y);
      shadowLine.setAttribute('x2', centers[i + 1].x);
      shadowLine.setAttribute('y2', centers[i + 1].y);
      shadowLine.setAttribute('stroke', shadowColor);
      shadowLine.setAttribute('stroke-width', '4');
      shadowLine.setAttribute('filter', 'blur(2px)');
      svg.appendChild(shadowLine);

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('data-tabpath', 'true');
      line.setAttribute('x1', centers[i].x);
      line.setAttribute('y1', centers[i].y);
      line.setAttribute('x2', centers[i + 1].x);
      line.setAttribute('y2', centers[i + 1].y);
      line.setAttribute('stroke', currentColor);
      line.setAttribute('stroke-width', '2');
      line.setAttribute('marker-end', 'url(#arrow)');
      svg.appendChild(line);
    }

    // Return results
    return elementInfo;
  }


  // Keep the original function private
  const tabpathRunner = tabpath_runner;

  function cleanTabpathVisualization() {
    document.querySelectorAll('[data-tabpath="true"]').forEach(el => {
      el.remove();
    });

    // Reset element styles
    document.querySelectorAll('[data-tabpath-styled="true"]').forEach(el => {
      el.style.outline = '';
      el.removeAttribute('data-tabpath-styled');
    });

    console.debug("Tabpath visualization cleaned");
  }

  // Expose the clean function to the global scope
  window.cleanTabpathVisualization = cleanTabpathVisualization;

  // Expose it to the global scope
  window.runTabpathAnalysis = async function() {
    try {
      const results = await tabpathRunner();
      console.debug("Tab order analysis complete", results);
      return results;
    } catch (error) {
      console.error("Error running tabpath analysis:", error);
      throw error;
    }
  };
})();


