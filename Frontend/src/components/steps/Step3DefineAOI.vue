<!-- frontend/src/components/steps/Step3DefineAOI.vue - With File Upload Support -->
<script setup>
import { ProjectFormData } from '@/classes/ProjectFormData.js';
import { AreaOfInterestDraft } from '@/classes/AreaOfInterestDraft.js';
import MapVisualization from '@/components/map/MapVisualization.vue';
import { ref, computed, onMounted } from 'vue';
import { useMessageStore } from '@/stores/MessageStore.js';
const messageStore = useMessageStore();

const props = defineProps({
    projectData: ProjectFormData,
});

const accumulatedGeometries = ref([]);
const showDecisionModal = ref(false);
const showNameModal = ref(false);
const showUploadModal = ref(false);

const currentAoiName = ref('');
const currentAoiBuffer = ref(100);
const currentAoiType = ref('');
const currentAoiGeometry = ref(null);
const currentAoiAuxData = ref([]);
const showNewAuxFields = ref(false);
const newAuxKey = ref('');
const newAuxValue = ref('');

const aoiCounter = ref(1);
const isProcessingFile = ref(false);
const fileInputRef = ref(null);

onMounted(() => {
    if (props.projectData.aoiDrafts.length > 0) {
        const maxId = Math.max(...props.projectData.aoiDrafts.map(a => a.clientAoiId));
        aoiCounter.value = maxId + 1;
        console.log(`[Step3] Initialized AOI counter to ${aoiCounter.value}`);
    }
});

const mapVizRef = ref(null);

const handleAoiDrawn = (data) => {
    currentAoiGeometry.value = data.geometry;
    currentAoiType.value = data.geometry.type;
    currentAoiBuffer.value = 100;
    showDecisionModal.value = true;
};

const continueDrawing = () => {
    const requiresBuffer = ['Point', 'LineString'].includes(currentAoiType.value);
    const bufferValue = requiresBuffer ? Number(currentAoiBuffer.value) : null;

    accumulatedGeometries.value.push({
        geometry: currentAoiGeometry.value,
        type: currentAoiType.value,
        bufferDistance: bufferValue
    });

    if (mapVizRef.value?.clearUnsavedLayer) {
        mapVizRef.value.clearUnsavedLayer();
    }

    showDecisionModal.value = false;
    currentAoiGeometry.value = null;
    currentAoiBuffer.value = 100;
    currentAoiType.value = '';

    messageStore.showMessage(
        `Polygon added (${accumulatedGeometries.value.length} total). Draw next polygon.`,
        "info"
    );
};

const proceedToNaming = () => {
    const requiresBuffer = ['Point', 'LineString'].includes(currentAoiType.value);
    const bufferValue = requiresBuffer ? Number(currentAoiBuffer.value) : null;

    accumulatedGeometries.value.push({
        geometry: currentAoiGeometry.value,
        type: currentAoiType.value,
        bufferDistance: bufferValue
    });

    showDecisionModal.value = false;
    showNameModal.value = true;
    currentAoiName.value = '';
    currentAoiAuxData.value = [];
};

// NEW: File Upload Functions
const openUploadModal = () => {
    showUploadModal.value = true;
};

const closeUploadModal = () => {
    showUploadModal.value = false;
    if (fileInputRef.value) {
        fileInputRef.value.value = '';
    }
};

const parseKMLToGeoJSON = (kmlText) => {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(kmlText, 'text/xml');
    
    const parseCoordinates = (coordsText) => {
        return coordsText.trim().split(/\s+/).map(coord => {
            const [lng, lat] = coord.split(',').map(Number);
            return [lng, lat];
        });
    };

    const polygons = [];
    
    const polygonElements = xmlDoc.getElementsByTagName('Polygon');
    for (let polygon of polygonElements) {
        const outerBoundary = polygon.getElementsByTagName('outerBoundaryIs')[0];
        if (outerBoundary) {
            const coordinates = outerBoundary.getElementsByTagName('coordinates')[0];
            if (coordinates) {
                const coords = parseCoordinates(coordinates.textContent);
                polygons.push({
                    type: 'Polygon',
                    coordinates: [coords]
                });
            }
        }
    }

    const multiGeometries = xmlDoc.getElementsByTagName('MultiGeometry');
    for (let multi of multiGeometries) {
        const innerPolygons = multi.getElementsByTagName('Polygon');
        for (let polygon of innerPolygons) {
            const outerBoundary = polygon.getElementsByTagName('outerBoundaryIs')[0];
            if (outerBoundary) {
                const coordinates = outerBoundary.getElementsByTagName('coordinates')[0];
                if (coordinates) {
                    const coords = parseCoordinates(coordinates.textContent);
                    polygons.push({
                        type: 'Polygon',
                        coordinates: [coords]
                    });
                }
            }
        }
    }

    return polygons;
};

