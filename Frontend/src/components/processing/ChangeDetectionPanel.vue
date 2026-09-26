<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';
import { ApiClient } from '@/api/backendAPIendpoint.js';

const apiClient = ApiClient.getInstance();


// ============================================================
// PROPS
// ============================================================

const props = defineProps({
    subscriptionId: {
        type: [Number, String],
        default: 1,
    },
});


// ============================================================
// MINIMIZE / RESTORE
// ============================================================

const isMinimized = ref(false);

const toggleMinimize = () => {
    isMinimized.value = !isMinimized.value;
};


// ============================================================
// DRAGGABLE PANEL
// ============================================================

const panelX = ref(0);
const panelY = ref(0);

const isDragging = ref(false);

const dragStartX = ref(0);
const dragStartY = ref(0);

const startPanelX = ref(0);
const startPanelY = ref(0);


// ============================================================
// START DRAG
// ============================================================

const startDrag = (event) => {

    // Only left mouse button
    if (event.button !== 0) {
        return;
    }

    // Do not start dragging if a button was clicked
    if (event.target.closest('button')) {
        return;
    }

    isDragging.value = true;

    dragStartX.value = event.clientX;
    dragStartY.value = event.clientY;

    startPanelX.value = panelX.value;
    startPanelY.value = panelY.value;

    // Capture pointer so dragging continues smoothly
    event.currentTarget.setPointerCapture(
        event.pointerId
    );
};


// ============================================================
// HANDLE DRAG
// ============================================================

const handleDrag = (event) => {

    if (!isDragging.value) {
        return;
    }

    const deltaX =
        event.clientX - dragStartX.value;

    const deltaY =
        event.clientY - dragStartY.value;

    panelX.value =
        startPanelX.value + deltaX;

    panelY.value =
        startPanelY.value + deltaY;
};


// ============================================================
// STOP DRAG
// ============================================================

const stopDrag = (event) => {

    if (!isDragging.value) {
        return;
    }

    isDragging.value = false;

    try {

        if (
            event.currentTarget.hasPointerCapture(
                event.pointerId
            )
        ) {

            event.currentTarget.releasePointerCapture(
                event.pointerId
            );
        }

    } catch {
        // Ignore pointer capture errors
    }
};


// ============================================================
// FILE STATE
// ============================================================

const t1File = ref(null);
const t2File = ref(null);

const t1Preview = ref(null);
const t2Preview = ref(null);

const isProcessing = ref(false);

const errorMessage = ref('');

const result = ref(null);

const selectedChannel = ref('structural');

const channelOptions = [
    { id: 'structural', label: '🏗️ Structural', name: 'Structural DL (Siamese U-Net)', color: 'text-cyan-400', desc: 'Buildings & Military Fortifications' },
    { id: 'vegetation', label: '🌿 Vegetation', name: 'Vegetation NDVI / VARI', color: 'text-emerald-400', desc: 'Clearance, Logging & Regrowth' },
    { id: 'pixel_diff', label: '🔍 Pixel Diff', name: 'Tactical Surface Anomaly', color: 'text-amber-400', desc: 'Surface Anomalies & Vehicle Activity' },
];

const activeChannelInfo = computed(() => {
    return channelOptions.find(opt => opt.id === selectedChannel.value) || channelOptions[0];
});

const isT1Tiff = computed(() => {
    return Boolean(t1File.value?.name && t1File.value.name.match(/\.(tif|tiff|geotiff)$/i));
});

const isT2Tiff = computed(() => {
    return Boolean(t2File.value?.name && t2File.value.name.match(/\.(tif|tiff|geotiff)$/i));
});

const geotiffMeta = computed(() => {
    return result.value?.geotiff_metadata || result.value?.ml_result?.geotiff_metadata || null;
});

const focusMapOnGeoTIFF = () => {
    if (geotiffMeta.value?.wgs84_bounds) {
        const bounds = geotiffMeta.value.wgs84_bounds; // [min_lon, min_lat, max_lon, max_lat]
        window.dispatchEvent(new CustomEvent('focus-satellite-bounds', {
            detail: {
                minLat: bounds[1],
                minLon: bounds[0],
                maxLat: bounds[3],
                maxLon: bounds[2]
            }
        }));
    }
};


// ============================================================
// PREVIEW CLEANUP
// ============================================================

const revokePreview = (url) => {

    if (url) {
        URL.revokeObjectURL(url);
    }

};


