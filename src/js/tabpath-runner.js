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

// Check why an element is not focusable
  function getMissingReason(element) {
    if (element.getAttribute('tabindex') === '-1') return 'tabindex="-1"';
    if (element.disabled) return 'disabled';
    const style = window.getComputedStyle(element);
    if (style.display === 'none') return 'display: none';
    if (style.visibility === 'hidden') return 'visibility: hidden';
    if (!element.offsetParent) return 'outside visible area';
    return 'unknown';
  }

  // Replace your getTabOrder function with this improved version
  function getTabOrder(idCache) {
    const elements = [];
    const seenElements = new Set();

    // First focus the document body to start from the beginning
    document.body.focus();

    return new Promise(resolve => {
      let maxAttempts = 1000;

      // Add event listener for real tab key presses (if you want to allow manual tabbing)
      const tabListener = (e) => {
        if (e.key === 'Tab') {
          e.preventDefault(); // Prevent default browser tab behavior
          console.log("Tab key intercepted");
          // Record the current element before moving to next
          recordAndAdvance();
        }
      };

      document.addEventListener('keydown', tabListener);

      function recordAndAdvance() {
        const activeElement = document.activeElement;
        const id = getElementIdentifier(activeElement, idCache);

        console.log("Active element:", activeElement, "ID:", id);

        if (seenElements.has(id) || maxAttempts-- <= 0) {
          console.log("Max attempts reached or element already seen, resolving.");
          document.removeEventListener('keydown', tabListener);
          resolve(elements);
          return;
        }

        elements.push(activeElement);
        seenElements.add(id);

        // Get all focusable elements
        const focusables = getFocusableElements();
        const currentIndex = focusables.indexOf(activeElement);

        // Move to next element
        if (currentIndex >= 0 && currentIndex < focusables.length - 1) {
          // Focus the next element
          setTimeout(() => {
            focusables[currentIndex + 1].focus();
            setTimeout(recordAndAdvance, 50);  // Continue with next element
          }, 50);
        } else {
          // Reached end of focusable elements
          console.log("Reached end of tab sequence");
          document.removeEventListener('keydown', tabListener);
          resolve(elements);
        }
      }

      // Helper function to get all focusable elements in tab order
      function getFocusableElements() {
        return Array.from(document.querySelectorAll(
          'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), ' +
          'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )).filter(el => {
          const style = window.getComputedStyle(el);
          return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetParent !== null;
        }).sort((a, b) => {
          const aTabIndex = a.tabIndex || 0;
          const bTabIndex = b.tabIndex || 0;
          return aTabIndex - bTabIndex;
        });
      }

      // Start the process
      recordAndAdvance();
    });
  }

  // Main function
  async function tabpath_runner() {
    console.log("Tabpath Runner started");
    // Get all potentially focusable elements
    const potentialElements = Array.from(
      document.querySelectorAll('a[href], button, input:not([type="hidden"]), select, textarea, [tabindex]')
    );
    const idCache = new Map();
    const potentialIds = new Map(potentialElements.map(el => [el, getElementIdentifier(el, idCache)]));

    // Get tab order using shared idCache
    const tabElements = await getTabOrder(idCache);
    const tabElementIds = new Set(tabElements.map(el => getElementIdentifier(el, idCache)));

    // Identify missing elements
    const missingElements = potentialElements.filter(el => !tabElementIds.has(getElementIdentifier(el, idCache)));

    // Collect element info
    const elementInfo = [];
    tabElements.forEach((el, index) => {
      elementInfo.push({
        index: index + 1,
        tag: el.tagName.toLowerCase(),
        text: el.textContent.trim().slice(0, 50),
        href: el.getAttribute('href') || '',
        id: el.id || '',
        class: el.className || '',
        status: 'found',
        reason: '',
        position: getElementCenter(el)
      });
    });
    missingElements.forEach((el, index) => {
      elementInfo.push({
        index: `X${index + 1}`,
        tag: el.tagName.toLowerCase(),
        text: el.textContent.trim().slice(0, 50),
        href: el.getAttribute('href') || '',
        id: el.id || '',
        class: el.className || '',
        status: 'missing',
        reason: getMissingReason(el),
        position: getElementCenter(el)
      });
    });

    // Create SVG container
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight) + 'px';
    svg.style.pointerEvents = 'none';
    svg.style.zIndex = '10000';
    document.body.appendChild(svg);

    // Arrowhead definition
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', 'arrow');
    marker.setAttribute('viewBox', '0 0 10 10');
    marker.setAttribute('refX', '5');
    marker.setAttribute('refY', '5');
    marker.setAttribute('markerWidth', '6');
    marker.setAttribute('markerHeight', '6');
    marker.setAttribute('orient', 'auto-start-reverse');
    const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('points', '0,0 10,5 0,10 2,5');
    polyline.setAttribute('fill', 'blue');
    marker.appendChild(polyline);
    defs.appendChild(marker);
    svg.appendChild(defs);

    // Visualize found elements
    tabElements.forEach((el, index) => {
      el.style.outline = '3px solid yellow';
      el.style.position = 'relative';
      const number = document.createElement('span');
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
      el.appendChild(number);
    });

    // Visualize missing elements
    missingElements.forEach((el, index) => {
      el.style.outline = '3px solid red';
      el.style.position = 'relative';
      const number = document.createElement('span');
      number.textContent = `X${index + 1}`;
      number.style.position = 'absolute';
      number.style.background = 'gray';
      number.style.color = 'white';
      number.style.padding = '2px 5px';
      number.style.borderRadius = '50%';
      number.style.fontSize = '12px';
      number.style.zIndex = '10001';
      number.style.left = '-10px';
      number.style.top = '-10px';
      el.appendChild(number);
    });

    // Draw connecting lines
    const centers = tabElements.map(el => getElementCenter(el));
    for (let i = 0; i < centers.length - 1; i++) {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', centers[i].x);
      line.setAttribute('y1', centers[i].y);
      line.setAttribute('x2', centers[i + 1].x);
      line.setAttribute('y2', centers[i + 1].y);
      line.setAttribute('stroke', 'blue');
      line.setAttribute('stroke-width', '2');
      line.setAttribute('marker-end', 'url(#arrow)');
      svg.appendChild(line);
    }

    // Return results
    return elementInfo;
  }


  // Keep the original function private
  const tabpathRunner = tabpath_runner;

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