const extractPolygonGeometries = (geoJson) => {
    const polygons = [];

    const processGeometry = (geometry) => {
        if (!geometry || !geometry.type) return;

        switch (geometry.type) {
            case 'Polygon':
                polygons.push({
                    type: 'Polygon',
                    coordinates: geometry.coordinates
                });
                break;
            
            case 'MultiPolygon':
                geometry.coordinates.forEach(polyCoords => {
                    polygons.push({
                        type: 'Polygon',
                        coordinates: polyCoords
                    });
                });
                break;
            
            case 'GeometryCollection':
                geometry.geometries.forEach(geom => processGeometry(geom));
                break;
            
            case 'Point':
            case 'LineString':
            case 'MultiPoint':
            case 'MultiLineString':
                break;
        }
    };

    if (geoJson.type === 'FeatureCollection') {
        geoJson.features.forEach(feature => {
            if (feature.geometry) {
                processGeometry(feature.geometry);
            }
        });
    } else if (geoJson.type === 'Feature') {
        if (geoJson.geometry) {
            processGeometry(geoJson.geometry);
        }
    } else if (geoJson.type) {
        processGeometry(geoJson);
    }

    return polygons;
};

const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    isProcessingFile.value = true;

    try {
        const text = await file.text();
        let polygons = [];

        if (file.name.toLowerCase().endsWith('.kml')) {
            polygons = parseKMLToGeoJSON(text);
        } else if (file.name.toLowerCase().endsWith('.geojson') || file.name.toLowerCase().endsWith('.json')) {
            const geoJson = JSON.parse(text);
            polygons = extractPolygonGeometries(geoJson);
        } else {
            throw new Error('Unsupported file format. Please upload .geojson or .kml files only.');
        }

        if (polygons.length === 0) {
            throw new Error('No polygon geometries found in the file.');
        }

        // Add polygons to accumulated geometries
        polygons.forEach(polygon => {
            accumulatedGeometries.value.push({
                geometry: polygon,
                type: 'Polygon',
                bufferDistance: null
            });
        });

        messageStore.showMessage(
            `Successfully extracted ${polygons.length} polygon(s) from file.`,
            "success"
        );

        // Close upload modal and open naming modal
        closeUploadModal();
        showNameModal.value = true;
        currentAoiName.value = '';
        currentAoiAuxData.value = [];

    } catch (err) {
        console.error('Error processing file:', err);
        messageStore.showMessage(
            err.message || 'Failed to process file. Please check the file format.',
            'error'
        );
    } finally {
        isProcessingFile.value = false;
    }
};

