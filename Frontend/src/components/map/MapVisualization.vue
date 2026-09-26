<!-- MapVisualization.vue - Fully Responsive with Buffer Preview -->

<template>
    <div class="map-container flex flex-col h-full bg-gray-900 rounded-lg shadow-inner relative">
        <div id="map" class="map-view flex-grow z-[0]" ref="mapDiv"></div>

        <button v-if="!isFullscreen && !isMonitorMode" @click="enterFullscreen"
            class="fullscreen-btn absolute bottom-4 right-4 z-[70] bg-gray-800 hover:bg-gray-700 text-white p-2 rounded-lg shadow-lg transition-all duration-200 flex items-center gap-2"
            title="Enter Fullscreen">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4">
                </path>
            </svg>
            <span class="text-sm font-medium">Fullscreen</span>
        </button>

        <button v-if="isFullscreen && !isMonitorMode" @click="exitFullscreen"
            class="exit-fullscreen-btn fixed bottom-4 right-4 z-[10000] bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg shadow-lg transition-all duration-200 flex items-center gap-2"
            title="Exit Fullscreen">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            <span class="text-sm font-medium">Exit Fullscreen</span>
        </button>
    </div>
</template>

<script setup>
import { onMounted, ref, nextTick, watch, onBeforeUnmount } from 'vue';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import L from 'leaflet';
import 'leaflet-draw';
import * as turf from '@turf/turf';

const props = defineProps({
    aoisToDisplay: Array,
    accumulatedGeometries: Array, // NEW: Display multi-polygon progress
    isMonitorMode: Boolean,
    alertFeaturesToDisplay: Array,
});

const emit = defineEmits(['aoi-drawn', 'aoi-clicked']);

const map = ref(null);
const drawnItems = ref(null);
const savedAoisLayerGroup = ref(null);
const accumulatedLayerGroup = ref(null); // NEW: Layer for accumulated geometries
const mapDiv = ref(null);
const isFullscreen = ref(false);
const drawControlRef = ref(null);
const alertFeaturesLayerGroup = ref(null);
const tempSatelliteFootprintLayer = ref(null);

const safePatch = (handler) => {
    if (handler && handler.prototype && !handler.prototype._fireCreatedEvent) {
        handler.prototype._fireCreatedEvent = function (layer) {
            this._map.fire(L.Draw.Event.CREATED, { layer: layer, layerType: this.type });
        };
    }
};

const enterFullscreen = () => {
    const container = mapDiv.value.parentElement;
    if (container.requestFullscreen) {
        container.requestFullscreen();
    } else if (container.webkitRequestFullscreen) {
        container.webkitRequestFullscreen();
    } else if (container.msRequestFullscreen) {
        container.msRequestFullscreen();
    }
};

const exitFullscreen = () => {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
    }
};

const handleFullscreenChange = () => {
    isFullscreen.value = !!(document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement);
    if (map.value) {
        setTimeout(() => {
            map.value.invalidateSize();
        }, 100);
    }
};

const disableAllDrawingTools = () => {
    if (!drawControlRef.value || !map.value) return;

    const modes = drawControlRef.value._toolbars.draw._modes;
    Object.values(modes).forEach(mode => {
        if (mode.handler && mode.handler.enabled()) {
            mode.handler.disable();
        }
    });
};



// MapVisualization.vue - FIXED initializeMap function
// Replace your initializeMap function with this:

