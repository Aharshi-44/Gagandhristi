<!-- frontend/src/components/map/AoiVizPanel.vue - SCATTER PLOT VERSION -->
<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import Highcharts from 'highcharts';
import { ApiClient } from '@/api/backendAPIendpoint.js';

const apiClient = ApiClient.getInstance();

const props = defineProps({
    isVisible: Boolean,
    projectId: [Number, String],
    selectedAoi: { type: Object, default: null },
    projectAlerts: { type: Array, default: () => [] },
    alertTimeRange: { type: Object, default: () => ({ from: null, to: null }) }
});

const emit = defineEmits(['close']);

const selectedChannelIds = ref([]);
const CHANNEL_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];
const channelColorMap = ref({});

const chartElement = ref(null);
let chartInstance = null;

const showAlertModal = ref(false);
const currentAlertDetails = ref(null);
const isLoadingChart = ref(false);

// --- PS 2.2.5 ANALYST REVIEW & DOSSIER STATE ---
const selectedReviewStatus = ref('CONFIRMED');
const reviewConfidence = ref('HIGH');
const analystNotes = ref('');
const isSubmittingReview = ref(false);
const reviewSuccessMsg = ref('');
const reviewErrorMsg = ref('');

// Dossier State
const showDossierModal = ref(false);
const dossierData = ref(null);
const isLoadingDossier = ref(false);
const dossierError = ref('');

// --- COMPUTED DATA ---

// Get unique alert channels for the selected AOI
const availableChannels = computed(() => {
    if (!props.selectedAoi || !props.selectedAoi.subscriptions) {
        console.log('[AoiVizPanel] No selectedAoi or subscriptions');
        return [];
    }

    const channels = new Map();
    let colorIndex = 0;

    props.selectedAoi.subscriptions.forEach(sub => {
        if (!channels.has(sub.channelId)) {
            const color = CHANNEL_COLORS[colorIndex % CHANNEL_COLORS.length];
            channels.set(sub.channelId, {
                channelId: sub.channelId,
                channelName: sub.channelName,
                category: sub.category,
                color: color
            });
            channelColorMap.value[sub.channelId] = color;
            colorIndex++;
        }
    });

    const result = Array.from(channels.values());
    console.log('[AoiVizPanel] Available channels:', result);
    return result;
});

// Process alerts into series data for Highcharts - SCATTER PLOT VERSION
const chartSeriesData = computed(() => {
    console.log('[AoiVizPanel] Computing chart data...', {
        hasAlerts: props.projectAlerts?.length > 0,
        alertCount: props.projectAlerts?.length,
        hasAoi: !!props.selectedAoi,
        selectedChannels: selectedChannelIds.value.length
    });

    if (!props.projectAlerts || props.projectAlerts.length === 0) {
        console.log('[AoiVizPanel] No alerts');
        return [];
    }

    if (!props.selectedAoi || selectedChannelIds.value.length === 0) {
        console.log('[AoiVizPanel] No AOI or no channels selected');
        return [];
    }

    const dataMap = new Map();

    // Initialize series for each selected channel
    const selectedChannels = availableChannels.value.filter(ch =>
        selectedChannelIds.value.includes(ch.channelId)
    );

    console.log('[AoiVizPanel] Initializing series for channels:', selectedChannels);

    selectedChannels.forEach(channel => {
        const seriesId = `${props.selectedAoi.aoi_id}_${channel.channelId}`;
        dataMap.set(seriesId, {
            id: seriesId,
            name: `${props.selectedAoi.name} / ${channel.channelName}`,
            data: [],
            color: channel.color,
            aoiId: props.selectedAoi.aoi_id,
            channelId: channel.channelId,
            type: 'scatter', // Changed to scatter
        });
    });

    // Filter alerts for selected AOI and channels
    const filteredAlerts = props.projectAlerts.filter(alert => {
        const match = alert.aoiId === props.selectedAoi.aoi_id &&
            selectedChannelIds.value.includes(alert.channelId);
        if (match) {
            console.log('[AoiVizPanel] Alert matched:', alert);
        }
        return match;
    });

    console.log('[AoiVizPanel] Filtered alerts:', filteredAlerts.length);

    // Populate series with alert data - SCATTER POINTS ONLY
    filteredAlerts.forEach(alert => {
        const seriesId = `${alert.aoiId}_${alert.channelId}`;
        const series = dataMap.get(seriesId);

        if (series) {
            const timestamp = new Date(alert.timestamp).getTime();

            // Add single point for each alert
            series.data.push({
                x: timestamp,
                y: 1,
                alertDetails: alert,
                marker: {
                    enabled: true,
                    radius: 6,
                    symbol: 'circle',
                    lineWidth: 2,
                    lineColor: '#ffffff'
                }
            });
        }
    });

    const allSeries = Array.from(dataMap.values());
    const result = allSeries.filter(s => s.data.length > 0);

    console.log('[AoiVizPanel] Final series count:', result.length);
    return result;
});