const finalizeAOI = async () => {
    if (!currentAoiName.value.trim()) {
        messageStore.showMessage("AOI Name is required.", "error");
        return;
    }

    if (accumulatedGeometries.value.length === 0) {
        messageStore.showMessage("No geometries drawn.", "error");
        return;
    }

    const auxDataObject = {};
    currentAoiAuxData.value.forEach(item => {
        if (item.key.trim() && item.value.trim()) {
            auxDataObject[item.key.trim()] = item.value.trim();
        }
    });

    let finalGeometry;
    let finalGeometryType;

    if (accumulatedGeometries.value.length === 1) {
        finalGeometry = accumulatedGeometries.value[0].geometry;
        finalGeometryType = accumulatedGeometries.value[0].type;
    } else {
        finalGeometry = {
            type: 'GeometryCollection',
            geometries: accumulatedGeometries.value.map(g => g.geometry)
        };
        finalGeometryType = 'GeometryCollection';
    }

    const bufferConfig = accumulatedGeometries.value.map((g, idx) => ({
        index: idx,
        type: g.type,
        buffer: g.bufferDistance,
        originalCoordinates: g.geometry.coordinates
    }));

    const newClientAoiId = aoiCounter.value;
    console.log(`[Step3] Creating AOI with clientAoiId: ${newClientAoiId}`);

    const newAOI = new AreaOfInterestDraft(
        currentAoiName.value.trim(),
        finalGeometry,
        newClientAoiId,
        finalGeometryType,
        null
    );

    newAOI.geomProperties = {
        ...newAOI.geomProperties,
        bufferConfig: bufferConfig,
        geometryCount: accumulatedGeometries.value.length
    };

    newAOI.setAuxData(Object.keys(auxDataObject).length > 0 ? auxDataObject : null);

    props.projectData.aoiDrafts.push(newAOI);
    aoiCounter.value++;

    if (mapVizRef.value?.clearUnsavedLayer) {
        mapVizRef.value.clearUnsavedLayer();
    }
    if (mapVizRef.value?.clearAccumulatedGeometries) {
        mapVizRef.value.clearAccumulatedGeometries();
    }

    accumulatedGeometries.value = [];
    showNameModal.value = false;
    currentAoiName.value = '';
    currentAoiAuxData.value = [];
    showNewAuxFields.value = false;
    newAuxKey.value = '';
    newAuxValue.value = '';

    messageStore.showMessage(
        `AOI "${newAOI.name}" saved with ${bufferConfig.length} polygon(s).`,
        "success"
    );
};

const cancelDecision = () => {
    if (mapVizRef.value?.clearUnsavedLayer) {
        mapVizRef.value.clearUnsavedLayer();
    }
    showDecisionModal.value = false;
    currentAoiGeometry.value = null;
    currentAoiBuffer.value = 100;
    currentAoiType.value = '';
};

const cancelNaming = () => {
    accumulatedGeometries.value = [];
    if (mapVizRef.value?.clearAccumulatedGeometries) {
        mapVizRef.value.clearAccumulatedGeometries();
    }
    showNameModal.value = false;
    currentAoiName.value = '';
    currentAoiAuxData.value = [];
};

const addAuxField = () => {
    if (!newAuxKey.value.trim()) {
        messageStore.showMessage("Key cannot be empty.", "error");
        return;
    }

    const isDuplicate = currentAoiAuxData.value.some(
        item => item.key.toLowerCase() === newAuxKey.value.trim().toLowerCase()
    );

    if (isDuplicate) {
        messageStore.showMessage("This key already exists.", "error");
        return;
    }

    currentAoiAuxData.value.push({
        key: newAuxKey.value.trim(),
        value: newAuxValue.value.trim()
    });

    newAuxKey.value = '';
    newAuxValue.value = '';
    showNewAuxFields.value = false;
};

const removeAuxField = (index) => {
    currentAoiAuxData.value.splice(index, 1);
};

const removeAOI = (clientAoiId) => {
    const aoi = props.projectData.aoiDrafts.find(a => a.clientAoiId === clientAoiId);

    if (aoi) {
        if (aoi.dbId) {
            console.log(`[Step3] Marking existing AOI ${aoi.aoiId} for deletion`);
            aoi.markForDeletion();
        } else {
            console.log(`[Step3] Removing new AOI ${aoi.aoiId} from draft`);
            const index = props.projectData.aoiDrafts.findIndex(a => a.clientAoiId === clientAoiId);
            if (index !== -1) {
                props.projectData.aoiDrafts.splice(index, 1);
            }
        }

        messageStore.showMessage(`AOI removed`, "info");
    }
};

const requiresBuffer = computed(() =>
    ['Point', 'LineString'].includes(currentAoiType.value)
);

const visibleAoiDrafts = computed(() =>
    props.projectData.aoiDrafts.filter(aoi => aoi.status !== 2)
);
</script>

