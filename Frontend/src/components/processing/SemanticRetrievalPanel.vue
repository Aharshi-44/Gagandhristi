<script setup>
import { ref, onMounted } from 'vue';
import { ApiClient } from '@/api/backendAPIendpoint.js';

const emit = defineEmits(['close']);

const apiClient = ApiClient.getInstance();

// ============================================================
// PANEL STATE & DRAG
// ============================================================
const isMinimized = ref(true);
const activeTab = ref('text'); // 'text' | 'image' | 'catalog'

const toggleMinimize = () => {
    isMinimized.value = !isMinimized.value;
};

const panelX = ref(0);
const panelY = ref(0);
const isDragging = ref(false);
const dragStartX = ref(0);
const dragStartY = ref(0);
const startPanelX = ref(0);
const startPanelY = ref(0);

const startDrag = (event) => {
    if (event.button !== 0) return;
    if (event.target.closest('button') || event.target.closest('input') || event.target.closest('select')) return;

    isDragging.value = true;
    dragStartX.value = event.clientX;
    dragStartY.value = event.clientY;
    startPanelX.value = panelX.value;
    startPanelY.value = panelY.value;

    try {
        event.currentTarget.setPointerCapture(event.pointerId);
    } catch (e) {}
};

const handleDrag = (event) => {
    if (!isDragging.value) return;
    const deltaX = event.clientX - dragStartX.value;
    const deltaY = event.clientY - dragStartY.value;
    panelX.value = startPanelX.value + deltaX;
    panelY.value = startPanelY.value + deltaY;
};

const stopDrag = (event) => {
    if (!isDragging.value) return;
    isDragging.value = false;
    try {
        if (event?.currentTarget?.hasPointerCapture?.(event.pointerId)) {
            event.currentTarget.releasePointerCapture(event.pointerId);
        }
    } catch (e) {}
};

// ============================================================
// RETRIEVAL STATE (PS 2.2.1)
// ============================================================
const textQuery = ref('');
const topK = ref(5);
const isSearching = ref(false);
const searchError = ref('');
const searchResults = ref([]);
const activeSearchQuery = ref('');
const searchModeUsed = ref('');

// Query-by-Example State
const queryImageFile = ref(null);
const queryImagePreview = ref(null);
const fileInputRef = ref(null);

// Catalog State
const catalogTiles = ref([]);
const isLoadingCatalog = ref(false);

// Inspection Modal
const selectedInspectTile = ref(null);

// Tactical Presets
const tacticalPresets = [
    { label: '🏗️ New Structures', query: 'newly constructed buildings, military barracks, or concrete expansion' },
    { label: '✈️ Airfield / Runway', query: 'airport tarmac, airplane runway, or helipad surface' },
    { label: '🌲 Forest Clearance', query: 'cleared forest, tree logging, or earth excavation' },
    { label: '💧 Water Bodies', query: 'river bank, water reservoir, or flooded terrain' },
    { label: '🚛 Convoys & Vehicles', query: 'military vehicle convoy or supply trucks on open ground' },
    { label: '🛡️ Fortifications', query: 'military fortifications, trenches, and defensive earthworks' }
];

const applyPreset = (query) => {
    textQuery.value = query;
    executeTextSearch();
};

// ============================================================
// EXECUTE SEARCHES
// ============================================================
const executeTextSearch = async () => {
    if (!textQuery.value.trim()) return;

    isSearching.value = true;
    searchError.value = '';
    activeSearchQuery.value = textQuery.value.trim();
    searchModeUsed.value = 'text';

    try {
        const response = await apiClient.retrieveByText(textQuery.value.trim(), topK.value);
        searchResults.value = response.results || [];
    } catch (err) {
        console.error('Text retrieval error:', err);
        searchError.value = err.response?.data?.error || err.message || 'Semantic search failed';
    } finally {
        isSearching.value = false;
    }
};