// Highcharts configuration - SCATTER PLOT VERSION
const chartOptions = computed(() => {
    const minTime = props.alertTimeRange?.from ? props.alertTimeRange.from - 1 * 60 * 1000 : undefined;
    const maxTime = props.alertTimeRange?.to ? props.alertTimeRange.to + 1 * 60 * 1000 : undefined;
    const chartHeight = window.innerHeight * 0.30;

    return {
        chart: {
            type: 'scatter',
            zoomType: 'x',
            backgroundColor: '#1f2937',
            height: chartHeight,
            animation: true,
        },
        title: {
            text: null,
        },
        credits: {
            enabled: false
        },
        xAxis: {
            type: 'datetime',
            min: minTime,
            max: maxTime,
            title: {
                text: 'Timeline',
                style: { color: '#9ca3af', fontWeight: 'bold' }
            },
            labels: { style: { color: '#d1d5db' }, format: '{value:%e %b %H:%M}' },
            gridLineColor: '#374151'
        },
        yAxis: {
            title: {
                text: 'Alert Status',
                style: { color: '#9ca3af', fontWeight: 'bold' }
            },
            labels: {
                style: { color: '#d1d5db' },
                formatter: function () {
                    return this.value === 1 ? 'Yes' : 'No';
                }
            },
            min: 0,
            max: 1.5,
            tickPositions: [0, 1],
            gridLineColor: '#374151'
        },
        tooltip: {
            backgroundColor: '#111827',
            borderColor: '#4b5563',
            style: { color: '#f3f4f6' },
            useHTML: true,
            formatter: function () {
                const alertData = this.point.options.alertDetails;

                if (alertData) {
                    const time = Highcharts.dateFormat('%A, %b %e, %Y, %H:%M:%S', this.x);
                    return `
                        <div style="padding: 8px;">
                            <div style="font-size: 11px; color: #9ca3af;">${time}</div>
                            <div style="margin-top: 4px;">
                                <span style="color:${this.point.color}">●</span>
                                <strong>${this.series.name}</strong>
                            </div>
                            <div style="margin-top: 4px; font-size: 11px; color: #fbbf24;">
                                🔔 Alert Detected
                            </div>
                            <div style="margin-top: 2px; font-size: 10px; color: #9ca3af;">
                                Click for details
                            </div>
                        </div>
                    `;
                }
                return `<div style="padding: 8px;"><strong>${this.series.name}</strong></div>`;
            }
        },
        legend: {
            enabled: false
        },
        plotOptions: {
            scatter: {
                cursor: 'pointer',
                marker: {
                    enabled: true,
                    radius: 6,
                    symbol: 'circle',
                    states: {
                        hover: {
                            enabled: true,
                            radius: 8,
                            lineWidth: 3
                        }
                    }
                },
                states: {
                    hover: {
                        enabled: true
                    }
                },
                point: {
                    events: {
                        click: function () {
                            if (this.options.alertDetails) {
                                handlePointClick(this.options.alertDetails);
                            }
                        }
                    }
                }
            }
        },
        series: chartSeriesData.value
    };
});

// --- ACTIONS ---

const toggleChannelSelection = (channelId) => {
    const index = selectedChannelIds.value.indexOf(channelId);
    if (index > -1) {
        selectedChannelIds.value.splice(index, 1);
    } else {
        selectedChannelIds.value.push(channelId);
    }
    console.log('[AoiVizPanel] Selected channels:', selectedChannelIds.value);
};

const handlePointClick = (alertDetails) => {
    currentAlertDetails.value = alertDetails;
    selectedReviewStatus.value = alertDetails.reviewStatus && alertDetails.reviewStatus !== 'PENDING'
        ? alertDetails.reviewStatus
        : 'CONFIRMED';
    reviewConfidence.value = alertDetails.confidenceRating || 'HIGH';
    analystNotes.value = alertDetails.reviewNotes || '';
    reviewSuccessMsg.value = '';
    reviewErrorMsg.value = '';
    showAlertModal.value = true;
};

