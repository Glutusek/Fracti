/**
 * @typedef {Object} OLFeature
 * @property {function(): OLGeometry} [getGeometry]
 * @property {function(): OLFeature} clone
 */

/**
 * @typedef {Object} OLGeometry
 * @property {function(string, string): OLGeometry} transform
 */

/**
 * @typedef {Object} OLSource
 * @property {function(): void} clear
 * @property {function(OLFeature): void} addFeature
 * @property {function(): any} [getTileGrid]
 * @property {function(): void} changed
 */

/**
 * @typedef {Object} OLLayer
 * @property {function(): OLSource} getSource
 */

/**
 * @typedef {Object} OLView
 * @property {function(number[]): void} setCenter
 * @property {function(number): void} [setZoom]
 * @property {function(): number[]} [getCenter]
 * @property {function(): number} [getZoom]
 */

/**
 * @typedef {Object} OLMap
 * @property {function(): OLView} getView
 * @property {function(): OLCollection<OLLayer>} getLayers
 * @property {function(): void} render
 * @property {function(): void} [renderSync]
 * @property {function(number[]): number[]} [getPixelFromCoordinate]
 * @property {function(Object): void} [dispatchEvent]
 * @property {function(): void} [updateSize]
 */

/**
 * @template T
 * @typedef {Object} OLCollection
 * @property {function(): void} clear
 * @property {function(T): void} push
 * @property {function(): T[]} getArray
 */

/**
 * @typedef {Object} OLFormatWKT
 * @property {function(string, Object=): OLFeature} readFeature
 */

/**
 * @typedef {Object} OLProj
 * @property {function(number[], string, string): number[]} transform
 * @property {function(number[]): number[]} fromLonLat
 */

/**
 * @typedef {Object} OLGeom
 * @property {function(new:OLPoint, number[])} Point
 */

/**
 * @typedef {Object} OLPoint
 * @property {function(string, string): OLPoint} transform
 */

/**
 * @typedef {Object} OLFormat
 * @property {function(new:OLFormatWKT)} WKT
 */

/**
 * @typedef {OLMap & {
 *   deserialize: function(string): void,
 *   map?: OLMap,
 *   featureCollection?: OLCollection<OLFeature>,
 *   featureOverlay?: OLLayer
 * }} GeoDjangoMap
 */

/**
 * @typedef {Object} OLGlobal
 * @property {OLProj} proj
 * @property {OLFormat} format
 * @property {OLGeom} geom
 * @property {function(new:OLFeature, OLGeometry=): void} Feature
 */

/**
 * @typedef {Window & {
 *   ol?: OLGlobal,
 *   django?: { ol: OLGlobal }
 * }} CustomWindow
 */