// ============================================================
// T1 FILE SELECTION
// ============================================================

const handleT1Change = (event) => {

    const file =
        event.target.files?.[0] || null;

    // Remove old preview
    revokePreview(t1Preview.value);

    t1File.value = file;

    // Create local preview
    t1Preview.value = file
        ? URL.createObjectURL(file)
        : null;

    // New image means old result is no longer valid
    result.value = null;

    errorMessage.value = '';
};


// ============================================================
// T2 FILE SELECTION
// ============================================================

const handleT2Change = (event) => {

    const file =
        event.target.files?.[0] || null;

    // Remove old preview
    revokePreview(t2Preview.value);

    t2File.value = file;

    // Create local preview
    t2Preview.value = file
        ? URL.createObjectURL(file)
        : null;

    // New image means old result is no longer valid
    result.value = null;

    errorMessage.value = '';
};


// ============================================================
// CLEANUP PREVIEWS
// ============================================================

onBeforeUnmount(() => {

    revokePreview(t1Preview.value);
    revokePreview(t2Preview.value);

});


// ============================================================
// BUTTON STATE
// ============================================================

const canProcess = computed(() => {

    return (
        t1File.value !== null &&
        t2File.value !== null &&
        !isProcessing.value
    );

});


// ============================================================
// RUN CHANGE DETECTION
// ============================================================

const runChangeDetection = async () => {

    if (!t1File.value || !t2File.value) {

        errorMessage.value =
            'Please select both T1 and T2 images.';

        return;
    }

    errorMessage.value = '';

    result.value = null;

    isProcessing.value = true;

    try {

        console.log(
            '[ChangeDetection] Sending T1/T2 to backend...'
        );

        const response =
            await apiClient.detectChange(
                props.subscriptionId,
                t1File.value,
                t2File.value,
                selectedChannel.value
            );

        console.log(
            '[ChangeDetection] Result:',
            response
        );

        result.value = response;

        // If GeoTIFF web previews were generated, update previews for browser display
        const mlRes = response.ml_result || response;
        if (mlRes?.t1_preview) {
            t1Preview.value = mlRes.t1_preview;
        }
        if (mlRes?.t2_preview) {
            t2Preview.value = mlRes.t2_preview;
        }

    } catch (error) {

        console.error(
            '[ChangeDetection] Failed:',
            error
        );

        errorMessage.value =
            error.response?.data?.error ||
            error.message ||
            'Change detection failed.';

    } finally {

        isProcessing.value = false;

    }
};


// ============================================================
// RESULT DATA
// ============================================================

const changeDetection = computed(() => {

    return (
        result.value?.ml_result?.change_detection ||
        null
    );

});


const severity = computed(() => {

    return changeDetection.value?.severity || '';

});


const changePercentage = computed(() => {

    return (
        changeDetection.value?.change_percentage ??
        null
    );

});


const numberOfRegions = computed(() => {

    return (
        changeDetection.value?.number_of_regions ??
        0
    );

});


// ============================================================
// OVERLAY IMAGE
// ============================================================

const overlayImage = computed(() => {

    return (
        result.value?.ml_result?.overlay_image ||
        result.value?.overlay_image ||
        null
    );

});


// ============================================================
// SEVERITY STYLE
// ============================================================

const severityClass = computed(() => {

    switch (severity.value) {

        case 'CRITICAL':
            return 'text-red-500';

        case 'HIGH':
            return 'text-orange-400';

        case 'MEDIUM':
            return 'text-yellow-400';

        case 'LOW':
            return 'text-green-400';

        default:
            return 'text-gray-300';

    }

});

</script>