const initializeMap = () => {
    if (!mapDiv.value) return;

    if (map.value) {
        map.value.remove();
        map.value = null;
    }

    map.value = L.map(mapDiv.value, {
        attributionControl: false,
        dragging: true
    });

    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: false,
        maxZoom: 19,
    });

    const baseLayers = { 'OpenStreetMap': osmLayer };
    osmLayer.addTo(map.value);
    L.control.layers(baseLayers).addTo(map.value);

    // CRITICAL FIX: Initialize layer groups in CORRECT z-index order (bottom to top)
    // Layer at bottom (z-index lowest)
    savedAoisLayerGroup.value = new L.FeatureGroup();
    map.value.addLayer(savedAoisLayerGroup.value);

    // Accumulated geometries (middle layer)
    accumulatedLayerGroup.value = new L.FeatureGroup();
    map.value.addLayer(accumulatedLayerGroup.value);

    // CRITICAL: Alert features MUST be added AFTER AOIs to appear on top
    alertFeaturesLayerGroup.value = new L.FeatureGroup();
    map.value.addLayer(alertFeaturesLayerGroup.value);

    // Drawn items (top layer)
    drawnItems.value = new L.FeatureGroup();
    map.value.addLayer(drawnItems.value);

    if (!props.isMonitorMode) {
        setupDrawingControls();
    }

    if (props.aoisToDisplay && props.aoisToDisplay.length > 0) {
        loadExistingAOIs(props.aoisToDisplay, true);
        setTimeout(() => {
            if (map.value) map.value.invalidateSize();
        }, 50);
    } else {
        navigator.geolocation.getCurrentPosition(
            p => {
                if (map.value) {
                    map.value.setView([p.coords.latitude, p.coords.longitude], 10);
                }
            },
            err => {
                console.warn("Location access denied. Falling back to Kolkata.", err);
                if (map.value) {
                    map.value.setView([22.57, 88.36], 10);
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 5000
            }
        );
    }

    L.DomUtil.addClass(map.value.getPane('tilePane'), 'leaflet-pane-hardware-accel');

    // GeoTIFF satellite bounds focus handler with temporary AOI footprint (PS 2.2.6)
    window.addEventListener('focus-satellite-bounds', (e) => {
        if (map.value && e.detail) {
            const { minLat, minLon, maxLat, maxLon } = e.detail;

            // Remove existing temporary footprint if present
            if (tempSatelliteFootprintLayer.value) {
                map.value.removeLayer(tempSatelliteFootprintLayer.value);
                tempSatelliteFootprintLayer.value = null;
            }

            const bounds = [
                [minLat, minLon],
                [maxLat, maxLon]
            ];

            // Draw tactical temporary AOI swath rectangle
            tempSatelliteFootprintLayer.value = L.rectangle(bounds, {
                color: '#06b6d4',
                weight: 2.5,
                dashArray: '8, 6',
                fillColor: '#0891b2',
                fillOpacity: 0.18,
                className: 'satellite-swath-footprint'
            });

            // Bind tactical tooltip
            tempSatelliteFootprintLayer.value.bindTooltip(
                `🛰️ SATELLITE SCENE AOI SWATH [${minLat.toFixed(3)}°, ${minLon.toFixed(3)}° ↔ ${maxLat.toFixed(3)}°, ${maxLon.toFixed(3)}°] (Click to dismiss)`,
                {
                    permanent: true,
                    direction: 'top',
                    className: 'satellite-swath-tooltip'
                }
            );

            // Dismiss on click
            tempSatelliteFootprintLayer.value.on('click', () => {
                if (tempSatelliteFootprintLayer.value && map.value) {
                    map.value.removeLayer(tempSatelliteFootprintLayer.value);
                    tempSatelliteFootprintLayer.value = null;
                    console.log('[MapViz] 🛰️ Dismissed temporary satellite footprint swath');
                }
            });

            tempSatelliteFootprintLayer.value.addTo(map.value);

            // Fly smoothly to the scene bounds
            map.value.flyToBounds(bounds, {
                padding: [60, 60],
                duration: 1.5,
                maxZoom: 15
            });

            console.log('[MapViz] 🛰️ Displayed temporary satellite AOI swath and focused bounds:', e.detail);
        }
    });
};