// PS 2.2.5 Analyst Review Action
const submitReview = async (statusOverride = null) => {
    if (!currentAlertDetails.value) return;
    const statusToSave = statusOverride || selectedReviewStatus.value;
    selectedReviewStatus.value = statusToSave;
    isSubmittingReview.value = true;
    reviewSuccessMsg.value = '';
    reviewErrorMsg.value = '';

    try {
        const reviewData = {
            review_status: statusToSave,
            confidence_rating: reviewConfidence.value,
            notes: analystNotes.value
        };
        await apiClient.reviewAlert(currentAlertDetails.value.id, reviewData);

        // Optimistically update current modal
        currentAlertDetails.value.reviewStatus = statusToSave;
        currentAlertDetails.value.reviewNotes = analystNotes.value;
        currentAlertDetails.value.confidenceRating = reviewConfidence.value;
        currentAlertDetails.value.reviewerId = apiClient.getUserId() || 'DEFENCE_ANALYST';
        currentAlertDetails.value.reviewedAt = new Date().toISOString();

        // Also update in projectAlerts reactive array
        const existing = props.projectAlerts.find(a => a.id === currentAlertDetails.value.id);
        if (existing) {
            existing.reviewStatus = statusToSave;
            existing.reviewNotes = analystNotes.value;
            existing.confidenceRating = reviewConfidence.value;
            existing.reviewerId = currentAlertDetails.value.reviewerId;
            existing.reviewedAt = currentAlertDetails.value.reviewedAt;
        }

        reviewSuccessMsg.value = `Alert marked as ${statusToSave.replace('_', ' ')}!`;
        setTimeout(() => {
            reviewSuccessMsg.value = '';
        }, 4000);
    } catch (err) {
        console.error('Error submitting review:', err);
        reviewErrorMsg.value = err.response?.data?.error || err.message || 'Failed to submit review';
    } finally {
        isSubmittingReview.value = false;
    }
};

// PS 2.2.5 Military Intel Dossier
const openDossier = async () => {
    if (!currentAlertDetails.value) return;
    isLoadingDossier.value = true;
    showDossierModal.value = true;
    dossierError.value = '';
    dossierData.value = null;

    try {
        const res = await apiClient.getAlertDossier(currentAlertDetails.value.id);
        dossierData.value = res.dossier;
    } catch (err) {
        console.error('Error loading dossier:', err);
        dossierError.value = err.response?.data?.error || err.message || 'Failed to load intelligence dossier';
    } finally {
        isLoadingDossier.value = false;
    }
};

const printDossier = () => {
    window.print();
};

const selectAllChannels = () => {
    selectedChannelIds.value = availableChannels.value.map(ch => ch.channelId);
};

const deselectAllChannels = () => {
    selectedChannelIds.value = [];
};

// Add this function in your script setup section, after the other functions

const formatValue = (value) => {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (typeof value === 'object') {
        // For nested objects/arrays, convert to readable string without brackets
        if (Array.isArray(value)) {
            return value.join(', ');
        }
        // For nested objects, show as "key: value" pairs
        return Object.entries(value).map(([k, v]) => `${k}: ${v}`).join('; ');
    }
    return String(value);
};

// Chart management
const updateChart = () => {
    if (!props.isVisible || !chartElement.value) {
        console.log('[AoiVizPanel] Skipping chart update - not visible or no element');
        return;
    }

    isLoadingChart.value = true;

    setTimeout(() => {
        console.log('[AoiVizPanel] Updating chart with series count:', chartSeriesData.value.length);

        if (chartSeriesData.value.length > 0) {
            if (chartInstance) {
                chartInstance.update(chartOptions.value, true, true);
            } else {
                chartInstance = Highcharts.chart(chartElement.value, chartOptions.value);
            }
        } else if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }
        isLoadingChart.value = false;
    }, 100);
};

const destroyChart = () => {
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }
};

// --- LIFECYCLE ---

onMounted(() => {
    console.log('[AoiVizPanel] Mounted');
});

onBeforeUnmount(() => {
    destroyChart();
});

// Watch for changes
watch(() => props.isVisible, (newVal) => {
    console.log('[AoiVizPanel] Visibility changed:', newVal);
    if (!newVal) {
        destroyChart();
    } else {
        updateChart();
    }
});

watch([selectedChannelIds], () => {
    console.log('[AoiVizPanel] Selected channels changed');
    if (props.isVisible) {
        updateChart();
    }
}, { deep: true });

watch([() => props.projectAlerts, () => props.alertTimeRange], () => {
    console.log('[AoiVizPanel] Alerts or time range changed');
    if (props.isVisible) updateChart();
}, { deep: true });

watch([chartSeriesData, () => props.isVisible], () => {
    console.log('[AoiVizPanel] Chart data or visibility changed');
    if (props.isVisible) {
        updateChart();
    }
}, { deep: true });

watch(() => props.selectedAoi, (newAoi) => {
    console.log('[AoiVizPanel] Selected AOI changed:', newAoi);
    if (newAoi) {
        selectedChannelIds.value = availableChannels.value.map(ch => ch.channelId);
        console.log('[AoiVizPanel] Auto-selected channels:', selectedChannelIds.value);
        if (props.isVisible) {
            updateChart();
        }
    }
}, { immediate: true, deep: true });

watch(availableChannels, (newChannels) => {
    console.log('[AoiVizPanel] Available channels changed:', newChannels);
    if (newChannels.length > 0 && selectedChannelIds.value.length === 0) {
        selectedChannelIds.value = newChannels.map(ch => ch.channelId);
        console.log('[AoiVizPanel] Auto-selected channels:', selectedChannelIds.value);
    }
}, { immediate: true });
</script>

