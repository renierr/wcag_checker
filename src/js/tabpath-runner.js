(() => {
    /**
     * Calculates the center position of an element in the document.
     * @param {HTMLElement} element
     * @returns {{x: number, y: number}}
     */
    const getElementCenter = (element) => {
        const rect = element.getBoundingClientRect();
        return {
            x: rect.left + rect.width / 2 + window.scrollX,
            y: rect.top + rect.height / 2 + window.scrollY,
        };
    };

    /**
     * Generates a unique identifier for an element via CSS path.
     * @param {HTMLElement} element
     * @param {Map} cache
     * @returns {string}
     */
    const getEnhancedCSSPath = (element, cache = new Map()) => {
        if (!(element instanceof Element)) return '';
        if (cache.has(element)) return cache.get(element);

        const path = [];
        while (element && element.nodeType === Node.ELEMENT_NODE) {
            let selector = element.nodeName.toLowerCase();
            if (element.id) {
                selector = `#${element.id}`;
                path.unshift(selector);
                break;
            } else {
                let sib = element, nth = 1;
                while (sib.previousElementSibling) {
                    sib = sib.previousElementSibling;
                    if (sib.nodeName.toLowerCase() === selector) nth++;
                }
                if (nth !== 1) selector += `:nth-child(${nth})`;
            }
            path.unshift(selector);
            element = element.parentNode;
        }
        const result = path.join(' > ');
        cache.set(element, result);
        return result;
    };

    /**
     * Collects focusable elements in tab order.
     * @returns {Promise<HTMLElement[]>}
     */
    const getTabOrder = () => new Promise((resolve) => {
        const focusableSelector = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), ' +
            'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]), [contenteditable="true"]';
        const elements = Array.from(document.querySelectorAll(focusableSelector))
            .filter((el) => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetParent !== null;
            })
            .sort((a, b) => {
                const aTabIndex = a.tabIndex > 0 ? a.tabIndex : 0;
                const bTabIndex = b.tabIndex > 0 ? b.tabIndex : 0;
                return aTabIndex > 0 && bTabIndex > 0 ? aTabIndex - bTabIndex : aTabIndex > 0 ? -1 : bTabIndex > 0 ? 1 : 0;
            });
        resolve(elements);
    });

    /**
     * Collects metadata for elements.
     * @param {HTMLElement[]} elements
     * @param {Map} cache
     * @returns {Array}
     */
    const collectElementInfo = (elements, cache) => elements.map((el, index) => ({
        index: index + 1,
        id: getEnhancedCSSPath(el, cache),
        tag: el.tagName.toLowerCase(),
        text: (el.getAttribute('aria-label') || el.textContent.trim()).slice(0, 50),
        href: el.getAttribute('href') || '',
        class: el.className || '',
        position: getElementCenter(el),
        role: el.getAttribute('role') || '',
    }));

    /**
     * Checks if an element or its parents are hidden.
     * @param {HTMLElement} element
     * @returns {boolean}
     */
    const isElementHiddenByParents = (element) => {
        let parent = element.parentElement;
        while (parent && parent !== document.body) {
            const style = window.getComputedStyle(parent);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return true;
            parent = parent.parentElement;
        }
        return false;
    };

    /**
     * Identifies potentially interactive elements.
     * @returns {Promise<HTMLElement[]>}
     */
    const buildPotentialElements = async () => {
        const tabbedElements = await getTabOrder();
        const interactiveSelector = '[onclick], [onmousedown], [onmouseup], [role="link"], [role="button"], ' +
            '[role="checkbox"], [role="radio"], [role="switch"], [role="tab"], [role="menuitem"], [role="option"], [aria-haspopup]';
        const clickableElements = Array.from(document.querySelectorAll(interactiveSelector));
        const elementsFound = new Set([...tabbedElements, ...clickableElements]);

        const cursorElements = Array.from(document.querySelectorAll('*')).filter(el => {
          if (elementsFound.has(el)) return false;

          let parent = el.parentElement;
          while (parent) {
            if (elementsFound.has(parent)) return false;
            parent = parent.parentElement;
          }

          const style = window.getComputedStyle(el);
          if (style.cursor === 'pointer' && style.display !== 'none' && style.visibility !== 'hidden') {
            const isHiddenByParent = isElementHiddenByParents(el);
            if (isHiddenByParent) return false;

            const children = Array.from(el.children || []);
            const hasRelevantChild = children.some(child =>
                elementsFound.has(child) || window.getComputedStyle(child).cursor === 'pointer');
            return !hasRelevantChild;
          }
          return false;
        });

        return Array.from(new Set([...tabbedElements, ...clickableElements, ...cursorElements]));
    };

    /**
     * Creates an SVG container for visualization.
     * @returns {SVGElement}
     */
    const createSvgContainer = () => {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('data-tabpath', 'true');
        Object.assign(svg.style, {
            position: 'absolute',
            top: '0',
            left: '0',
            width: '100%',
            pointerEvents: 'none',
            zIndex: '10000',
        });
        document.body.appendChild(svg);

        const updateSvgHeight = () => {
            svg.style.height = `${Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.offsetHeight
            )}px`;
        };
        updateSvgHeight();
        window.addEventListener('resize', updateSvgHeight);
        return svg;
    };

    /**
     * Defines an arrowhead marker for SVG paths.
     * @param {SVGElement} svg
     */
    const arrowHeadDefinition = (svg) => {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrow');
        marker.setAttribute('viewBox', '0 0 10 10');
        marker.setAttribute('refX', '5');
        marker.setAttribute('refY', '5');
        marker.setAttribute('markerWidth', '6');
        marker.setAttribute('markerHeight', '6');
        marker.setAttribute('orient', 'auto-start-reverse');
        marker.setAttribute('data-tabpath', 'true');
        const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline.setAttribute('points', '0,0 10,5 0,10 2,5');
        polyline.setAttribute('fill', 'rgba(30, 80, 255, 0.85)');
        polyline.setAttribute('data-tabpath', 'true');
        marker.appendChild(polyline);
        defs.appendChild(marker);
        svg.appendChild(defs);
    };

    /**
     * Visualizes elements in the tab order.
     * @param {HTMLElement[]} elements
     */
    const visualizeElements = (elements) => {
        const config = {
            outline: '2px dotted rgba(255, 223, 128, 1)',
            labelStyles: {
                first: { background: 'rgba(0, 150, 0, 0.8)', color: 'white', border: '2px solid lightgreen' },
                last: { background: 'rgba(80, 40, 0, 0.9)', color: 'white', border: '2px solid #A06020' },
                default: { background: 'rgba(255, 0, 0, 0.6)', color: 'white' },
            },
        };

        elements.forEach((el, index) => {
            Object.assign(el.style, { outline: config.outline, position: 'relative' });
            el.setAttribute('data-tabpath-styled', 'true');
            const number = document.createElement('span');
            Object.assign(number, {
                textContent: (index + 1).toString(),
                'data-tabpath': 'true',
            });
            Object.assign(number.style, {
                position: 'absolute',
                padding: '2px 5px',
                borderRadius: '50%',
                fontSize: '12px',
                zIndex: '10001',
                boxShadow: '2px 2px 4px rgba(0, 0, 0, 0.5)',
                ...(index === 0 ? config.labelStyles.first :
                    index === elements.length - 1 ? config.labelStyles.last : config.labelStyles.default),
            });
            const rect = el.getBoundingClientRect();
            Object.assign(number.style, {
                left: `${rect.left + window.scrollX - 10}px`,
                top: `${rect.top + window.scrollY - 10}px`,
            });
            document.body.appendChild(number);
        });
    };

    /**
     * Visualizes missed elements.
     * @param {HTMLElement[]} elements
     */
    const visualizeMissedElements = (elements) => {
        elements.forEach((el, index) => {
            Object.assign(el.style, { outline: '2px solid rgba(255, 0, 0, 0.8)', position: 'relative' });
            el.setAttribute('data-tabpath-styled', 'true');
            const number = document.createElement('span');
            Object.assign(number, {
                textContent: `X${index + 1}`,
                'data-tabpath': 'true',
            });
            Object.assign(number.style, {
                position: 'absolute',
                padding: '2px 5px',
                borderRadius: '50%',
                fontSize: '12px',
                zIndex: '10001',
                background: 'rgba(171, 77, 187, 0.6)',
                color: 'white',
                boxShadow: '2px 2px 4px rgba(0, 0, 0, 0.5)',
            });
            const rect = el.getBoundingClientRect();
            Object.assign(number.style, {
                left: `${rect.left + window.scrollX - 10}px`,
                top: `${rect.top + window.scrollY - 10}px`,
            });
            document.body.appendChild(number);
        });
    };

    /**
     * Draws curved lines between tabbed elements.
     * @param {HTMLElement[]} elements
     * @param {SVGElement} svg
     */
    const drawTabLines = (elements, svg) => {
        const centers = elements.map(getElementCenter);
        const lineColors = ['rgba(30, 80, 255, 0.85)', 'rgba(65, 105, 225, 0.85)', 'rgba(100, 149, 237, 0.85)'];

        for (let i = 0; i < centers.length - 1; i++) {
            const currentColor = lineColors[i % lineColors.length];
            const [start, end] = [centers[i], centers[i + 1]];
            const dx = end.x - start.x;
            const dy = end.y - start.y;
            const length = Math.sqrt(dx * dx + dy * dy);
            const nx = dx / length;
            const ny = dy / length;
            const gapSize = 8;
            const adjustedX2 = end.x - nx * gapSize;
            const adjustedY2 = end.y - ny * gapSize;
            const curveAmount = Math.min(length * 0.3, 50);
            const controlX = start.x + dx / 2 - ny * curveAmount;
            const controlY = start.y + dy / 2 + nx * curveAmount;

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            line.setAttribute('data-tabpath', 'true');
            line.setAttribute('d', `M ${start.x} ${start.y} Q ${controlX} ${controlY} ${adjustedX2} ${adjustedY2}`);
            line.setAttribute('fill', 'none');
            line.setAttribute('stroke', currentColor);
            line.setAttribute('stroke-width', '1.5');
            line.setAttribute('marker-end', 'url(#arrow)');
            line.setAttribute('filter', 'drop-shadow(0 0 1px black)');
            svg.appendChild(line);
        }
    };

    /**
     * Runs the tab path analysis.
     * @param {HTMLElement[]|null} elements
     * @returns {Promise<{tabbed_elements: Array, potential_elements: Array, missed_elements: Array}>}
     */
    const tabpathRunner = async (elements = null) => {
        console.debug('Tab path Runner started');
        const idCache = new Map();
        const tabElements = elements || await getTabOrder();
        const potentialElements = elements ? await buildPotentialElements() : tabElements;
        const missedElements = potentialElements.filter((pe) => !tabElements.includes(pe));
        console.debug("Tab path Runner found", tabElements.length, "tabbed elements and", potentialElements.length, "potential elements");

        const svg = createSvgContainer();
        arrowHeadDefinition(svg);
        visualizeElements(tabElements);
        if (missedElements.length) {
            visualizeMissedElements(missedElements);
            console.warn(`Missed ${missedElements.length} elements in tab order`);
        }
        drawTabLines(tabElements, svg);

        return {
            tabbed_elements: collectElementInfo(tabElements, idCache),
            potential_elements: collectElementInfo(potentialElements, idCache),
            missed_elements: collectElementInfo(missedElements, idCache),
        };
    };

    /**
     * Cleans up the tabpath visualization.
     */
    const cleanTabpathVisualization = () => {
        document.querySelectorAll('[data-tabpath="true"]').forEach((el) => el.remove());
        document.querySelectorAll('[data-tabpath-styled="true"]').forEach((el) => {
            el.style.outline = '';
            el.removeAttribute('data-tabpath-styled');
        });
        console.debug('Tabpath visualization cleaned');
    };

    // Expose global functions
    window.runTabpathAnalysis = async (elements = null) => {
        try {
            const results = await tabpathRunner(elements);
            console.debug('Tab order analysis complete', results);
            return results;
        } catch (error) {
            console.error('Tabpath analysis error:', error);
            throw error;
        }
    };
    window.cleanTabpathVisualization = cleanTabpathVisualization;
})();