const displayAlertFeatures = (features) => {
    console.log('[MapViz] displayAlertFeatures called');
    console.log('[MapViz] alertFeaturesLayerGroup exists?', !!alertFeaturesLayerGroup.value);
    console.log('[MapViz] map exists?', !!map.value);
    console.log('[MapViz] Features received:', features);

    if (!alertFeaturesLayerGroup.value) {
        console.error('[MapViz] alertFeaturesLayerGroup is null!');
        return;
    }

    if (!map.value) {
        console.error('[MapViz] map is null!');
        return;
    }

    // Clear existing layers
    alertFeaturesLayerGroup.value.clearLayers();
    console.log('[MapViz] Cleared existing alert features');
    
    if (!features || features.length === 0) {
        console.log('[MapViz] No alert features to display (empty or null)');
        return;
    }

    console.log('[MapViz] Displaying', features.length, 'alert features');

    let successCount = 0;
    let failCount = 0;

    features.forEach((featureData, index) => {
        try {
            console.log(`[MapViz] Processing feature ${index + 1}:`, featureData);

            // Handle different GeoJSON structures
            let geoJsonToDisplay = featureData;

            if (featureData.type === 'Feature' || featureData.type === 'FeatureCollection') {
                geoJsonToDisplay = featureData;
                console.log(`[MapViz] Feature ${index + 1} is already a ${featureData.type}`);
            }
            else if (featureData.type && featureData.coordinates) {
                geoJsonToDisplay = {
                    type: 'Feature',
                    geometry: featureData,
                    properties: {}
                };
                console.log(`[MapViz] Feature ${index + 1} wrapped as Feature from Geometry`);
            }
            else {
                console.warn('[MapViz] Unrecognized GeoJSON structure:', featureData);
                failCount++;
                return;
            }

            // Create the layer with VERY VISIBLE styling
            const layer = L.geoJSON(geoJsonToDisplay, {
                style: {
                    color: '#ffc107', 
                    weight: 6,           
                    opacity: 1,              
                    fillColor: '#ffc107', 
                    fillOpacity: 0.5,        
                    dashArray: '10, 5',      
                    className: 'alert-feature-layer'  
                },
                pointToLayer: function (geoJsonPoint, latlng) {
                    console.log(`[MapViz] Creating point marker at [${latlng.lat}, ${latlng.lng}]`);
                    return L.circleMarker(latlng, {
                        radius: 12,          
                        fillColor: "#ffc107",
                        color: "#ff9800",
                        weight: 4,           
                        opacity: 1,
                        fillOpacity: 0.8,
                        className: 'alert-point-marker'
                    });
                },
                onEachFeature: (feature, layer) => {
                    const tooltipText = `🚨 Alert ${index + 1}`;
                    layer.bindTooltip(tooltipText, { 
                        permanent: true, 
                        direction: 'center',
                        className: 'alert-feature-tooltip'
                    });

                    if (feature.properties && Object.keys(feature.properties).length > 0) {
                        const popupContent = '<div style="color: black;">' +
                            Object.entries(feature.properties)
                                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                                .join('<br>') +
                            '</div>';
                        layer.bindPopup(popupContent);
                    }

                    layer.on('click', () => {
                        console.log(`[MapViz] Alert feature ${index + 1} clicked`);
                    });
                }
            });

            layer.addTo(alertFeaturesLayerGroup.value);
            successCount++;
            

            try {
                const bounds = layer.getBounds();
                console.log(`[MapViz] Feature ${index + 1} bounds:`, {
                    north: bounds.getNorth(),
                    south: bounds.getSouth(),
                    east: bounds.getEast(),
                    west: bounds.getWest()
                });
            } catch (e) {
                console.log(`[MapViz] Could not get bounds for feature ${index + 1} (might be a point)`);
            }

        } catch (e) {
            console.error(`[MapViz] ❌ Failed to display alert feature ${index}:`, e);
            console.error('[MapViz] Failed feature data:', featureData);
            failCount++;
        }
    });

    console.log(`[MapViz] Summary: ${successCount} succeeded, ${failCount} failed`);
    console.log('[MapViz] Total layers in alertFeaturesLayerGroup:', 
                alertFeaturesLayerGroup.value.getLayers().length);

    // CRITICAL: Bring alert features to front
    if (alertFeaturesLayerGroup.value.getLayers().length > 0) {
        alertFeaturesLayerGroup.value.bringToFront();
        console.log('[MapViz] Brought alert features to front');
    }

    try {
        if (alertFeaturesLayerGroup.value.getLayers().length > 0) {
            const bounds = alertFeaturesLayerGroup.value.getBounds();
            console.log('[MapViz] Alert features bounds:', {
                north: bounds.getNorth(),
                south: bounds.getSouth(),
                east: bounds.getEast(),
                west: bounds.getWest(),
                isValid: bounds.isValid()
            });

            if (bounds && bounds.isValid()) {
                // FIT BOUNDS with generous padding
                map.value.fitBounds(bounds, { 
                    padding: [100, 100],  
                    maxZoom: 14        
                });
                console.log('[MapViz] ✅ Map fitted to alert features bounds');
            }
        } else {
            console.warn('[MapViz] No layers added to fit bounds');
        }
    } catch (e) {
        console.error('[MapViz] ❌ Could not fit bounds to alert features:', e);
    }
};

