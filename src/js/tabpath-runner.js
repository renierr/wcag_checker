(() => {

    const styleConfig = {
        outline: '2px dotted rgba(255, 223, 128, 1)',
        circleRadius: 10,
        fontSize: 12,
        colors: {
            first: { fill: 'rgba(0, 150, 0, 0.8)', stroke: 'lightgreen', strokeWidth: 2 },
            last: { fill: 'rgba(80, 40, 0, 0.9)', stroke: '#A06020', strokeWidth: 2 },
            default: { fill: 'rgba(255, 0, 0, 0.6)', stroke: 'none' },
            missed: { fill: 'rgba(171, 77, 187, 0.6)' },
            lines: ['rgba(30, 80, 255, 0.85)', 'rgba(100, 149, 237, 0.85)'],
        },
        shadow: 'drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.5))',
    };

    const FOCUSABLE_SELECTOR = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), ' +
      'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]), [contenteditable="true"]';
    const INTERACTIVE_SELECTOR = '[onclick], [onmousedown], [onmouseup], [role="link"], [role="button"], ' +
      '[role="checkbox"], [role="radio"], [role="switch"], [role="tab"], [role="menuitem"], [role="option"], [aria-haspopup]';

    const debounce = (func, wait) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    };

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
            element = element.parentNode || current.getRootNode().host;
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
        const elements = Array.from(document.querySelectorAll(FOCUSABLE_SELECTOR))
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
        const clickableElements = Array.from(document.querySelectorAll(INTERACTIVE_SELECTOR));
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

        const docWidth = Math.max(
            document.body.scrollWidth,
            document.documentElement.scrollWidth,
            document.body.offsetWidth,
            document.documentElement.offsetWidth
        );
        const docHeight = Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.offsetHeight
        );

        // Setze viewBox für relative Positionierung
        svg.setAttribute('viewBox', `0 0 ${docWidth} ${docHeight}`);
        svg.setAttribute('preserveAspectRatio', 'xMinYMin meet');
        svg.setAttribute('width', docWidth);
        svg.setAttribute('height', docHeight);
        svg.setAttribute('aria-label', 'Tab order visualization');
        svg.setAttribute('role', 'img');

        Object.assign(svg.style, {
            position: 'absolute',
            top: '0',
            left: '0',
            pointerEvents: 'none',
            zIndex: '10002',
        });
        document.body.appendChild(svg);

        const updateSvgDimensions = () => {
            const newDocWidth = Math.max(
                document.body.scrollWidth,
                document.documentElement.scrollWidth,
                document.body.offsetWidth,
                document.documentElement.offsetWidth
            );
            const newDocHeight = Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.offsetHeight
            );

            svg.setAttribute('viewBox', `0 0 ${newDocWidth} ${newDocHeight}`);
            svg.setAttribute('width', newDocWidth);
            svg.setAttribute('height', newDocHeight);
        };

        window.addEventListener('resize', debounce(updateSvgDimensions, 100));
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
        const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline.setAttribute('points', '0,0 10,5 0,10 2,5');
        polyline.setAttribute('fill', 'rgba(30, 80, 255, 0.7)');
        marker.appendChild(polyline);
        defs.appendChild(marker);
        svg.appendChild(defs);
    };

    /**
     * Visualizes elements in the tab order.
     * @param {HTMLElement[]} elements
     * @param {SVGElement} svg - SVG container for visualization
     */
    const visualizeElements = (elements, svg) => {

        elements.forEach((el, index) => {
            if (el !== document.body && el !== document.documentElement) {
                Object.assign(el.style, {outline: styleConfig.outline, position: 'relative'});
                el.setAttribute('data-tabpath-styled', 'true');
            }

            const center = getElementCenter(el);

            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', center.x);
            circle.setAttribute('cy', center.y);
            circle.setAttribute('r', '10');

            const style = index === 0 ? styleConfig.colors.first :
                index === elements.length - 1 ? styleConfig.colors.last :
                  styleConfig.colors.default;

            circle.setAttribute('fill', style.fill);
            if (style.stroke) circle.setAttribute('stroke', style.stroke);
            if (style.strokeWidth) circle.setAttribute('stroke-width', style.strokeWidth);

            circle.setAttribute('filter', styleConfig.shadow);
            svg.appendChild(circle);

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', center.x);
            text.setAttribute('y', center.y);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'central');
            text.setAttribute('font-size', '12');
            text.setAttribute('fill', 'white');
            text.textContent = (index + 1).toString();
            svg.appendChild(text);
        });
    };

    /**
     * Visualizes missed elements.
     * @param {HTMLElement[]} elements
     * @param {SVGElement} svg - SVG container for visualization
     */
    const visualizeMissedElements = (elements, svg) => {
        elements.forEach((el, index) => {
            Object.assign(el.style, { outline: '2px dotted rgba(255, 0, 0, 0.8)', position: 'relative' });
            el.setAttribute('data-tabpath-styled', 'true');

            const rect = el.getBoundingClientRect();
            const x = rect.left + window.scrollX;
            const y = rect.top + window.scrollY;

            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', y);
            circle.setAttribute('r', '10');
            circle.setAttribute('fill', styleConfig.colors.missed.fill);
            circle.setAttribute('filter', styleConfig.shadow);
            svg.appendChild(circle);

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', y);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'central');
            text.setAttribute('font-size', '12');
            text.setAttribute('fill', 'white');
            text.textContent = `X${index + 1}`;
            svg.appendChild(text);
        });
    };

    /**
     * Draws curved lines between tabbed elements.
     * @param {HTMLElement[]} elements
     * @param {SVGElement} svg
     */
    const drawTabLines = (elements, svg) => {
        const centers = elements.map(getElementCenter);
        const lineColors = styleConfig.colors.lines;

        const styleElem = document.createElementNS('http://www.w3.org/2000/svg', 'style');
        // language=CSS
        styleElem.textContent = `
        @keyframes dashoffset {
            from {
                stroke-dashoffset: 20;
            }
            to {
                stroke-dashoffset: 0;
            }
        }
        .animated-line {
            animation: dashoffset 1.5s linear infinite;
        }
        `;
        svg.appendChild(styleElem);

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
            line.setAttribute('d', `M ${start.x} ${start.y} Q ${controlX} ${controlY} ${adjustedX2} ${adjustedY2}`);
            line.setAttribute('fill', 'none');
            line.setAttribute('stroke', currentColor);
            line.setAttribute('stroke-width', '1.5');
            line.setAttribute('marker-end', 'url(#arrow)');
            line.setAttribute('filter', 'drop-shadow(0 0 1px black)');

            line.setAttribute('class', 'animated-line');
            line.setAttribute('stroke-dasharray', '4,3');

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
        visualizeElements(tabElements, svg);
        if (missedElements.length) {
            visualizeMissedElements(missedElements, svg);
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

    /**
     * Exports the tab path visualization as an SVG file.
     * @param {SVGElement} svg - The SVG element to export
     * @returns {string} - SVG als String
     */
    const exportTabpathAsSVG = (svg) => {
        if (!svg) throw new Error('No tabpath SVG found');
        const serializer = new XMLSerializer();
        return serializer.serializeToString(svg);
    };

    // Expose global functions
    window.runTabpathAnalysis = async (elements = null) => {
        try {
            const results = await tabpathRunner(elements);
            return {
                success: true,
                data: results
            };
        } catch (error) {
            console.error('Tabpath analysis error:', error.message);
            return {
                success: false,
                error: {
                    message: error.message || 'Unknown Error during analyse',
                    details: error.stack || '',
                    originalError: error
                }
            };
        }
    };
    window.exportTabpathAsSVG = (svg) => {
        return exportTabpathAsSVG(svg || document.querySelector('svg[data-tabpath="true"]'));
    };
    window.cleanTabpathVisualization = cleanTabpathVisualization;

})();