const onImageSelected = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    queryImageFile.value = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        queryImagePreview.value = e.target.result;
    };
    reader.readAsDataURL(file);
};

const executeImageSearch = async () => {
    if (!queryImageFile.value) return;

    isSearching.value = true;
    searchError.value = '';
    activeSearchQuery.value = queryImageFile.value.name;
    searchModeUsed.value = 'image';

    try {
        const response = await apiClient.retrieveByImage(queryImageFile.value, topK.value);
        searchResults.value = response.results || [];
    } catch (err) {
        console.error('Image retrieval error:', err);
        searchError.value = err.response?.data?.error || err.message || 'Visual similarity search failed';
    } finally {
        isSearching.value = false;
    }
};

const clearImageSelection = () => {
    queryImageFile.value = null;
    queryImagePreview.value = null;
    if (fileInputRef.value) fileInputRef.value.value = '';
};

const loadCatalog = async () => {
    isLoadingCatalog.value = true;
    try {
        const response = await apiClient.getRetrievalCatalog();
        catalogTiles.value = response.tiles || [];
    } catch (err) {
        console.error('Catalog fetch error:', err);
    } finally {
        isLoadingCatalog.value = false;
    }
};

onMounted(() => {
    loadCatalog();
});
</script>

<template>
    <div
        class="semantic-retrieval-panel
               bg-gray-900/95
               border border-cyan-500/40
               rounded-xl
               shadow-2xl
               p-4
               text-white
               flex flex-col"
        :class="{
            'is-minimized': isMinimized
        }"
        :style="{
            transform: `translate(${panelX}px, ${panelY}px)`
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
            <div class="flex items-center gap-2 min-w-0">
                <!-- Drag Grip Icon -->
                <svg
                    class="w-4 h-4 text-gray-500 flex-shrink-0"
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

                <span class="text-base flex-shrink-0">🛰️</span>

                <div class="min-w-0">
                    <h2 class="text-lg font-bold text-cyan-300 truncate flex items-center gap-1.5">
                        <span>Semantic Retrieval</span>
                        <span class="text-[9px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 font-mono border border-cyan-700/60 flex-shrink-0">
                            PS 2.2.1
                        </span>
                    </h2>
                    <p v-if="!isMinimized" class="text-xs text-gray-400 font-mono mt-1 truncate">
                        CLIP Vision-Language Model · CUDA Accelerated
                    </p>
                </div>
            </div>

            <!-- RIGHT -->
            <div class="flex items-center gap-2 flex-shrink-0">
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
        <div v-if="!isMinimized" class="flex-1 space-y-4 overflow-y-auto min-h-0 pr-1">

            <!-- MODE SELECTOR TABS -->
            <div class="grid grid-cols-3 gap-1 bg-gray-800/90 p-1 rounded-lg border border-gray-700 text-xs">
                <button
                    @click="activeTab = 'text'"
                    class="py-1.5 rounded-md font-bold transition flex items-center justify-center gap-1.5"
                    :class="activeTab === 'text' ? 'bg-cyan-600 text-white shadow' : 'text-gray-400 hover:text-white'"
                >
                    <span>💬</span> Free-Text Search
                </button>
                <button
                    @click="activeTab = 'image'"
                    class="py-1.5 rounded-md font-bold transition flex items-center justify-center gap-1.5"
                    :class="activeTab === 'image' ? 'bg-cyan-600 text-white shadow' : 'text-gray-400 hover:text-white'"
                >
                    <span>🖼️</span> Visual Search
                </button>
                <button
                    @click="activeTab = 'catalog'; loadCatalog()"
                    class="py-1.5 rounded-md font-bold transition flex items-center justify-center gap-1.5"
                    :class="activeTab === 'catalog' ? 'bg-cyan-600 text-white shadow' : 'text-gray-400 hover:text-white'"
                >
                    <span>📁</span> Catalog ({{ catalogTiles.length }})
                </button>
            </div>

            <!-- TAB 1: FREE-TEXT SEARCH -->
            <div v-if="activeTab === 'text'" class="space-y-3">
                <div class="relative">
                    <input
                        v-model="textQuery"
                        @keyup.enter="executeTextSearch"
                        type="text"
                        placeholder="Search imagery (e.g. 'damaged runway', 'excavation near river')..."
                        class="w-full bg-gray-800 border border-gray-600 rounded-lg pl-9 pr-24 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 font-medium"
                    />
                    <span class="absolute left-3 top-2.5 text-gray-400 text-sm">🔍</span>
                    <button
                        @click="executeTextSearch"
                        :disabled="isSearching || !textQuery.trim()"
                        class="absolute right-1.5 top-1.5 px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md text-xs font-bold transition disabled:opacity-40 flex items-center gap-1"
                    >
                        <span v-if="isSearching" class="animate-spin text-[10px]">⟳</span>
                        <span>{{ isSearching ? 'Searching...' : 'Search' }}</span>
                    </button>
                </div>

                <!-- Tactical Quick-Search Chips -->
                <div class="space-y-1.5">
                    <label class="text-[11px] uppercase font-bold text-gray-400 tracking-wider">
                        Tactical Query Presets (Defense Scenarios):
                    </label>
                    <div class="flex flex-wrap gap-1.5">
                        <button
                            v-for="preset in tacticalPresets"
                            :key="preset.label"
                            @click="applyPreset(preset.query)"
                            class="px-2.5 py-1 bg-gray-800 hover:bg-cyan-950/80 border border-gray-700 hover:border-cyan-500/50 rounded-full text-[11px] text-gray-300 hover:text-cyan-300 font-medium transition"
                        >
                            {{ preset.label }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- TAB 2: QUERY-BY-EXAMPLE VISUAL SEARCH -->
            <div v-if="activeTab === 'image'" class="space-y-3">
                <div
                    class="border-2 border-dashed border-gray-600 hover:border-cyan-500 rounded-lg p-4 text-center cursor-pointer transition bg-gray-800/50"
                    @click="$refs.fileInputRef.click()"
                >
                    <input
                        ref="fileInputRef"
                        type="file"
                        accept="image/*"
                        class="hidden"
                        @change="onImageSelected"
                    />

                    <div v-if="queryImagePreview" class="flex flex-col items-center gap-2">
                        <img :src="queryImagePreview" class="h-24 w-24 object-cover rounded-lg border border-cyan-500 shadow" />
                        <div class="flex items-center gap-2">
                            <span class="text-xs text-white font-medium">{{ queryImageFile?.name }}</span>
                            <button
                                @click.stop="clearImageSelection"
                                class="text-rose-400 hover:text-rose-300 text-xs underline font-bold"
                            >
                                Remove
                            </button>
                        </div>
                    </div>

                    <div v-else class="space-y-1">
                        <span class="text-2xl">📸</span>
                        <p class="text-xs text-gray-300 font-bold">Upload Target Crop / Patch</p>
                        <p class="text-[11px] text-gray-500">Find structurally and visually similar satellite tiles across catalog</p>
                    </div>
                </div>

                <div class="flex justify-end">
                    <button
                        @click="executeImageSearch"
                        :disabled="isSearching || !queryImageFile"
                        class="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold transition disabled:opacity-40 flex items-center gap-1.5 shadow"
                    >
                        <span v-if="isSearching" class="animate-spin text-xs">⟳</span>
                        <span>{{ isSearching ? 'Scanning Catalog...' : 'Execute Visual Retrieval' }}</span>
                    </button>
                </div>
            </div>

            <!-- TAB 3: CATALOG BROWSER -->
            <div v-if="activeTab === 'catalog'" class="space-y-3">
                <div class="flex justify-between items-center text-xs">
                    <span class="text-gray-400 font-mono">Total Indexed Tiles: {{ catalogTiles.length }}</span>
                    <button @click="loadCatalog" class="text-cyan-400 hover:underline text-[11px] flex items-center gap-1">
                        <span>⟳</span> Refresh Index
                    </button>
                </div>

                <div class="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
                    <div
                        v-for="tile in catalogTiles"
                        :key="tile.tile_id"
                        class="bg-gray-800/80 p-2 rounded-lg border border-gray-700 flex gap-2 items-center hover:border-cyan-500/60 transition cursor-pointer"
                        @click="selectedInspectTile = tile"
                    >
                        <img :src="tile.thumbnail_b64" class="w-12 h-12 object-cover rounded border border-gray-600 flex-shrink-0" />
                        <div class="min-w-0">
                            <p class="text-xs text-white font-bold truncate">{{ tile.name }}</p>
                            <span class="text-[9px] px-1 py-0.2 rounded bg-gray-700 text-cyan-300 font-mono">
                                {{ tile.category }}
                            </span>
                            <p class="text-[10px] text-gray-400 truncate mt-0.5">{{ tile.dimensions }}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ERROR NOTIFICATION -->
            <div v-if="searchError" class="p-2.5 bg-rose-950/80 border border-rose-700 text-rose-300 text-xs rounded-lg">
                ⚠️ {{ searchError }}
            </div>

            <!-- SEARCH RESULTS SECTION -->
            <div v-if="searchResults.length > 0 && activeTab !== 'catalog'" class="space-y-2.5 pt-2 border-t border-gray-800">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase tracking-wider text-amber-400">
                        Top Ranked Matches ({{ searchResults.length }})
                    </span>
                    <span class="text-[10px] text-gray-400 font-mono">
                        Query: "{{ activeSearchQuery }}"
                    </span>
                </div>

                <div class="space-y-2 max-h-72 overflow-y-auto pr-1">
                    <div
                        v-for="match in searchResults"
                        :key="match.tile_id"
                        class="bg-gray-800 p-2.5 rounded-lg border transition hover:border-cyan-500 flex gap-3 items-center"
                        :class="match.rank === 1 ? 'border-amber-500/70 shadow-md ring-1 ring-amber-500/30' : 'border-gray-700'"
                    >
                        <!-- Thumbnail Preview -->
                        <div class="relative flex-shrink-0 cursor-pointer" @click="selectedInspectTile = match">
                            <img :src="match.thumbnail_b64" class="w-16 h-16 object-cover rounded-lg border border-gray-600 hover:opacity-90" />
                            <span
                                class="absolute top-1 left-1 px-1.5 py-0.2 rounded font-black text-[9px] shadow"
                                :class="match.rank === 1 ? 'bg-amber-500 text-gray-950' : 'bg-gray-900/90 text-white'"
                            >
                                #{{ match.rank }}
                            </span>
                        </div>

                        <!-- Match Details -->
                        <div class="flex-grow min-w-0 space-y-1">
                            <div class="flex items-start justify-between gap-1">
                                <h4 class="text-xs font-bold text-white truncate">{{ match.name }}</h4>
                                <span
                                    class="text-xs font-mono font-black px-2 py-0.5 rounded flex-shrink-0"
                                    :class="match.similarity_score >= 70 ? 'bg-emerald-950 text-emerald-400 border border-emerald-600' : 'bg-amber-950 text-amber-400 border border-amber-600'"
                                >
                                    {{ match.similarity_score }}% Match
                                </span>
                            </div>

                            <!-- Similarity Bar -->
                            <div class="w-full bg-gray-900 rounded-full h-1.5 overflow-hidden">
                                <div
                                    class="h-full rounded-full transition-all duration-500"
                                    :style="{ width: `${match.similarity_score}%` }"
                                    :class="match.similarity_score >= 70 ? 'bg-gradient-to-r from-emerald-500 to-cyan-400' : 'bg-gradient-to-r from-amber-500 to-yellow-400'"
                                ></div>
                            </div>

                            <div class="flex items-center justify-between text-[10px] text-gray-400">
                                <span class="truncate">{{ match.description }}</span>
                                <span class="font-mono text-cyan-400 flex-shrink-0 ml-2">cos θ = {{ match.raw_cosine_similarity }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- EMPTY STATE -->
            <div v-else-if="!isSearching && searchResults.length === 0 && activeTab !== 'catalog'" class="py-6 text-center text-gray-500 text-xs">
                <span class="text-2xl block mb-1">🛰️</span>
                Enter a free-text military prompt or upload a crop to execute zero-shot semantic retrieval.
            </div>

        </div>
    </div>

    <!-- TILE INSPECTION MODAL -->
    <div
        v-if="selectedInspectTile"
        class="fixed inset-0 bg-black/80 z-[50000] flex items-center justify-center p-4"
        @click.self="selectedInspectTile = null"
    >
        <div class="bg-gray-900 border-2 border-cyan-500 rounded-xl max-w-lg w-full p-5 space-y-3 relative shadow-2xl">
            <button
                @click="selectedInspectTile = null"
                class="absolute top-3 right-3 text-gray-400 hover:text-white text-xl font-bold px-2"
            >
                ✕
            </button>

            <div class="flex items-center gap-2 border-b border-gray-800 pb-2">
                <span class="text-lg">🔍</span>
                <h3 class="text-sm font-bold text-white uppercase">{{ selectedInspectTile.name }}</h3>
            </div>

            <img :src="selectedInspectTile.thumbnail_b64" class="w-full h-64 object-contain rounded-lg bg-black border border-gray-700" />

            <div class="bg-gray-800 p-3 rounded-lg text-xs space-y-1">
                <p><strong class="text-gray-400">Category:</strong> <span class="text-cyan-400 font-mono">{{ selectedInspectTile.category }}</span></p>
                <p><strong class="text-gray-400">Description:</strong> <span class="text-gray-200">{{ selectedInspectTile.description }}</span></p>
                <p v-if="selectedInspectTile.similarity_score"><strong class="text-gray-400">Similarity Score:</strong> <span class="text-amber-400 font-mono font-bold">{{ selectedInspectTile.similarity_score }}%</span></p>
                <p v-if="selectedInspectTile.raw_cosine_similarity"><strong class="text-gray-400">Cosine Similarity:</strong> <span class="text-cyan-300 font-mono">{{ selectedInspectTile.raw_cosine_similarity }}</span></p>
            </div>
        </div>
    </div>
</template>

<style scoped>
.semantic-retrieval-panel {
    position: relative;
    width: 580px;
    min-width: 360px;
    max-width: 850px;
    min-height: 280px;
    max-height: 85vh;
    resize: both;
    overflow: auto;
    box-sizing: border-box;
    z-index: 100;
}

.semantic-retrieval-panel.is-minimized {
    min-height: auto;
    height: auto;
    resize: none;
}

.panel-drag-handle {
    cursor: move;
    user-select: none;
    touch-action: none;
}

.panel-drag-handle:active {
    cursor: grabbing;
}

.semantic-retrieval-panel::-webkit-resizer {
    background-color: rgba(6, 182, 212, 0.25);
    border-radius: 2px;
}

.semantic-retrieval-panel.is-minimized::-webkit-resizer {
    display: none;
}

button,
input {
    touch-action: auto;
}

.overflow-y-auto::-webkit-scrollbar,
.semantic-retrieval-panel::-webkit-scrollbar {
    width: 5px;
    height: 5px;
}
.overflow-y-auto::-webkit-scrollbar-track,
.semantic-retrieval-panel::-webkit-scrollbar-track {
    background: #111827;
}
.overflow-y-auto::-webkit-scrollbar-thumb,
.semantic-retrieval-panel::-webkit-scrollbar-thumb {
    background: #374151;
    border-radius: 3px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover,
.semantic-retrieval-panel::-webkit-scrollbar-thumb:hover {
    background: #4b5563;
}
</style>