const setupDrawingControls = () => {
    safePatch(L.Draw.Polygon);
    safePatch(L.Draw.Polyline);
    safePatch(L.Draw.Marker);

    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems.value,
            edit: false,
            remove: false
        },
        draw: {
            polygon: true,
            polyline: true,
            marker: true,
            rectangle: false,
            circle: false,
            circlemarker: false
        }
    });
    drawControlRef.value = drawControl;
    map.value.addControl(drawControl);

    map.value.on(L.Draw.Event.DRAWSTOP, (e) => {
        // User cancelled drawing - do nothing

        disableAllDrawingTools();
        initializeMap();
    });

    map.value.on(L.Draw.Event.CREATED, (e) => {
        const layer = e.layer;
        const layerType = e.layerType;

        drawnItems.value.addLayer(layer);

        const geoJsonFeature = layer.toGeoJSON();
        let geometryType;

        switch (layerType) {
            case 'marker':
                geometryType = 'Point';
                break;
            case 'polyline':
                geometryType = 'LineString';
                break;
            case 'polygon':
            default:
                geometryType = 'Polygon';
                break;
        }

        const aoiData = {
            geometry: geoJsonFeature.geometry,
            geometryType: geometryType,
            coordinates: geoJsonFeature.geometry.coordinates,
        };

        emit('aoi-drawn', aoiData);
    });
};

// NEW: Visualize accumulated geometries before finalization
const visualizeAccumulatedGeometries = () => {
    if (!accumulatedLayerGroup.value || !props.accumulatedGeometries) return;

    accumulatedLayerGroup.value.clearLayers();

    props.accumulatedGeometries.forEach((item, index) => {
        const layer = L.geoJSON(item.geometry, {
            style: {
                color: '#10b981', // Green for accumulated
                weight: 3,
                opacity: 0.9,
                fillColor: '#10b981',
                fillOpacity: 0.2,
                dashArray: '5, 10' // Dashed line to differentiate
            }
        });

        layer.bindTooltip(`Part ${index + 1}`, {
            permanent: true,
            direction: 'center',
            className: 'accumulated-tooltip'
        });

        layer.addTo(accumulatedLayerGroup.value);

        // Add buffer visualization if applicable
        if (item.bufferDistance && item.type !== 'Polygon') {
            if (item.type === 'Point') {
                const [lng, lat] = item.geometry.coordinates;
                L.circle([lat, lng], {
                    radius: item.bufferDistance,
                    color: '#00BFFF',
                    fillColor: '#3399ff',
                    fillOpacity: 0.15,
                    weight: 1,
                    dashArray: '3, 6'
                }).addTo(accumulatedLayerGroup.value);
            } else if (item.type === 'LineString') {
                const buffered = turf.buffer(item.geometry, item.bufferDistance, { units: 'meters' });
                L.geoJSON(buffered, {
                    style: {
                        color: '#00BFFF',
                        weight: 1,
                        fillColor: '#3399ff',
                        fillOpacity: 0.15,
                        dashArray: '3, 6'
                    }
                }).addTo(accumulatedLayerGroup.value);
            }
        }
    });
};