(function () {
    'use strict';

    /**
     * Debounce function to limit the frequency of function execution.
     */
    function debounce(func, timeout = 800) {
        let timer;
        const debounced = (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => { func(...args); }, timeout);
        };
        debounced.cancel = () => clearTimeout(timer);
        return debounced;
    }

    let retryCount = 0;
    const MAX_RETRIES = 10;

    function setupMapSync(latInput, lonInput, locationInput) {
        const win = /** @type {CustomWindow} */ (window);
        const ol = win.ol || win.django?.ol;

        /**
         * Transforms coordinates to EPSG:4326 if they are in Web Mercator.
         * @param {number} lon
         * @param {number} lat
         * @returns {number[]}
         */
        function transformTo4326(lon, lat) {
            const proj = ol?.proj;
            if ((Math.abs(lon) > 180 || Math.abs(lat) > 90) && proj && typeof proj.transform === 'function') {
                try {
                    return proj.transform([lon, lat], 'EPSG:3857', 'EPSG:4326');
                } catch (e) {
                    console.debug("Transform to 4326 failed", e);
                }
            }
            return [lon, lat];
        }

        /**
         * Transforms coordinates to EPSG:3857 (Web Mercator).
         * @param {number} lon
         * @param {number} lat
         * @returns {number[]}
         */
        function transformTo3857(lon, lat) {
            const proj = ol?.proj;
            if (proj && typeof proj.fromLonLat === 'function') {
                try {
                    return proj.fromLonLat([lon, lat]);
                } catch (e) {
                    console.debug("Transform to 3857 failed", e);
                }
            }
            return [lon, lat];
        }

        /**
         * Updates Lat/Lon inputs based on the map's location value.
         */
        function updateInputsFromMap() {
            /** @type {HTMLTextAreaElement} */
            const locInput = /** @type {any} */ (locationInput);
            const rawValue = locInput.value;
            if (!rawValue?.trim()) {
                /** @type {HTMLInputElement} */ (latInput).value = "";
                /** @type {HTMLInputElement} */ (lonInput).value = "";
                return;
            }

            let lon, lat;
            try {
                if (rawValue.startsWith('{')) {
                    /** @type {{type: string, coordinates: [number, number]}} */
                    const data = JSON.parse(rawValue);
                    if (data.type === 'Point') {
                        [lon, lat] = data.coordinates;
                    }
                } else if (rawValue.toUpperCase().startsWith('POINT')) {
                    const match = rawValue.match(/POINT\s*\(([-\d.]+)\s+([-\d.]+)\)/i);
                    if (match) {
                        lon = parseFloat(match[1]);
                        lat = parseFloat(match[2]);
                    }
                }
            } catch (e) {
                console.debug("Parsing location failed", e);
            }

            if (lon !== undefined && lat !== undefined) {
                const [outLon, outLat] = transformTo4326(lon, lat);
                // Use 8 decimal places to maintain high precision
                /** @type {HTMLInputElement} */ (latInput).value = outLat.toFixed(8).replace(/\.?0+$/, '');
                /** @type {HTMLInputElement} */ (lonInput).value = outLon.toFixed(8).replace(/\.?0+$/, '');
            }
        }

        /**
         * Updates the map based on manual Lat/Lon input values.
         */
        function updateMapFromInputs(shouldCenter = false) {
            const lat = parseFloat(/** @type {HTMLInputElement} */ (latInput).value);
            const lon = parseFloat(/** @type {HTMLInputElement} */ (lonInput).value);

            if (isNaN(lat) || isNaN(lon)) return;

            const wkt = `POINT (${lon} ${lat})`;
            if (/** @type {HTMLTextAreaElement} */ (locationInput).value === wkt) return;

            /** @type {HTMLTextAreaElement} */ (locationInput).value = wkt;
            ['change', 'input'].forEach(evt => locationInput.dispatchEvent(new Event(evt, { bubbles: true })));

            const mapVarName = 'geodjango_' + locationInput.id.replace('id_', '');
            /** @type {GeoDjangoMap|undefined} */
            const mapObject = win[mapVarName] || Object.values(win).find(v => v?.map && typeof v.deserialize === 'function');

            if (!mapObject) return;

            if (typeof mapObject.deserialize === 'function') {
                try {
                    mapObject.deserialize(wkt);
                } catch (e) {}
            }

            if (ol) {
                const actualMap = mapObject.map || mapObject;
                const coords3857 = transformTo3857(lon, lat);
                try {
                    const format = ol.format;
                    /** @type {OLFeature|null} */
                    const feature = format?.WKT 
                        ? new format.WKT().readFeature(wkt, { dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857' })
                        : (ol.Feature && ol.geom?.Point ? new ol.Feature(new ol.geom.Point(coords3857)) : null);

                    if (!feature) return;

                    if (mapObject.featureCollection?.clear) {
                        mapObject.featureCollection.clear();
                        mapObject.featureCollection.push(feature);
                    } else if (mapObject.featureOverlay?.getSource) {
                        const source = mapObject.featureOverlay.getSource();
                        if (source) {
                            source.clear();
                            source.addFeature(feature);
                        }
                    }

                    if (actualMap.getLayers) {
                        actualMap.getLayers().getArray().forEach(layer => {
                            const source = layer.getSource?.();
                            if (source?.addFeature && !source.getTileGrid) {
                                source.clear();
                                source.addFeature(feature.clone());
                            }
                        });
                    }

                    if (shouldCenter && actualMap.getView) {
                        actualMap.getView().setCenter(coords3857);
                    }
                    actualMap.render?.();
                } catch (e) {
                    console.debug("Map manipulation failed", e);
                }
            }

            // Simulate pointer events to ensure the widget recognizes the change
            setTimeout(() => {
                const actualMap = mapObject.map || mapObject;
                if (actualMap?.getPixelFromCoordinate) {
                    const coords3857 = transformTo3857(lon, lat);
                    const pixel = actualMap.getPixelFromCoordinate(coords3857);
                    if (pixel) {
                        ['pointerdown', 'pointerup'].forEach(type => {
                            actualMap.dispatchEvent({
                                type,
                                coordinate: coords3857,
                                pixel,
                                originalEvent: new MouseEvent(type)
                            });
                        });
                    }
                }
            }, 50);
        }

        // Poll for internal location change (e.g., from user clicking a map)
        /** @type {HTMLTextAreaElement} */
        const locInput = /** @type {any} */ (locationInput);
        let lastValue = locInput.value;
        setInterval(() => {
            if (locInput.value !== lastValue) {
                lastValue = locInput.value;
                updateInputsFromMap();
            }
        }, 500);

        const debouncedUpdate = debounce(() => updateMapFromInputs(false), 800);

        [latInput, lonInput].forEach(el => {
            el.addEventListener('input', debouncedUpdate);
            el.addEventListener('change', () => {
                debouncedUpdate.cancel();
                updateMapFromInputs(true);
            });
        });

        // Initial centering for new objects with default coordinates
        setTimeout(() => {
            const lat = parseFloat(/** @type {HTMLInputElement} */ (latInput).value);
            const lon = parseFloat(/** @type {HTMLInputElement} */ (lonInput).value);
            if (lat === 52.2297 && lon === 21.0122 && !locInput.value?.trim()) {
                updateMapFromInputs(true);
            }
        }, 1500);
    }

    function initMapSync() {
        const latInput = document.querySelector('input[id$="latitude"]');
        const lonInput = document.querySelector('input[id$="longitude"]');
        const locationInput = document.querySelector('textarea[id$="location"]');

        if (!latInput || !lonInput || !locationInput) {
            if (retryCount < MAX_RETRIES) {
                retryCount++;
                setTimeout(initMapSync, 1000);
                return;
            }
            // Elements not found after max retries, use MutationObserver
            const observer = new MutationObserver((mutations, obs) => {
                const lat = document.querySelector('input[id$="latitude"]');
                const lon = document.querySelector('input[id$="longitude"]');
                const loc = document.querySelector('textarea[id$="location"]');
                if (lat && lon && loc) {
                    obs.disconnect();
                    setupMapSync(lat, lon, loc);
                }
            });
            observer.observe(document.body, { childList: true, subtree: true });
            return;
        }

        setupMapSync(latInput, lonInput, locationInput);
    }

    if (document.readyState === 'complete') initMapSync();
    else window.addEventListener('load', initMapSync);
})();
