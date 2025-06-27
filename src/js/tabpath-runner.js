(function() {

  /**
   * Calculates the center position of an element in the document.
   *
   * @param {HTMLElement} element - The element for which to calculate the center position.
   * @returns {{x: number, y: number}}
   */
  function getElementCenter(element) {
    const rect = element.getBoundingClientRect();
    return {
      x: rect.left + rect.width / 2 + window.scrollX,
      y: rect.top + rect.height / 2 + window.scrollY
    };
  }

  /**
   * Generates a unique identifier for an element based on its ID, tag name, class names,
   * and its position in the DOM.
   *
   * @param {HTMLElement} element
   * @param {Map} cache - Map to cache identifiers for elements
   * @returns {*|string}
   */
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

  /**
   * This function collects all potential focusable elements in the document, sorts them by their tabindex
   *
   * @return {Promise<HTMLElement[]>} - Promise resolving to an array of focusable elements in tab order
   */
  function getTabOrder() {
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

  /**
   * Collects information about each element in the tab order.
   * This includes its index, unique identifier, tag name, text content,
   * href attribute (if applicable), class names, and position.
   * This information is stored in an array for further processing or visualization.
   *
   * @param tabElements - Array of elements in tab order
   * @param idCache - Cache to store unique identifiers for elements
   * @returns {[]} - Array of objects containing information about each element
   */
  function collectElementInfo(tabElements, idCache) {
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
    return elementInfo;
  }

  /**
   * Visualizes the missed elements in the tab order by adding a styled outline and a label.
   *
   * @param {HTMLElement[]} missedElements - Array of elements that were missed in the tab order
   */
  function visualizeMissedElements(missedElements) {
    missedElements.forEach((el, index) => {
      el.style.outline = '2px solid rgba(255, 0, 0, 0.8)';
      el.style.position = 'relative';
      el.setAttribute('data-tabpath-styled', 'true');
      const number = document.createElement('span');
      number.setAttribute('data-tabpath', 'true');
      number.textContent = 'X' + (index + 1).toString();
      number.style.position = 'absolute';
      number.style.padding = '2px 5px';
      number.style.borderRadius = '50%';
      number.style.fontSize = '12px';
      number.style.zIndex = '10001';
      number.style.left = '-10px';
      number.style.top = '-10px';
      number.style.background = 'rgba(171,77,187,0.6)';
      number.style.color = 'white';
      number.style.boxShadow = '2px 2px 4px rgba(0, 0, 0, 0.5)';

      const rect = el.getBoundingClientRect();
      number.style.left = (rect.left + window.scrollX - 10) + 'px';
      number.style.top = (rect.top + window.scrollY - 10) + 'px';
      document.body.appendChild(number);
    });
  }

  /**
   * Visualizes the elements in the tab order by adding a styled outline and a number label.
   * Each element is outlined with a dotted style, and a number label is added
   * to indicate its position in the tab order.
   * The first element is styled with a green label, the last element with a darker label,
   * and all other elements with a red label.
   *
   * @param {HTMLElement[]} tabElements - Array of elements in tab order to visualize
   */
  function visualizeElements(tabElements) {
    tabElements.forEach((el, index) => {
      el.style.outline = '2px dotted rgba(255, 223, 128, 1)';
      el.style.position = 'relative';
      el.setAttribute('data-tabpath-styled', 'true');
      const number = document.createElement('span');
      number.setAttribute('data-tabpath', 'true');
      number.textContent = (index + 1).toString();
      number.style.position = 'absolute';
      number.style.padding = '2px 5px';
      number.style.borderRadius = '50%';
      number.style.fontSize = '12px';
      number.style.zIndex = '10001';
      number.style.left = '-10px';
      number.style.top = '-10px';
      number.style.boxShadow = '2px 2px 4px rgba(0, 0, 0, 0.5)';
      // Style based on position in tab order
      if (index === 0) {
        // First element - green label
        number.style.background = 'rgba(0, 150, 0, 0.8)';
        number.style.color = 'white';
        number.style.border = '2px solid lightgreen';
      } else if (index === tabElements.length - 1) {
        // Last element - darker label
        number.style.background = 'rgba(80, 40, 0, 0.9)';
        number.style.color = 'white';
        number.style.border = '2px solid #A06020';
      } else {
        // Normal elements - original red label
        number.style.background = 'rgba(255, 0, 0, 0.6)';
        number.style.color = 'white';
      }

      const rect = el.getBoundingClientRect();
      number.style.left = (rect.left + window.scrollX - 10) + 'px';
      number.style.top = (rect.top + window.scrollY - 10) + 'px';
      document.body.appendChild(number);
    });

  }

  /**
   * Draws curved lines between the centers of the tabbed elements.
   * Each line is drawn with a slight curve and an arrowhead at the end.
   * The lines are styled with different colors to enhance visibility.
   *
   * @param {HTMLElement[]} tabElements - Array of elements in tab order to connect with lines
   * @param {SVGElement} svg - The SVG container where the lines will be drawn
   */
  function drawTabLines(tabElements, svg) {
    const centers = tabElements.map(el => getElementCenter(el));
    // Define an array of colors to iterate through
    const lineColors = [
      'rgba(30, 80, 255, 0.85)',    // bright blue
      'rgba(65, 105, 225, 0.85)',    // royal blue
      'rgba(100, 149, 237, 0.85)'    // cornflower blue
    ];

    for (let i = 0; i < centers.length - 1; i++) {
      // Get color from the array using modulo to cycle through colors
      const colorIndex = i % lineColors.length;
      const currentColor = lineColors[colorIndex];

      // Calculate the direction vector
      const dx = centers[i + 1].x - centers[i].x;
      const dy = centers[i + 1].y - centers[i].y;

      // Calculate the length of the line
      const length = Math.sqrt(dx * dx + dy * dy);

      // If the line is too short, skip the gap
      const gapSize = 8; // Size of the gap in pixels

      // Normalize the direction vector
      const nx = dx / length;
      const ny = dy / length;

      // Calculate adjusted end point with a gap
      const adjustedX2 = centers[i + 1].x - nx * gapSize;
      const adjustedY2 = centers[i + 1].y - ny * gapSize;

      // Calculate control points for the curved path
      // Use 30% of the distance as the curve amount
      const curveAmount = Math.min(length * 0.3, 50);

      // Create a slight offset perpendicular to the line direction
      const perpX = -ny; // Perpendicular vector
      const perpY = nx;

      // Create control point (use perpendicular vector for a nice curve)
      const controlX = centers[i].x + dx / 2 + perpX * curveAmount;
      const controlY = centers[i].y + dy / 2 + perpY * curveAmount;

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      line.setAttribute('data-tabpath', 'true');
      line.setAttribute('d', `M ${centers[i].x} ${centers[i].y} Q ${controlX} ${controlY} ${adjustedX2} ${adjustedY2}`);
      line.setAttribute('fill', 'none');

      line.setAttribute('stroke', currentColor);
      line.setAttribute('stroke-width', '1.5');
      line.setAttribute('marker-end', 'url(#arrow)');
      line.setAttribute('filter', 'drop-shadow(0 0 1px black)');
      svg.appendChild(line);
    }
  }

  /**
   * Creates an SVG container to hold the visualization.
   * This container is positioned absolutely to cover the entire viewport,
   * ensuring it does not interfere with user interactions.
   * The SVG is styled to be transparent and has a high z-index
   * to appear above other content.
   *
   * @returns {SVGElement}
   */
  function createSvgContainer() {
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
      svg.style.height = (docHeight) + 'px';
    }
    return svg;
  }

  /**
   * Defines the arrowhead marker used for the SVG paths.
   * This function creates a marker element with a polyline
   * that represents the arrowhead shape.
   * The marker is added to the SVG definitions section
   * and is used to style the end of the lines drawn between elements.
   *
   * @param {SVGElement} svg - The SVG container where the marker will be defined
   */
  function arrowHeadDefinition(svg) {
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
    polyline.setAttribute('fill', 'rgba(30, 80, 255, 0.85)');
    marker.appendChild(polyline);
    defs.appendChild(marker);
    svg.appendChild(defs);
  }

  function isElementHiddenByParents(element) {
    let parent = element.parentElement;
    while (parent) {
      const parentStyle = window.getComputedStyle(parent);
      if (parentStyle.display === 'none' || parentStyle.visibility === 'hidden' || parentStyle.opacity === '0') {
        return true;
      }
      parent = parent.parentElement;
    }
    return false;
  }

  async function buildPotentialElements() {
    const tabbedElements = await getTabOrder();
    const clickableElements = Array.from(document.querySelectorAll('*')).filter(el => {
      const eventAttrs = ['onclick', 'onmousedown', 'onmouseup'];
      if (eventAttrs.some(attr => el.hasAttribute(attr))) {
        return true;
      }
      const role = el.getAttribute('role');
      if (role) {
        const interactiveRoles = ['link', 'button', 'checkbox', 'radio', 'switch', 'tab', 'menuitem', 'option'];
        if (interactiveRoles.includes(role.toLowerCase())) return true;
      }
      if (el.hasAttribute('aria-haspopup')) return true;

      return false;
    });

    const elementsFoundSoFar = new Set([...tabbedElements, ...clickableElements]);
    const cursorElements = Array.from(document.querySelectorAll('*')).filter(el => {
      if (elementsFoundSoFar.has(el)) return false;

      let parent = el.parentElement;
      while (parent) {
        if (elementsFoundSoFar.has(parent)) return false;
        parent = parent.parentElement;
      }

      const style = window.getComputedStyle(el);
      if (style.cursor === 'pointer' && style.display !== 'none' && style.visibility !== 'hidden') {
        const isHiddenByParent = isElementHiddenByParents(el);
        if (isHiddenByParent) return false;

        const children = Array.from(el.children || []);
        const hasRelevantChild = children.some(child =>
          elementsFoundSoFar.has(child) || window.getComputedStyle(child).cursor === 'pointer');
        return !hasRelevantChild;
      }
      return false;
    });

    cursorElements.forEach(el => elementsFoundSoFar.add(el));
    return Array.from(elementsFoundSoFar);
  }

  /**
   * Runs the tab path analysis.
   *
   * This function creates an SVG container to draw lines between elements
   * and adds number labels to each element.
   * It returns an object containing the tabbed elements and potential elements.
   *
   * @param {HTMLElement[]} elements - Optional array of elements to analyze.
   * If provided, these elements will be used instead of collecting them from the document via a CSS selector.
   * @returns {Promise<{tabbed_elements: [], potential_elements: *[]}>}
   */
  async function tabpathRunner(elements = null) {
    console.debug("Tab path Runner started");
    const idCache = new Map();
    const tabElements = elements || await getTabOrder(idCache);
    const potentialElements = elements ? await buildPotentialElements() : tabElements;
    console.debug("Tab path Runner found", tabElements.length, "tabbed elements and", potentialElements.length, "potential elements");
    const svg = createSvgContainer();
    arrowHeadDefinition(svg);
    visualizeElements(tabElements);
    drawTabLines(tabElements, svg);

    // compare tabElements and potentialElements and output the differences as missed elements
    const missedElements = potentialElements.filter(pe => !tabElements.includes(pe));
    if (missedElements.length > 0) {
      visualizeMissedElements(missedElements)
      console.warn("Missed elements in tab order:", missedElements.length);
    }

    return {
      tabbed_elements: collectElementInfo(tabElements, idCache),
      potential_elements: collectElementInfo(potentialElements, idCache),
      missed_elements: collectElementInfo(missedElements, idCache)
    };
  }


  /**
   * Cleans up the tabpath visualization by removing all elements that were added during the analysis.
   */
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
  window.runTabpathAnalysis = async function(elements= null) {
    try {
      const results = await tabpathRunner(elements);
      console.debug("Tab order analysis complete", results);
      return results;
    } catch (error) {
      console.error("Error running tabpath analysis:", error);
      throw error;
    }
  };
})();