<template>
    <div v-if="isVisible"
        class="fixed bottom-0 left-0 right-0 bg-gray-800 shadow-2xl border-t-4 border-cyan-500 transition-all duration-300"
        style=" z-index: 1000;">

        <!-- Close Button -->
        <button @click="$emit('close')"
            class="absolute top-2 right-2 text-red-400 hover:text-red-300 text-3xl font-bold z-20 w-8 h-8 flex items-center justify-center"
            title="Close Panel">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="4" y1="4" x2="20" y2="20" stroke="currentColor" stroke-width="2" />
                <line x1="20" y1="4" x2="4" y2="20" stroke="currentColor" stroke-width="2" />
            </svg>
        </button>

        <!-- Main Content -->
        <div class="flex flex-col">
            <!-- AOI Title -->
            <div v-if="selectedAoi" class="flex-shrink-0 h-[6vh] bg-gray-700 rounded-lg p-2">
                <h3 class="text-cyan-400 font-bold text-lg">
                    {{ selectedAoi.name }}
                </h3>
            </div>

            <!-- Chart Area -->
            <div class=" bg-gray-900 rounded-lg p-2 h-[32vh] relative overflow-hidden">
                <div v-if="isLoadingChart"
                    class=" inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75 z-10">
                    <div class="text-cyan-400 text-lg">Loading chart...</div>
                </div>

                <div ref="chartElement" v-show="chartSeriesData.length > 0 && !isLoadingChart" class="w-full h-[30vh]">
                </div>

                <div v-if="!isLoadingChart && chartSeriesData.length === 0"
                    class="flex items-center justify-center text-gray-400 text-center h-[32vh]">
                    <div>
                        <svg class="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor"
                            viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z">
                            </path>
                        </svg>
                        <p class="text-lg font-semibold">No Data to Display</p>
                        <p class="text-sm mt-2">
                            {{ projectAlerts.length === 0
                                ? 'No alerts found for this AOI'
                                : 'Select alert channels to view alerts' }}
                        </p>
                    </div>
                </div>
            </div>

            <!-- Alert Channel Legend -->
            <div
                class="flex-shrink-0 bg-gray-700 h-[10vh] my-1 rounded-lg p-2 max-h-[120px] overflow-hidden flex flex-col">
                <div class="flex justify-between h-[2vh] items-center">
                    <label class="text-gray-300 text-sm font-semibold">Alert Channels:</label>
                </div>
                <div class="flex h-[6vhv] p-2 flex-wrap gap-2 overflow-y-auto">
                    <label v-for="channel in availableChannels" :key="channel.channelId"
                        class="flex items-center space-x-2 text-xs cursor-pointer transition-all px-2 py-1 bg-gray-600 rounded whitespace-nowrap"
                        :class="selectedChannelIds.includes(channel.channelId) ? 'text-white ring-2 ring-cyan-500' : 'text-gray-400'"
                        :title="`${channel.category} - ${channel.channelName}`">
                        <input type="checkbox" :value="channel.channelId"
                            :checked="selectedChannelIds.includes(channel.channelId)"
                            @change="toggleChannelSelection(channel.channelId)"
                            class="rounded text-cyan-500 bg-gray-700 border-gray-600 focus:ring-cyan-500">
                        <div class="w-3 h-3 rounded-full flex-shrink-0" :style="{ backgroundColor: channel.color }">
                        </div>
                        <span class="font-medium">{{ channel.channelName }}</span>
                    </label>
                </div>
            </div>
        </div>
    </div>

    <!-- Alert Details Modal (with PS 2.2.5 Analyst Verification & Dossier Export) -->
    <div v-if="showAlertModal && currentAlertDetails"
        class="fixed inset-0 bg-black bg-opacity-75 z-[30000] flex justify-center items-center p-4"
        @click.self="showAlertModal = false">
        <div
            class="bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-2xl relative border-2 border-cyan-500 max-h-[88vh] overflow-y-auto">
            <button @click="showAlertModal = false"
                class="absolute top-3 right-3 text-gray-400 hover:text-red-400 text-2xl font-bold px-2 py-1">
                ✕
            </button>

            <!-- Modal Header with Verification Badge -->
            <div class="flex items-center justify-between border-b border-gray-700 pb-3 mb-4">
                <div class="flex items-center space-x-3">
                    <span class="text-2xl">🔔</span>
                    <h3 class="text-xl text-white font-bold">
                        Alert #{{ currentAlertDetails.id }} Overview
                    </h3>
                </div>

                <!-- Status Badge -->
                <div>
                    <span v-if="currentAlertDetails.reviewStatus === 'CONFIRMED'"
                        class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-950 text-emerald-400 border border-emerald-500 flex items-center gap-1.5 shadow-sm">
                        <span>●</span> CONFIRMED ANOMALY
                    </span>
                    <span v-else-if="currentAlertDetails.reviewStatus === 'FALSE_ALARM'"
                        class="px-3 py-1 rounded-full text-xs font-bold bg-amber-950 text-amber-400 border border-amber-500 flex items-center gap-1.5 shadow-sm">
                        <span>⚠</span> FALSE ALARM
                    </span>
                    <span v-else-if="currentAlertDetails.reviewStatus === 'REJECTED'"
                        class="px-3 py-1 rounded-full text-xs font-bold bg-rose-950 text-rose-400 border border-rose-500 flex items-center gap-1.5 shadow-sm">
                        <span>✕</span> REJECTED
                    </span>
                    <span v-else
                        class="px-3 py-1 rounded-full text-xs font-bold bg-yellow-950/60 text-yellow-300 border border-yellow-500/60 flex items-center gap-1.5 animate-pulse">
                        <span>◌</span> PENDING REVIEW
                    </span>
                </div>
            </div>

            <div class="space-y-4">
                <!-- AOI & Metadata Grid -->
                <div class="bg-gray-700/80 p-4 rounded-lg border border-gray-600">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <p class="text-gray-400 text-xs uppercase font-medium">Project</p>
                            <p class="text-white font-semibold text-sm">{{ currentAlertDetails.projectName }}</p>
                        </div>
                        <div>
                            <p class="text-gray-400 text-xs uppercase font-medium">Area of Interest (AOI)</p>
                            <p class="text-white font-semibold text-sm">{{ currentAlertDetails.aoiName }}</p>
                        </div>
                        <div>
                            <p class="text-gray-400 text-xs uppercase font-medium">Detection Model / Channel</p>
                            <p class="text-cyan-400 font-semibold text-sm">{{ currentAlertDetails.channelName }}</p>
                        </div>
                        <div>
                            <p class="text-gray-400 text-xs uppercase font-medium">Timestamp</p>
                            <p class="text-white font-semibold text-sm">
                                {{ new Date(currentAlertDetails.timestamp).toLocaleString() }}
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Alert Content & Metrics -->
                <div class="bg-gray-900 p-4 rounded-lg border border-gray-700">
                    <p class="text-gray-400 text-xs uppercase font-medium mb-2">Automated Detection Payload:</p>
                    <div class="bg-gray-800/90 p-3 rounded text-sm text-yellow-300 space-y-1.5 font-mono">
                        <template
                            v-if="typeof currentAlertDetails.message === 'object' && currentAlertDetails.message !== null">
                            <div v-for="(value, key) in currentAlertDetails.message" :key="key" class="flex justify-between items-start border-b border-gray-700/50 py-1 last:border-none">
                                <span class="text-gray-400 font-medium text-xs">{{ key }}:</span>
                                <span class="text-yellow-300 text-xs text-right font-semibold ml-2">{{ formatValue(value) }}</span>
                            </div>
                        </template>
                        <template v-else>
                            <div class="text-yellow-300 text-xs">{{ currentAlertDetails.message }}</div>
                        </template>
                    </div>
                </div>

                <!-- PS 2.2.5: OPERATIONAL ANALYST VERIFICATION PANEL -->
                <div class="bg-gray-700/60 p-4 rounded-lg border border-cyan-500/40 space-y-3">
                    <div class="flex items-center justify-between">
                        <h4 class="text-cyan-400 text-sm font-bold uppercase tracking-wider flex items-center gap-1.5">
                            <span>🛡️</span> Human-in-the-Loop Analyst Verification
                        </h4>
                        <span v-if="currentAlertDetails.reviewedAt" class="text-[11px] text-gray-400">
                            Last reviewed by <strong class="text-gray-200">{{ currentAlertDetails.reviewerId || 'Analyst' }}</strong> on {{ new Date(currentAlertDetails.reviewedAt).toLocaleDateString() }}
                        </span>
                    </div>

                    <!-- Quick Action Buttons -->
                    <div class="grid grid-cols-3 gap-2">
                        <button type="button"
                            @click="submitReview('CONFIRMED')"
                            :disabled="isSubmittingReview"
                            class="px-3 py-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 border"
                            :class="currentAlertDetails.reviewStatus === 'CONFIRMED' 
                                ? 'bg-emerald-600 text-white border-emerald-400 ring-2 ring-emerald-500/50' 
                                : 'bg-gray-800 text-emerald-300 border-emerald-800 hover:bg-emerald-950/80'">
                            <span>✓</span> Confirm Anomaly
                        </button>
                        <button type="button"
                            @click="submitReview('FALSE_ALARM')"
                            :disabled="isSubmittingReview"
                            class="px-3 py-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 border"
                            :class="currentAlertDetails.reviewStatus === 'FALSE_ALARM' 
                                ? 'bg-amber-600 text-white border-amber-400 ring-2 ring-amber-500/50' 
                                : 'bg-gray-800 text-amber-300 border-amber-800 hover:bg-amber-950/80'">
                            <span>⚠</span> Mark False Alarm
                        </button>
                        <button type="button"
                            @click="submitReview('REJECTED')"
                            :disabled="isSubmittingReview"
                            class="px-3 py-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 border"
                            :class="currentAlertDetails.reviewStatus === 'REJECTED' 
                                ? 'bg-rose-600 text-white border-rose-400 ring-2 ring-rose-500/50' 
                                : 'bg-gray-800 text-rose-300 border-rose-800 hover:bg-rose-950/80'">
                            <span>✕</span> Reject Alert
                        </button>
                    </div>

                    <!-- Confidence Rating and Notes -->
                    <div class="space-y-2 pt-1">
                        <div class="flex items-center justify-between text-xs">
                            <label class="text-gray-300 font-medium">Analyst Tactical Remarks / Notes:</label>
                            <div class="flex items-center gap-2">
                                <span class="text-gray-400">Confidence:</span>
                                <select v-model="reviewConfidence"
                                    class="bg-gray-800 border border-gray-600 rounded px-2 py-0.5 text-xs text-white focus:ring-1 focus:ring-cyan-500">
                                    <option value="HIGH">HIGH (Definitive)</option>
                                    <option value="MEDIUM">MEDIUM (Probable)</option>
                                    <option value="LOW">LOW (Uncertain)</option>
                                </select>
                            </div>
                        </div>
                        <textarea v-model="analystNotes"
                            rows="2"
                            placeholder="Add intelligence remarks, tactical assessment, or target classification notes..."
                            class="w-full bg-gray-900 border border-gray-600 rounded-lg p-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"></textarea>

                        <div class="flex items-center justify-between pt-1">
                            <button type="button"
                                @click="submitReview()"
                                :disabled="isSubmittingReview"
                                class="px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded shadow transition disabled:opacity-50">
                                {{ isSubmittingReview ? 'Saving Assessment...' : '💾 Save Assessment' }}
                            </button>

                            <span v-if="reviewSuccessMsg" class="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                                <span>✓</span> {{ reviewSuccessMsg }}
                            </span>
                            <span v-if="reviewErrorMsg" class="text-xs text-rose-400 font-semibold">
                                {{ reviewErrorMsg }}
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Export Intelligence Dossier Button -->
                <div class="pt-2 border-t border-gray-700 flex justify-end gap-3">
                    <button type="button"
                        @click="openDossier"
                        class="px-4 py-2 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white text-xs font-bold rounded-lg shadow-lg flex items-center gap-2 transition transform active:scale-95 border border-amber-400/50">
                        <span>📄</span> Export Military Intel Dossier (SITREP)
                    </button>
                    <button type="button"
                        @click="showAlertModal = false"
                        class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs font-bold rounded-lg transition">
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- PS 2.2.5: MILITARY INTELLIGENCE DOSSIER / SITREP MODAL -->
    <div v-if="showDossierModal"
        class="fixed inset-0 bg-black bg-opacity-85 z-[40000] flex justify-center items-center p-4 overflow-y-auto"
        @click.self="showDossierModal = false">
        <div class="bg-gray-900 rounded-xl shadow-2xl p-6 w-full max-w-4xl relative border-2 border-amber-500/80 max-h-[92vh] overflow-y-auto dossier-print-container">
            
            <!-- Close & Print Action Header (Hidden in Print) -->
            <div class="flex justify-between items-center pb-3 border-b border-gray-700 no-print">
                <div class="flex items-center gap-2">
                    <span class="text-amber-400 text-lg">🛡️</span>
                    <span class="text-xs font-mono text-amber-400 tracking-wider font-bold">
                        GAGANDHRISTI DEFENCE INTELLIGENCE SYSTEM
                    </span>
                </div>
                <div class="flex items-center gap-3">
                    <button @click="printDossier"
                        class="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-bold flex items-center gap-1.5 shadow transition">
                        <span>🖨️</span> Print / Save PDF
                    </button>
                    <button @click="showDossierModal = false"
                        class="text-gray-400 hover:text-white text-xl font-bold px-2 py-1">
                        ✕
                    </button>
                </div>
            </div>

            <!-- Loading State -->
            <div v-if="isLoadingDossier" class="py-20 text-center">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-amber-400 border-t-transparent mb-3"></div>
                <p class="text-amber-300 text-sm font-semibold tracking-wide">Compiling Military Intelligence Dossier...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="dossierError" class="py-12 text-center text-rose-400">
                <p class="font-bold mb-2">Error Generating Dossier</p>
                <p class="text-xs">{{ dossierError }}</p>
            </div>

            <!-- Dossier Content -->
            <div v-else-if="dossierData" class="space-y-4 pt-3">
                <!-- Top Security Clearance Banner -->
                <div class="bg-red-950/80 border border-red-700 text-red-300 py-1.5 px-4 text-center rounded text-xs font-bold tracking-widest uppercase">
                    ★ {{ dossierData.classification }} ★
                </div>

                <!-- SITREP Document Header -->
                <div class="bg-gray-800 p-4 rounded-lg border border-gray-700 flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                    <div>
                        <p class="text-xs font-mono text-cyan-400 tracking-wider">DOC ID: {{ dossierData.dossier_id }}</p>
                        <h2 class="text-lg font-black text-white tracking-wide mt-0.5">
                            MILITARY INTELLIGENCE SITUATION REPORT (SITREP)
                        </h2>
                        <p class="text-xs text-gray-400">{{ dossierData.mission_title }}</p>
                    </div>
                    <div class="text-left md:text-right">
                        <p class="text-xs text-gray-400">GENERATED AT</p>
                        <p class="text-xs font-mono text-white font-semibold">{{ new Date(dossierData.generated_at).toUTCString() }}</p>
                        <span class="inline-block mt-1 px-2.5 py-0.5 rounded text-[11px] font-bold"
                            :class="dossierData.analyst_verification.status === 'CONFIRMED' ? 'bg-emerald-900 text-emerald-300' : 'bg-amber-900 text-amber-300'">
                            VERIFICATION: {{ dossierData.analyst_verification.status }}
                        </span>
                    </div>
                </div>

                <!-- Two-Column Operational Intel Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Column 1: Target AOI & Geographic Coordinates -->
                    <div class="bg-gray-800/90 p-4 rounded-lg border border-gray-700 space-y-2.5">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 border-b border-gray-700 pb-1.5 flex items-center gap-1.5">
                            <span>📍</span> Target AOI & Geospatial Extent
                        </h4>
                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <div>
                                <span class="text-gray-400 block text-[11px]">AOI Name:</span>
                                <span class="text-white font-bold">{{ dossierData.target_aoi.aoi_name }}</span>
                            </div>
                            <div>
                                <span class="text-gray-400 block text-[11px]">AOI ID:</span>
                                <span class="text-cyan-300 font-mono">{{ dossierData.target_aoi.aoi_id }}</span>
                            </div>
                            <div>
                                <span class="text-gray-400 block text-[11px]">Project:</span>
                                <span class="text-white font-medium">{{ dossierData.target_aoi.project_name }}</span>
                            </div>
                            <div>
                                <span class="text-gray-400 block text-[11px]">Project ID:</span>
                                <span class="text-cyan-300 font-mono">PRJ-{{ dossierData.target_aoi.project_id }}</span>
                            </div>
                        </div>

                        <!-- GeoJSON Geometry Summary -->
                        <div v-if="dossierData.target_aoi.aoi_geojson" class="bg-gray-900/80 p-2.5 rounded border border-gray-700/60 text-[11px]">
                            <span class="text-gray-400 font-medium block mb-1">Geospatial Geometry Type:</span>
                            <span class="text-yellow-300 font-mono">{{ dossierData.target_aoi.aoi_geojson.type }}</span>
                            <span class="text-gray-400 block mt-1">Coordinates Preview:</span>
                            <span class="text-gray-300 font-mono text-[10px] break-all block max-h-12 overflow-y-auto">
                                {{ JSON.stringify(dossierData.target_aoi.aoi_geojson.coordinates).substring(0, 150) }}...
                            </span>
                        </div>
                    </div>

                    <!-- Column 2: Detection Sensor & Change Algorithm -->
                    <div class="bg-gray-800/90 p-4 rounded-lg border border-gray-700 space-y-2.5">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-cyan-400 border-b border-gray-700 pb-1.5 flex items-center gap-1.5">
                            <span>🛰️</span> Detection Engine Profile
                        </h4>
                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <div>
                                <span class="text-gray-400 block text-[11px]">Channel:</span>
                                <span class="text-cyan-300 font-bold">{{ dossierData.sensor_and_algorithm.channel_name }}</span>
                            </div>
                            <div>
                                <span class="text-gray-400 block text-[11px]">Category:</span>
                                <span class="text-white font-semibold">{{ dossierData.sensor_and_algorithm.category }}</span>
                            </div>
                            <div>
                                <span class="text-gray-400 block text-[11px]">Script / Model:</span>
                                <span class="text-yellow-300 font-mono">{{ dossierData.sensor_and_algorithm.script_name }}</span>
                            </div>
                            <div>
                                <span class="text-gray-400 block text-[11px]">Detected:</span>
                                <span class="text-white">{{ new Date(dossierData.sensor_and_algorithm.detection_timestamp).toLocaleDateString() }}</span>
                            </div>
                        </div>

                        <!-- Model Description Callout -->
                        <div class="bg-gray-900/80 p-2.5 rounded border border-gray-700/60 text-[11px]">
                            <span class="text-gray-400 font-medium block mb-1">Surveillance Directive:</span>
                            <p class="text-gray-300 text-[11px]">
                                Automated multi-temporal satellite change analysis using the {{ dossierData.sensor_and_algorithm.channel_name }} analytic pipeline.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Quantitative Anomaly Metrics -->
                <div class="bg-gray-800/90 p-4 rounded-lg border border-gray-700">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-yellow-400 border-b border-gray-700 pb-1.5 mb-2.5 flex items-center gap-1.5">
                        <span>📊</span> Quantitative Change Metrics & Payload
                    </h4>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div v-for="(val, key) in dossierData.quantitative_metrics" :key="key"
                            class="bg-gray-900 p-2.5 rounded border border-gray-700/70">
                            <span class="text-gray-400 text-[11px] uppercase block font-medium">{{ key }}</span>
                            <span class="text-yellow-300 font-mono font-bold text-xs mt-1 block break-all">
                                {{ formatValue(val) }}
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Human-in-the-Loop Verification Sign-off -->
                <div class="bg-gray-800/90 p-4 rounded-lg border border-emerald-500/40 space-y-3">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 border-b border-gray-700 pb-1.5 flex items-center gap-1.5">
                        <span>✍️</span> Human-in-the-Loop Analyst Verification & Sign-off
                    </h4>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                        <div>
                            <span class="text-gray-400 block text-[11px]">Final Decision:</span>
                            <span class="font-bold" :class="dossierData.analyst_verification.status === 'CONFIRMED' ? 'text-emerald-400' : 'text-amber-400'">
                                {{ dossierData.analyst_verification.status }}
                            </span>
                        </div>
                        <div>
                            <span class="text-gray-400 block text-[11px]">Reviewing Officer:</span>
                            <span class="text-white font-semibold">{{ dossierData.analyst_verification.reviewer_id || 'Not Assigned' }}</span>
                        </div>
                        <div>
                            <span class="text-gray-400 block text-[11px]">Confidence Rating:</span>
                            <span class="text-cyan-300 font-semibold">{{ dossierData.analyst_verification.confidence_rating || 'N/A' }}</span>
                        </div>
                        <div>
                            <span class="text-gray-400 block text-[11px]">Review Timestamp:</span>
                            <span class="text-white font-mono text-[11px]">
                                {{ dossierData.analyst_verification.reviewed_at ? new Date(dossierData.analyst_verification.reviewed_at).toLocaleString() : 'PENDING' }}
                            </span>
                        </div>
                    </div>

                    <!-- Analyst Operational Remarks -->
                    <div class="bg-gray-900 p-3 rounded border border-gray-700">
                        <span class="text-gray-400 text-[11px] font-medium block mb-1">Analyst Intelligence Assessment:</span>
                        <p class="text-gray-200 text-xs italic">
                            "{{ dossierData.analyst_verification.notes || 'No remarks recorded at time of report generation.' }}"
                        </p>
                    </div>

                    <!-- Audit Trail (if multiple reviews) -->
                    <div v-if="dossierData.analyst_verification.audit_trail && dossierData.analyst_verification.audit_trail.length > 1"
                        class="pt-2">
                        <span class="text-gray-400 text-[11px] font-medium block mb-1">Audit Trail History:</span>
                        <div class="space-y-1 text-[11px]">
                            <div v-for="trail in dossierData.analyst_verification.audit_trail" :key="trail.id"
                                class="flex justify-between items-center bg-gray-900/60 px-2 py-1 rounded text-gray-300 font-mono text-[10px]">
                                <span>{{ trail.reviewer_id }} [{{ trail.status }}]</span>
                                <span>{{ new Date(trail.reviewed_at).toLocaleString() }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Bottom Security Classification Footer -->
                <div class="bg-red-950/80 border border-red-700 text-red-300 py-1.5 px-4 text-center rounded text-xs font-bold tracking-widest uppercase">
                    ★ {{ dossierData.classification }} ★
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.overflow-y-auto::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
    background: #1f2937;
    border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
    background: #4b5563;
    border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: #6b7280;
}

/* PS 2.2.5 Military Intel Dossier Print Formatting */
@media print {
    body * {
        visibility: hidden !important;
    }
    .dossier-print-container,
    .dossier-print-container * {
        visibility: visible !important;
    }
    .dossier-print-container {
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-height: none !important;
        background: #ffffff !important;
        color: #111827 !important;
        border: none !important;
        box-shadow: none !important;
        padding: 24px !important;
        overflow: visible !important;
    }
    .no-print {
        display: none !important;
    }
    .dossier-print-container .bg-gray-800,
    .dossier-print-container .bg-gray-800\/90,
    .dossier-print-container .bg-gray-900,
    .dossier-print-container .bg-gray-900\/80 {
        background: #f3f4f6 !important;
        color: #111827 !important;
        border-color: #d1d5db !important;
    }
    .dossier-print-container .text-white {
        color: #111827 !important;
    }
    .dossier-print-container .text-gray-400,
    .dossier-print-container .text-gray-300,
    .dossier-print-container .text-gray-200 {
        color: #374151 !important;
    }
    .dossier-print-container .bg-red-950\/80 {
        background: #fee2e2 !important;
        color: #991b1b !important;
        border-color: #f87171 !important;
    }
}
</style>