const loadExistingAOIs = (aois, shouldFitBounds = false) => {
    if (!savedAoisLayerGroup.value) return;

    savedAoisLayerGroup.value.clearLayers();

    if (!aois || aois.length === 0) return;

    const validAois = aois.filter(aoi => {
        const geom = aoi.geomGeoJson || aoi.geometry;
        if (!geom) {
            console.warn(`AOI ${aoi.name} has no geometry, skipping`);
            return false;
        }

        if (geom.type === 'GeometryCollection') {
            if (!geom.geometries || geom.geometries.length === 0) {
                console.warn(`AOI ${aoi.name} has empty GeometryCollection, skipping`);
                return false;
            }
            return geom.geometries.every(g => {
                if (!g.coordinates || g.coordinates.length === 0) {
                    console.warn(`Invalid coordinates in GeometryCollection for ${aoi.name}`);
                    return false;
                }
                return true;
            });
        } else {
            if (!geom.coordinates || geom.coordinates.length === 0) {
                console.warn(`AOI ${aoi.name} has invalid coordinates, skipping`);
                return false;
            }
        }

        return true;
    });

    if (validAois.length === 0) {
        console.warn('No valid AOIs to display');
        return;
    }

    const aoiLayers = validAois.map(aoi => {
        try {
            // Main AOI layer (buffered polygon)
            const layer = L.geoJSON(aoi.geomGeoJson || aoi.geometry, {
                style: {
                    color: props.isMonitorMode ? '#10b981' : '#f97316',
                    weight: 3,
                    opacity: 0.8,
                    fillColor: props.isMonitorMode ? '#10b981' : '#f97316',
                    fillOpacity: 0.3
                },
                onEachFeature: (feature, layer) => {
                    layer.options.aoiDetails = aoi;

                    layer.bindTooltip(`AOI: ${aoi.name}`, {
                        permanent: false,
                        direction: 'top'
                    });

                    if (props.isMonitorMode) {
                        layer.on('click', (e) => {
                            emit('aoi-clicked', aoi);
                            map.value.setView(e.latlng, map.value.getZoom());
                        });
                    }

                    // CRITICAL: Display original coordinates from geom_properties
                    const originalCoordinates = aoi.geomProperties?.originalCoordinates || 
                                               aoi.geom_properties?.originalCoordinates;

                    if (originalCoordinates && Array.isArray(originalCoordinates)) {
                        // Display original points/lines
                        originalCoordinates.forEach((original, idx) => {
                            try {
                                if (original.type === 'Point') {
                                    const [lng, lat] = original.coordinates;
                                    if (typeof lng === 'number' && typeof lat === 'number') {
                                        // Display original point
                                        L.circleMarker([lat, lng], {
                                            radius: 6,
                                            color: '#FF0000',
                                            fillColor: '#FF0000',
                                            fillOpacity: 0.8,
                                            weight: 2
                                        }).addTo(savedAoisLayerGroup.value)
                                          .bindTooltip(`Original Point ${idx + 1}`, { permanent: false });

                                        // Display buffer circle
                                        if (original.buffer) {
                                            L.circle([lat, lng], {
                                                radius: original.buffer,
                                                color: '#FF0000',
                                                fillColor: '#FF0000',
                                                fillOpacity: 0.15,
                                                weight: 1,
                                                dashArray: '3, 6'
                                            }).addTo(savedAoisLayerGroup.value);
                                        }
                                    }
                                } else if (original.type === 'LineString') {
                                    // Display original line
                                    L.geoJSON({
                                        type: 'LineString',
                                        coordinates: original.coordinates
                                    }, {
                                        style: {
                                            color: '#FF0000',
                                            weight: 3,
                                            opacity: 0.8
                                        }
                                    }).addTo(savedAoisLayerGroup.value)
                                      .bindTooltip(`Original Line ${idx + 1}`, { permanent: false });

                                    // Display buffer around line
                                    if (original.buffer) {
                                        const buffered = turf.buffer({
                                            type: 'LineString',
                                            coordinates: original.coordinates
                                        }, original.buffer, { units: 'meters' });
                                        
                                        L.geoJSON(buffered, {
                                            style: {
                                                color: '#FF0000',
                                                weight: 1,
                                                fillColor: '#FF0000',
                                                fillOpacity: 0.15,
                                                dashArray: '3, 6'
                                            }
                                        }).addTo(savedAoisLayerGroup.value);
                                    }
                                }
                            } catch (coordError) {
                                console.warn(`Failed to display original coordinates for index ${idx}:`, coordError);
                            }
                        });
                    } else {
                        // Legacy format: single buffer (backward compatibility)
                        const bufferConfig = aoi.geomProperties?.bufferConfig || aoi.geom_properties?.bufferConfig;
                        
                        if (bufferConfig) {
                            bufferConfig.forEach((config, idx) => {
                                if (!config.buffer || config.type === 'Polygon') return;

                                try {
                                    const geom = aoi.geometry?.geometries
                                        ? aoi.geometry.geometries[idx]
                                        : aoi.geometry;

                                    if (!geom || !geom.coordinates) {
                                        console.warn(`No valid geometry for buffer at index ${idx}`);
                                        return;
                                    }

                                    if (config.type === 'Point') {
                                        const [lng, lat] = geom.coordinates;
                                        if (typeof lng === 'number' && typeof lat === 'number') {
                                            L.circle([lat, lng], {
                                                radius: config.buffer,
                                                color: '#00BFFF',
                                                fillColor: '#3399ff',
                                                fillOpacity: 0.3,
                                                weight: 2,
                                                dashArray: '5, 5'
                                            }).addTo(savedAoisLayerGroup.value);
                                        }
                                    } else if (config.type === 'LineString') {
                                        const buffered = turf.buffer(geom, config.buffer, { units: 'meters' });
                                        L.geoJSON(buffered, {
                                            style: {
                                                color: '#00BFFF',
                                                weight: 2,
                                                fillColor: '#3399ff',
                                                fillOpacity: 0.3,
                                                dashArray: '5, 5'
                                            }
                                        }).addTo(savedAoisLayerGroup.value);
                                    }
                                } catch (bufferError) {
                                    console.warn(`Failed to create buffer for index ${idx}:`, bufferError);
                                }
                            });
                        } else if (aoi.geomProperties?.buffer && aoi.geomProperties?.originalType !== 'Polygon') {
                            // Single geometry buffer (legacy format)
                            try {
                                const geom = aoi.geomGeoJson || aoi.geometry;
                                const buffer = aoi.geomProperties.buffer;

                                if (aoi.geomProperties.originalType === 'Point') {
                                    const [lng, lat] = geom.coordinates;
                                    if (typeof lng === 'number' && typeof lat === 'number') {
                                        L.circle([lat, lng], {
                                            radius: buffer,
                                            color: '#00BFFF',
                                            fillColor: '#3399ff',
                                            fillOpacity: 0.3,
                                            weight: 2,
                                            dashArray: '5, 5'
                                        }).addTo(savedAoisLayerGroup.value);
                                    }
                                } else if (aoi.geomProperties.originalType === 'LineString') {
                                    const buffered = turf.buffer(geom, buffer, { units: 'meters' });
                                    L.geoJSON(buffered, {
                                        style: {
                                            color: '#00BFFF',
                                            weight: 2,
                                            fillColor: '#3399ff',
                                            fillOpacity: 0.3,
                                            dashArray: '5, 5'
                                        }
                                    }).addTo(savedAoisLayerGroup.value);
                                }
                            } catch (bufferError) {
                                console.warn(`Failed to create single buffer:`, bufferError);
                            }
                        }
                    }
                }
            });
            return layer;
        } catch (layerError) {
            console.error(`Failed to create layer for AOI ${aoi.name}:`, layerError);
            return null;
        }
    }).filter(layer => layer !== null);

    if (aoiLayers.length === 0) {
        console.warn('No valid layers created');
        return;
    }

    const combinedAoiLayer = L.featureGroup(aoiLayers).addTo(savedAoisLayerGroup.value);

    if (!shouldFitBounds) return;

    try {
        if (combinedAoiLayer.getLayers().length > 0) {
            const bounds = combinedAoiLayer.getBounds();
            if (bounds && bounds.isValid()) {
                map.value.fitBounds(bounds, { padding: [30, 30] });
            } else {
                console.warn('Invalid bounds, setting default view');
                map.value.setView([21.5937, 80.9629], 5);
            }
        }
    } catch (e) {
        console.warn("Could not fit bounds:", e);
        map.value.setView([21.5937, 80.9629], 5);
    }
};