<template>
    <div>
        <div class="min-h-[50vh] relative">
            <MapVisualization @aoi-drawn="handleAoiDrawn" :aois-to-display="visibleAoiDrafts"
                :accumulated-geometries="accumulatedGeometries" :is-monitor-mode="false" ref="mapVizRef" />
            
            <!-- NEW: Upload Button -->
            <button @click="openUploadModal"
                class="absolute bottom-4 left-4 z-[70] bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg shadow-lg transition-all duration-200 flex items-center gap-2"
                title="Upload GeoJSON/KML">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12">
                    </path>
                </svg>
                <span class="text-sm font-medium">Upload File</span>
            </button>
        </div>

        <h4 class="text-lg font-semibold mt-2 text-cyan-400" style="font-size: 2vh;">
            Draft AOIs ({{ visibleAoiDrafts.length }})
        </h4>

        <div class="aoi-list-manager space-y-2 h-[12vh] overflow-y-auto">
            <div v-for="(aoi, index) in visibleAoiDrafts" :key="aoi.clientAoiId"
                class="aoi-draft flex justify-between h-[6vh] items-center px-3 text-left bg-gray-700 rounded shadow-md">
                <span class="flex flex-col">
                    <div>
                        <span class="text-white font-bold p-0 text-xs mr-3">
                            {{ index + 1 }}.
                        </span>
                        {{ aoi.name }}
                        <span class="text-sm ml-2 text-yellow-400">
                            ({{ aoi.geomProperties?.geometryCount || 1 }} polygon{{ aoi.geomProperties?.geometryCount >
                            1 ? 's' : '' }})
                        </span>
                    </div>
                    <div>
                        <span v-if="aoi.auxData" class="text-sm text-blue-400 ml-2">
                            ({{ Object.keys(aoi.auxData).length }} custom fields)
                        </span>
                    </div>
                </span>
                <button @click="removeAOI(aoi.clientAoiId)"
                    class="remove-btn bg-red-600 hover:bg-red-700 text-white p-1 rounded">
                    Remove
                </button>
            </div>
            <p v-if="visibleAoiDrafts.length === 0" class="text-center text-gray-400 p-4">
                Draw an AOI on the map above or upload a GeoJSON/KML file to begin.
            </p>
        </div>

        <!-- NEW: Upload Modal -->
        <Teleport to="body">
            <div v-if="showUploadModal"
                class="fixed inset-0 bg-black bg-opacity-70 z-[100000] flex justify-center items-center p-4">
                <div class="w-full max-w-md bg-gray-800 rounded-xl shadow-2xl p-6 text-white">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-xl font-bold text-cyan-400">Upload Polygon File</h3>
                        <button @click="closeUploadModal"
                            class="text-gray-400 hover:text-white transition">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>

                    <div class="bg-gray-700 rounded-lg border-2 border-dashed border-gray-600 hover:border-cyan-500 transition-colors duration-200">
                        <input
                            ref="fileInputRef"
                            type="file"
                            accept=".geojson,.json,.kml"
                            @change="handleFileUpload"
                            class="hidden"
                            id="geometry-file-upload"
                        />
                        
                        <label
                            for="geometry-file-upload"
                            class="flex flex-col items-center justify-center p-8 cursor-pointer"
                        >
                            <div v-if="isProcessingFile" class="flex flex-col items-center">
                                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mb-3"></div>
                                <p class="text-gray-300">Processing file...</p>
                            </div>
                            <div v-else class="flex flex-col items-center">
                                <svg class="w-12 h-12 text-cyan-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12">
                                    </path>
                                </svg>
                                <p class="text-white font-semibold mb-1">Click to browse</p>
                                <p class="text-gray-400 text-sm text-center">
                                    GeoJSON or KML files<br />
                                    <span class="text-xs text-gray-500">(Polygon geometries only)</span>
                                </p>
                            </div>
                        </label>
                    </div>

                    <div class="mt-4 p-3 bg-blue-900/30 border border-blue-500/50 rounded-lg">
                        <p class="text-blue-300 text-xs">
                            <strong>Supported formats:</strong> .geojson, .json, .kml<br />
                            <strong>Note:</strong> Only polygon geometries will be extracted. Points and LineStrings will be ignored.
                        </p>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Existing Decision Modal -->
        <Teleport to="body">
            <div v-if="showDecisionModal"
                class="fixed inset-0 bg-black bg-opacity-70 z-[100000] flex justify-center items-center p-4">
                <div class="w-full max-w-md bg-gray-800 rounded-xl shadow-2xl p-6 text-white">
                    <div class="flex items-center justify-between">
                        <p class="text-xl font-bold text-cyan-400">
                            Polygon ({{ accumulatedGeometries.length + 1 }})
                        </p>
                        <button @click="cancelDecision"
                            class="px-3 py-1 bg-red-600 hover:bg-red-500 rounded-md text-sm transition">
                            Cancel
                        </button>
                    </div>

                    <div v-if="requiresBuffer" class="form-group mb-4 mt-4">
                        <label class="block text-gray-400 mb-1">
                            Buffer Distance (meters):
                        </label>
                        <input type="number" v-model.number="currentAoiBuffer" min="1" step="10" placeholder="100"
                            class="w-full p-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-cyan-400 focus:outline-none">
                    </div>

                    <p class="text-gray-300 mb-6 mt-4">
                        What would you like to do next?
                    </p>

                    <div class="flex flex-col gap-3">
                        <button @click="continueDrawing"
                            class="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition">
                            Add New Polygon
                        </button>
                        <button @click="proceedToNaming"
                            class="w-full px-4 py-3 bg-cyan-600 hover:bg-cyan-700 rounded-lg font-semibold transition">
                            Finish
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Existing Naming Modal -->
        <Teleport to="body">
            <div v-if="showNameModal"
                class="fixed inset-0 bg-black bg-opacity-70 z-[100000] flex justify-center items-center p-4">
                <div
                    class="w-full max-w-md bg-gray-800 rounded-xl shadow-2xl p-6 text-white max-h-[90vh] overflow-y-auto">
                    <h3 class="text-2xl font-bold mb-4 text-cyan-400">
                        Name Your AOI ({{ accumulatedGeometries.length }} Polygons)
                    </h3>

                    <div class="form-group mb-4">
                        <label class="block text-gray-400 mb-1">
                            AOI Name: <span class="text-red-400">*</span>
                        </label>
                        <input type="text" v-model="currentAoiName" placeholder="e.g., Andaman & Nicobar Islands"
                            class="w-full p-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-cyan-400 focus:outline-none">
                    </div>

                    <div class="form-group mb-4">
                        <label class="block text-gray-400 mb-2">Custom Fields (Optional):</label>

                        <div v-if="currentAoiAuxData.length > 0" class="space-y-2 mb-3">
                            <div v-for="(item, index) in currentAoiAuxData" :key="index"
                                class="flex items-center justify-between p-2 bg-gray-700 rounded border border-gray-600">
                                <div class="flex-grow mr-2">
                                    <span class="text-cyan-400 font-semibold text-sm">{{ item.key }}:</span>
                                    <span class="text-white text-sm ml-2">{{ item.value }}</span>
                                </div>
                                <button @click="removeAuxField(index)"
                                    class="bg-red-500 px-3 py-1.5 text-white rounded-lg text-sm font-semibold">
                                    Remove
                                </button>
                            </div>
                        </div>

                        <button @click="showNewAuxFields = true" v-if="!showNewAuxFields"
                            class="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg w-full justify-center">
                            Add Custom Field
                        </button>

                        <div v-if="showNewAuxFields" class="p-3 bg-gray-700 rounded-lg border border-gray-600">
                            <div class="flex flex-col gap-2 mb-2">
                                <input type="text" v-model="newAuxKey" placeholder="Key"
                                    class="w-full p-2 bg-gray-600 text-white rounded border border-gray-500 focus:border-cyan-400 focus:outline-none text-sm" />
                                <input type="text" v-model="newAuxValue" placeholder="Value"
                                    class="w-full p-2 bg-gray-600 text-white rounded border border-gray-500 focus:border-cyan-400 focus:outline-none text-sm" />
                            </div>
                            <div class="flex justify-end gap-2">
                                <button @click="showNewAuxFields = false; newAuxKey = ''; newAuxValue = '';"
                                    class="bg-gray-500 px-3 py-1.5 text-white rounded-lg text-sm">
                                    Cancel
                                </button>
                                <button @click="addAuxField"
                                    class="bg-blue-600 hover:bg-blue-700 px-3 py-1.5 text-white rounded-lg text-sm">
                                    Save Field
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="flex justify-end gap-3 mt-6">
                        <button @click="cancelNaming" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg">
                            Cancel
                        </button>
                        <button @click="finalizeAOI"
                            class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg font-semibold">
                            Save AOI
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<style scoped>
.aoi-draft {
    display: flex;
    justify-content: space-between;
    padding: 8px;
    border-bottom: 1px dotted #eee;
}

.remove-btn {
    background-color: #f44336;
    color: white;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
}
</style>