<template>

    <!-- ======================================================
         MAIN PANEL
         ====================================================== -->

    <div
        class="change-detection-panel
               bg-gray-900/95
               border border-cyan-500/40
               rounded-xl
               shadow-2xl
               p-4
               text-white"
        :class="{
            'is-minimized': isMinimized
        }"
        :style="{
            transform:
                `translate(${panelX}px, ${panelY}px)`
        }"
    >

        <!-- ==================================================
             HEADER / DRAG HANDLE
             ================================================== -->

        <div
            class="panel-drag-handle
                   flex
                   items-center
                   justify-between
                   gap-2"
            :class="{
                'mb-4': !isMinimized
            }"
            @pointerdown.prevent="startDrag"
            @pointermove="handleDrag"
            @pointerup="stopDrag"
            @pointercancel="stopDrag"
        >

            <!-- LEFT -->
            <div
                class="flex
                       items-center
                       gap-2
                       min-w-0"
            >

                <!-- Drag icon -->
                <svg
                    class="w-4 h-4
                           text-gray-500
                           flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M8 7h8M8 12h8M8 17h8"
                    />
                </svg>


                <div class="min-w-0">

                    <h2
                        class="text-lg
                               font-bold
                               text-cyan-300
                               truncate"
                    >
                        Satellite Change Detection
                    </h2>


                    <p
                        v-if="!isMinimized"
                        class="text-xs
                               font-semibold
                               mt-1"
                        :class="activeChannelInfo.color"
                    >
                        {{ activeChannelInfo.name }}
                    </p>

                </div>

            </div>


            <!-- RIGHT -->
            <div
                class="flex
                       items-center
                       gap-2
                       flex-shrink-0"
            >

                <!-- Subscription -->
                <div
                    v-if="!isMinimized"
                    class="text-xs
                           px-2
                           py-1
                           rounded
                           bg-cyan-900/40
                           text-cyan-300"
                >
                    Subscription {{ subscriptionId }}
                </div>


                <!-- Minimize / Restore -->
                <button
                    type="button"
                    @pointerdown.stop
                    @click.stop="toggleMinimize"
                    class="w-7
                           h-7
                           flex
                           items-center
                           justify-center
                           rounded-md
                           text-gray-300
                           hover:text-white
                           hover:bg-gray-700
                           transition"
                    :title="
                        isMinimized
                            ? 'Restore panel'
                            : 'Minimize panel'
                    "
                >

                    <!-- MINUS -->
                    <svg
                        v-if="!isMinimized"
                        class="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M5 12h14"
                        />
                    </svg>


                    <!-- PLUS -->
                    <svg
                        v-else
                        class="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M12 5v14M5 12h14"
                        />
                    </svg>

                </button>

            </div>

        </div>


        <!-- ==================================================
             PANEL CONTENT
             ================================================== -->

        <div v-if="!isMinimized">


            <!-- ==================================================
                 CHANNEL SELECTOR
                 ================================================== -->
            <div class="mb-3">
                <label class="block text-xs font-semibold text-gray-300 mb-1.5">
                    Detection Model / Channel
                </label>
                <div class="grid grid-cols-3 gap-1.5 p-1 bg-gray-800/90 rounded-lg border border-gray-700">
                    <button
                        v-for="opt in channelOptions"
                        :key="opt.id"
                        type="button"
                        @click="selectedChannel = opt.id"
                        class="py-1.5 px-1 rounded-md text-[11px] sm:text-xs font-medium transition text-center truncate"
                        :class="selectedChannel === opt.id
                            ? 'bg-cyan-600 text-white shadow-md'
                            : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/60'"
                        :title="opt.desc"
                    >
                        {{ opt.label }}
                    </button>
                </div>
            </div>


            <!-- ==================================================
                 T1 + T2 PREVIEWS
                 ================================================== -->

            <div
                class="grid
                       grid-cols-2
                       gap-3
                       mb-4"
            >

                <!-- =================================================
                     T1
                     ================================================= -->

                <div>

                    <div
                        class="text-xs
                               font-semibold
                               text-gray-300
                               mb-2"
                    >
                        T1 — Earlier
                    </div>


                    <!-- Preview -->
                    <div
                        class="preview-box
                               bg-gray-800
                               border
                               border-gray-700
                               rounded-lg
                               overflow-hidden"
                    >

                        <div
                            v-if="isT1Tiff && !t1Preview"
                            class="preview-placeholder flex flex-col items-center justify-center p-2 text-center bg-cyan-950/40 border border-cyan-500/30 h-full"
                        >
                            <span class="text-2xl mb-1">🛰️</span>
                            <span class="text-[11px] font-bold text-cyan-300">GeoTIFF (.tif)</span>
                            <span class="text-[9px] text-gray-400">16-bit Multispectral</span>
                        </div>

                        <img
                            v-else-if="t1Preview"
                            :src="t1Preview"
                            alt="T1 satellite image"
                            class="preview-image"
                        />

                        <div
                            v-else
                            class="preview-placeholder"
                        >
                            <span>T1</span>
                        </div>

                    </div>


                    <!-- File input -->
                    <input
                        type="file"
                        accept=".jpg,.jpeg,.png,.tif,.tiff,image/jpeg,image/png,image/tiff"
                        @change="handleT1Change"
                        class="mt-2
                               w-full
                               text-xs
                               text-gray-300
                               file:mr-2
                               file:py-1.5
                               file:px-2.5
                               file:rounded-md
                               file:border-0
                               file:bg-cyan-700
                               file:text-white
                               hover:file:bg-cyan-600"
                    />


                    <p
                        v-if="t1File"
                        class="text-[11px]
                               text-gray-400
                               mt-1
                               truncate"
                        :title="t1File.name"
                    >
                        {{ t1File.name }}
                    </p>

                </div>


                <!-- =================================================
                     T2
                     ================================================= -->

                <div>

                    <div
                        class="text-xs
                               font-semibold
                               text-gray-300
                               mb-2"
                    >
                        T2 — Later
                    </div>


                    <!-- Preview -->
                    <div
                        class="preview-box
                               bg-gray-800
                               border
                               border-gray-700
                               rounded-lg
                               overflow-hidden"
                    >

                        <div
                            v-if="isT2Tiff && !t2Preview"
                            class="preview-placeholder flex flex-col items-center justify-center p-2 text-center bg-cyan-950/40 border border-cyan-500/30 h-full"
                        >
                            <span class="text-2xl mb-1">🛰️</span>
                            <span class="text-[11px] font-bold text-cyan-300">GeoTIFF (.tif)</span>
                            <span class="text-[9px] text-gray-400">16-bit Multispectral</span>
                        </div>

                        <img
                            v-else-if="t2Preview"
                            :src="t2Preview"
                            alt="T2 satellite image"
                            class="preview-image"
                        />

                        <div
                            v-else
                            class="preview-placeholder"
                        >
                            <span>T2</span>
                        </div>

                    </div>


                    <!-- File input -->
                    <input
                        type="file"
                        accept=".jpg,.jpeg,.png,.tif,.tiff,image/jpeg,image/png,image/tiff"
                        @change="handleT2Change"
                        class="mt-2
                               w-full
                               text-xs
                               text-gray-300
                               file:mr-2
                               file:py-1.5
                               file:px-2.5
                               file:rounded-md
                               file:border-0
                               file:bg-cyan-700
                               file:text-white
                               hover:file:bg-cyan-600"
                    />


                    <p
                        v-if="t2File"
                        class="text-[11px]
                               text-gray-400
                               mt-1
                               truncate"
                        :title="t2File.name"
                    >
                        {{ t2File.name }}
                    </p>

                </div>

            </div>


            <!-- ==================================================
                 DETECT BUTTON
                 ================================================== -->

            <button
                @click="runChangeDetection"
                :disabled="!canProcess"
                class="w-full
                       py-2.5
                       rounded-lg
                       font-semibold
                       transition
                       duration-200"
                :class="{
                    'bg-cyan-600 hover:bg-cyan-500 text-white':
                        canProcess,

                    'bg-gray-700 text-gray-500 cursor-not-allowed':
                        !canProcess
                }"
            >

                <span v-if="!isProcessing">
                    Detect Changes
                </span>

                <span v-else>
                    Processing T1 + T2...
                </span>

            </button>


            <!-- ==================================================
                 ERROR
                 ================================================== -->

            <div
                v-if="errorMessage"
                class="mt-4
                       p-3
                       rounded-lg
                       bg-red-900/40
                       border
                       border-red-500/40
                       text-red-300
                       text-sm"
            >

                {{ errorMessage }}

            </div>


            <!-- ==================================================
                 DETECTION RESULT
                 ================================================== -->

            <div
                v-if="result && changeDetection"
                class="mt-5
                       pt-4
                       border-t
                       border-gray-700"
            >

                <h3
                    class="text-sm
                           font-semibold
                           text-gray-200
                           mb-3"
                >
                    Detection Result
                </h3>


                <!-- =================================================
                     RESULT METRICS
                     ================================================= -->

                <div
                    class="grid
                           grid-cols-2
                           gap-3"
                >

                    <!-- Change -->
                    <div
                        class="bg-gray-800
                               rounded-lg
                               p-3"
                    >

                        <p
                            class="text-xs
                                   text-gray-400"
                        >
                            Change
                        </p>


                        <p
                            class="text-lg
                                   font-bold"
                            :class="
                                changeDetection.change_detected
                                    ? 'text-green-400'
                                    : 'text-gray-400'
                            "
                        >
                            {{
                                changeDetection.change_detected
                                    ? 'Detected'
                                    : 'No Change'
                            }}
                        </p>

                    </div>


                    <!-- Severity -->
                    <div
                        class="bg-gray-800
                               rounded-lg
                               p-3"
                    >

                        <p
                            class="text-xs
                                   text-gray-400"
                        >
                            Severity
                        </p>


                        <p
                            class="text-lg
                                   font-bold"
                            :class="severityClass"
                        >
                            {{ severity || 'N/A' }}
                        </p>

                    </div>


                    <!-- Changed Area -->
                    <div
                        class="bg-gray-800
                               rounded-lg
                               p-3"
                    >

                        <p
                            class="text-xs
                                   text-gray-400"
                        >
                            Changed Area
                        </p>


                        <p
                            class="text-lg
                                   font-bold
                                   text-white"
                        >
                            {{ changePercentage }}%
                        </p>

                    </div>


                    <!-- Regions -->
                    <div
                        class="bg-gray-800
                               rounded-lg
                               p-3"
                    >

                        <p
                            class="text-xs
                                   text-gray-400"
                        >
                            Regions
                        </p>


                        <p
                            class="text-lg
                                   font-bold
                                   text-white"
                        >
                            {{ numberOfRegions }}
                        </p>

                    </div>

                </div>


                <!-- =================================================
                     GEOTIFF GEOREFERENCING METADATA (PS 2.2.6)
                     ================================================= -->
                <div
                    v-if="geotiffMeta && geotiffMeta.is_geotiff"
                    class="mt-3 p-3 bg-gradient-to-br from-cyan-950/40 via-gray-900 to-gray-800 border border-cyan-500/40 rounded-xl"
                >
                    <div class="flex items-center justify-between gap-2 mb-2">
                        <div class="flex items-center gap-1.5">
                            <span class="text-sm">🛰️</span>
                            <span class="text-xs font-bold text-cyan-300 uppercase tracking-wider">
                                Georeferenced Satellite Ingestion (PS 2.2.6)
                            </span>
                        </div>
                        <span class="text-[10px] px-2 py-0.5 rounded-full bg-cyan-900/60 text-cyan-300 font-mono border border-cyan-500/30 font-semibold">
                            EPSG:{{ geotiffMeta.epsg || 'WGS84' }}
                        </span>
                    </div>

                    <div class="grid grid-cols-2 gap-2 text-[11px] mb-2.5">
                        <div class="bg-gray-900/70 p-2 rounded-lg border border-gray-700/60">
                            <span class="text-gray-400 block text-[10px]">Projection / Datum</span>
                            <span class="text-white font-mono font-semibold truncate block" :title="geotiffMeta.crs">
                                {{ geotiffMeta.crs || 'WGS 84' }}
                            </span>
                        </div>
                        <div class="bg-gray-900/70 p-2 rounded-lg border border-gray-700/60">
                            <span class="text-gray-400 block text-[10px]">Ground Resolution (GSD)</span>
                            <span class="text-cyan-400 font-mono font-bold">
                                {{ geotiffMeta.resolution ? `${geotiffMeta.resolution[0]}m` : '10.0m' }} / px
                            </span>
                        </div>
                        <div class="bg-gray-900/70 p-2 rounded-lg border border-gray-700/60 col-span-2">
                            <span class="text-gray-400 block text-[10px]">WGS84 Scene Bounds (Lat / Lon)</span>
                            <span class="text-emerald-400 font-mono text-[10.5px] block truncate">
                                [{{ geotiffMeta.wgs84_bounds ? `${geotiffMeta.wgs84_bounds[1]}°, ${geotiffMeta.wgs84_bounds[0]}°` : 'N/A' }}] ↔ [{{ geotiffMeta.wgs84_bounds ? `${geotiffMeta.wgs84_bounds[3]}°, ${geotiffMeta.wgs84_bounds[2]}°` : 'N/A' }}]
                            </span>
                        </div>
                    </div>

                    <button
                        type="button"
                        @click="focusMapOnGeoTIFF"
                        class="w-full py-1.5 px-3 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white flex items-center justify-center gap-1.5 shadow-md transition"
                    >
                        <span>🎯</span> Focus Map on GeoTIFF Bounds
                    </button>
                </div>


                <!-- =================================================
                     CHANGE OVERLAY
                     ================================================= -->

                <div
                    v-if="overlayImage"
                    class="mt-5"
                >

                    <div
                        class="flex
                               items-center
                               justify-between
                               mb-2"
                    >

                        <h3
                            class="text-sm
                                   font-semibold
                                   text-gray-200"
                        >
                            Detected Changes
                        </h3>


                        <span
                            v-if="selectedChannel === 'vegetation'"
                            class="text-xs
                                   text-emerald-400
                                   font-semibold"
                        >
                            Red = Clearance | Green = Regrowth
                        </span>

                        <span
                            v-else-if="selectedChannel === 'pixel_diff'"
                            class="text-xs
                                   text-amber-400
                                   font-semibold"
                        >
                            Amber = Surface Anomaly
                        </span>

                        <span
                            v-else
                            class="text-xs
                                   text-red-400
                                   font-semibold"
                        >
                            Red = Structural Change
                        </span>

                    </div>


                    <!-- Overlay image -->
                    <div
                        class="overlay-container"
                    >

                        <img
                            :src="overlayImage"
                            alt="T2 satellite image with detected changes"
                            class="overlay-image"
                        />

                    </div>


                    <p
                        class="text-xs
                               text-gray-400
                               mt-2"
                    >
                        <span v-if="selectedChannel === 'vegetation'">
                            Vegetation canopy clearance highlighted in red, regrowth in green (NDVI/VARI).
                        </span>
                        <span v-else-if="selectedChannel === 'pixel_diff'">
                            Tactical surface anomalies and pixel-level radiometric shifts highlighted in amber (CVA).
                        </span>
                        <span v-else>
                            Man-made structural changes detected by the Siamese U-Net deep learning model.
                        </span>
                    </p>

                </div>


                <!-- =================================================
                     MODEL
                     ================================================= -->

                <div
                    class="mt-4
                           text-xs
                           text-gray-400"
                >

                    Model:

                    <span class="text-gray-200">
                        {{ result.ml_result?.model }}
                    </span>

                </div>


                <!-- =================================================
                     THRESHOLD
                     ================================================= -->

                <div
                    class="mt-1
                           text-xs
                           text-gray-400"
                >

                    Threshold:

                    <span class="text-gray-200">
                        {{ result.ml_result?.threshold }}
                    </span>

                </div>


                <!-- =================================================
                     ALERT
                     ================================================= -->

                <div
                    v-if="result.alert_created"
                    class="mt-4
                           p-3
                           rounded-lg
                           bg-green-900/30
                           border
                           border-green-500/30
                           text-green-300
                           text-sm"
                >

                    ✓ Alert created successfully.

                    <div class="mt-1">

                        Alert ID:

                        <span class="font-semibold">
                            {{ result.alert_id }}
                        </span>

                    </div>

                </div>

            </div>

        </div>

    </div>