const clearUnsavedLayer = () => {
    if (drawnItems.value) {
        drawnItems.value.clearLayers();
    }
};

const clearAccumulatedGeometries = () => {
    if (accumulatedLayerGroup.value) {
        accumulatedLayerGroup.value.clearLayers();
    }
};

defineExpose({
    clearUnsavedLayer,
    clearAccumulatedGeometries,
    drawnItems,
    map
});

onMounted(() => {
    nextTick(() => {
        initializeMap();
        setTimeout(() => {
            if (map.value) map.value.invalidateSize();
        }, 10);

        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('msfullscreenchange', handleFullscreenChange);
    });
});

onBeforeUnmount(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
    document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.removeEventListener('msfullscreenchange', handleFullscreenChange);

    if (map.value) {
        map.value.remove();
        map.value = null;
    }
});

// MapVisualization.vue - FIXED watch for alert features
// Replace the existing watch with this version:

watch(() => props.alertFeaturesToDisplay, (newFeatures, oldFeatures) => {
    console.log('[MapViz] Watch triggered - alertFeaturesToDisplay changed');
    console.log('[MapViz] Old features:', oldFeatures?.length || 0);
    console.log('[MapViz] New features:', newFeatures?.length || 0);
    console.log('[MapViz] Map ready?', !!map.value);
    console.log('[MapViz] Alert layer ready?', !!alertFeaturesLayerGroup.value);
    
    // Only process if we have new features and map is ready
    if (!newFeatures || newFeatures.length === 0) {
        console.log('[MapViz] No features to display, clearing layer');
        if (alertFeaturesLayerGroup.value) {
            alertFeaturesLayerGroup.value.clearLayers();
        }
        return;
    }
    
    if (map.value && alertFeaturesLayerGroup.value) {
        console.log('[MapViz] Calling displayAlertFeatures with', newFeatures.length, 'features');
        displayAlertFeatures(newFeatures);
    } else {
        console.error('[MapViz] Cannot display - map or layer not ready!');
        console.log('[MapViz] Will retry after 500ms...');
        
        // Retry after a delay (map might still be initializing)
        setTimeout(() => {
            if (map.value && alertFeaturesLayerGroup.value && newFeatures.length > 0) {
                console.log('[MapViz] Retry: Calling displayAlertFeatures');
                displayAlertFeatures(newFeatures);
            } else {
                console.error('[MapViz] Retry failed - still not ready');
            }
        }, 500);
    }
}, { deep: true, immediate: true });

// Watch accumulated geometries and visualize them
watch(() => props.accumulatedGeometries, () => {
    if (map.value) {
        visualizeAccumulatedGeometries();
    }
}, { deep: true, immediate: true });

watch(() => props.aoisToDisplay, (newAois) => {
    if (map.value && newAois) {
        disableAllDrawingTools();
        loadExistingAOIs(newAois, false);
        // initializeMap();
    }
}, { deep: true, immediate: true });

watch(() => props.aoisToDisplay?.length, (newLength, oldLength) => {
    if (map.value && newLength !== oldLength) {
        const shouldFit = newLength === 1 || (oldLength === 0 && newLength > 0);
        loadExistingAOIs(props.aoisToDisplay, shouldFit);
    }
});
</script>

<style scoped>
:deep(.accumulated-tooltip) {
    background-color: #10b981;
    border: none;
    color: white;
    font-weight: bold;
    padding: 4px 8px;
    border-radius: 4px;
}

.map-view {
    min-height: 50vh;
}

.fullscreen-btn,
.exit-fullscreen-btn {
    backdrop-filter: blur(10px);
}

:global(.leaflet-draw-toolbar a) {
    background-color: #ffffff !important;
    color: white !important;
}

:global(.leaflet-draw-toolbar a:hover) {
    background-color: #4b5563 !important;
}

:global(.leaflet-control-container) {
    z-index: 9 !important;
}

/* Fullscreen container layout fix */
:global(.leaflet-container:fullscreen) {
    background: #000;
    width: 100vw !important;
    height: 100vh !important;
}