</template>


<style scoped>

.change-detection-panel {

    position: relative;

    width: 500px;

    min-width: 360px;

    max-width: 800px;

    min-height: 280px;

    max-height: 85vh;

    resize: both;

    overflow: auto;

    box-sizing: border-box;

    z-index: 100;

}


/* ============================================================
   MINIMIZED STATE
   ============================================================ */

.change-detection-panel.is-minimized {

    min-height: auto;

    height: auto;

}


/* ============================================================
   DRAG HEADER
   ============================================================ */

.panel-drag-handle {

    cursor: move;

    user-select: none;

    touch-action: none;

}


.panel-drag-handle:active {

    cursor: grabbing;

}


/* ============================================================
   FORM CONTROLS
   ============================================================ */

button,
input {

    touch-action: auto;

}


/* ============================================================
   IMAGE PREVIEW BOX
   ============================================================ */

.preview-box {

    width: 100%;

    height: 130px;

}


.preview-image {

    width: 100%;

    height: 100%;

    object-fit: cover;

    display: block;

}


.preview-placeholder {

    width: 100%;

    height: 100%;

    display: flex;

    align-items: center;

    justify-content: center;

    color: #6b7280;

    font-size: 0.8rem;

}


/* ============================================================
   CHANGE OVERLAY
   ============================================================ */

.overlay-container {

    width: 100%;

    max-height: 350px;

    overflow: hidden;

    border-radius: 0.5rem;

    border: 1px solid rgba(239, 68, 68, 0.4);

    background: #000;

}


.overlay-image {

    width: 100%;

    height: auto;

    display: block;

}

</style>