/* Chrome & Safari fullscreen */
:global(.leaflet-container:-webkit-full-screen) {
    background: #000;
    width: 100vw !important;
    height: 100vh !important;
}

/* Ensure map container takes full space in fullscreen */
:global(.map-container:fullscreen),
:global(.map-container:-webkit-full-screen) {
    width: 100vw !important;
    height: 100vh !important;
}

:global(.map-container:fullscreen .map-view),
:global(.map-container:-webkit-full-screen .map-view) {
    width: 100% !important;
    height: 100% !important;
    min-height: 100vh !important;
}

:deep(.alert-feature-tooltip) {
    background-color: #ffc107 !important;
    border: 2px solid #ff9800 !important;
    color: #000 !important;
    font-weight: bold !important;
    padding: 6px 10px !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 8px rgba(255, 193, 7, 0.5) !important;
}

:deep(.alert-feature-tooltip::before) {
    border-top-color: #ff9800 !important;
}

/* Ensure alert features are above AOIs but below controls */
:deep(.leaflet-overlay-pane) {
    z-index: 400 !important;
}

/* Highlight effect on hover */
:deep(.leaflet-interactive:hover) {
    stroke-width: 6 !important;
    filter: brightness(1.2);
}

/* Add these styles to MapVisualization.vue <style scoped> section */

/* CRITICAL: Ensure alert features are ALWAYS on top */
:deep(.alert-feature-layer) {
    z-index: 1000 !important;
    pointer-events: all !important;
}

:deep(.alert-point-marker) {
    z-index: 1001 !important;
    pointer-events: all !important;
}

/* Enhanced tooltip styling - ALWAYS VISIBLE */
:deep(.alert-feature-tooltip) {
    background-color: #ffc107 !important;
    border: 3px solid #ff9800 !important;
    color: #000 !important;
    font-weight: bold !important;
    font-size: 14px !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(255, 193, 7, 0.8) !important;
    opacity: 1 !important;
    z-index: 10000 !important;
}

:deep(.alert-feature-tooltip::before) {
    border-top-color: #ff9800 !important;
}

/* Make alert feature paths highly visible */
:deep(.leaflet-interactive.alert-feature-layer) {
    stroke: #ffc107 !important;
    stroke-width: 6 !important;
    stroke-opacity: 1 !important;
    fill: #ffc107 !important;
    fill-opacity: 0.5 !important;
    stroke-dasharray: 10, 5 !important;
    z-index: 1000 !important;
}

/* Point markers for alerts */
:deep(.alert-point-marker) {
    fill: #ffc107 !important;
    stroke: #ff9800 !important;
    stroke-width: 4 !important;
    fill-opacity: 0.8 !important;
    stroke-opacity: 1 !important;
}

/* Ensure alert layer pane is on top */
:deep(.leaflet-overlay-pane) {
    z-index: 400 !important;
}

:deep(.leaflet-marker-pane) {
    z-index: 600 !important;
}

:deep(.leaflet-tooltip-pane) {
    z-index: 650 !important;
}

:deep(.leaflet-popup-pane) {
    z-index: 700 !important;
}



/* Highlight effect on hover - MORE VISIBLE */
:deep(.leaflet-interactive:hover) {
    stroke-width: 8 !important;
    filter: brightness(1.3) !important;
    cursor: pointer !important;
}

/* Debug border - you can remove this after testing */
:deep(.leaflet-overlay-pane svg) {
    outline: 2px dashed rgba(255, 0, 0, 0.3);
}

/* Enhanced visibility for buffer preview */

/* Satellite Swath Footprint Temporary AOI (PS 2.2.6) */
:deep(.satellite-swath-footprint) {
    filter: drop-shadow(0 0 10px rgba(6, 182, 212, 0.55));
    cursor: pointer;
}

:deep(.satellite-swath-tooltip) {
    background: rgba(15, 23, 42, 0.95) !important;
    border: 1px solid #06b6d4 !important;
    color: #67e8f9 !important;
    font-family: monospace !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 4px 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6) !important;
}
</style>