<!-- frontend/src/components/common/NotificationDropdown.vue -->
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useProjectStore } from '@/stores/ProjectStore.js';
import { useRouter } from 'vue-router';

const projectStore = useProjectStore();
const router = useRouter();

// UI State
const dropdownRef = ref(null);
const isDropdownOpen = ref(false);
const expandedAlertIds = ref([]);

// Computed: Alerts list from the store
const alerts = computed(() => projectStore.activeAlerts);
const totalAlerts = computed(() => projectStore.totalAlerts);

// Toggle the dropdown visibility
const toggleDropdown = () => {
    isDropdownOpen.value = !isDropdownOpen.value;
};

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
    if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
        isDropdownOpen.value = false;
    }
};

const toggleExpand = (alertId) => {
    const index = expandedAlertIds.value.indexOf(alertId);
    if (index === -1) {
        expandedAlertIds.value.push(alertId);
    } else {
        expandedAlertIds.value.splice(index, 1);
    }
};

/**
 * Handles marking an alert as read and removing it from Redis and the local store.
 * @param {Object} alert The alert object to mark as read.
 */
const markAsRead = async (alert) => {
    const alertToRevert = alert;

    // Optimistic Update (Remove locally)
    projectStore.activeAlerts = projectStore.activeAlerts.filter(a => a.id !== alert.id);

    try {
        await projectStore.markAlertAsRead(alert.id);
    } catch (error) {
        console.error("Failed to mark alert as read on server:", error);

        if (!projectStore.activeAlerts.some(a => a.id === alertToRevert.id)) {
            // Re-add only if it's not somehow back in the list
            projectStore.activeAlerts.unshift(alertToRevert);
        }
    }
};

/**
 * Handles navigation when the main text area is clicked.
 * @param {Object} alert
 */
const handleNavigationClick = (alert) => {
    if (alert.projectId) {
        router.push({ name: 'monitor-map', params: { id: alert.projectId } });
        isDropdownOpen.value = false; // Close dropdown after navigation
    }
};

/**
 * Handles the full click action on an alert (mark read and potentially navigate).
 * @param {Object} alert
 */
const handleAlertClick = (alert) => {
    markAsRead(alert);

    if (alert.projectId) {
        router.push({ name: 'monitor-map', params: { id: alert.projectId } });
        isDropdownOpen.value = false; // Close dropdown after navigation
    }
};

// Function remains functionally the same, processing the 'message' field (which contains 'content')
const normalizeMessage = (msg) => {
    if (!msg) return {};

    // If already parsed JSON object
    if (typeof msg === 'object') return msg;

    // If it's a JSON string, try parsing:
    try {
        return JSON.parse(msg);
    } catch {
        return { message: msg }; // fallback to show raw string
    }
};

const formatMessage = (msg) => {
    const data = normalizeMessage(msg);

    return Object.entries(data).map(([key, value]) => ({
        key,
        value: typeof value === 'object' ? JSON.stringify(value, null, 2) : value
    }));
};

// Lifecycle hooks
onMounted(() => {
    document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
    document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
    <div ref="dropdownRef" class="notification-container z-[200] relative inline-block">

        <button @click="toggleDropdown" class="relative transition-colors duration-200 px-2 py-1 z-[2000] rounded-full"
            :class="{ 'text-white': totalAlerts > 0, 'text-gray-400': totalAlerts === 0 }" title="View Notifications"
            style="color: var(--text-muted); background-color: #0f172a;">
            <svg class="w-[4vh] h-[4vh]" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9">
                </path>
            </svg>

            <span v-if="totalAlerts > 0"
                class="absolute top-1 right-1 bg-red-600 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
                {{ totalAlerts > 99 ? '99+' : totalAlerts }}
            </span>
        </button>

        <!-- Dropdown Menu with Transition -->
        <Transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95">
            <div v-if="isDropdownOpen" 
                class="absolute bg-black rounded-lg shadow-xl ring-1 ring-gray ring-opacity-5 w-72 sm:w-80 right-0 max-w-[calc(100vw-20px)]">
                <div class="p-3 flex items-center justify-between border-b border-gray-600">

                    <h3 class="text-lg font-semibold text-white flex-grow text-center">
                        Alerts
                    </h3>

                    <div class="p-1.5 border-red-600 bg-red-600 rounded-lg text-xs">
                        <a @click="isDropdownOpen = false" class="cursor-pointer hover:text-white text-white">
                            Close
                        </a>
                    </div>
                </div>

                <div class="max-h-80 overflow-y-auto">
                    <div v-if="totalAlerts === 0" class="p-4 text-gray-400 text-left">
                        No new alerts.
                    </div>

                    <div v-for="alert in alerts" :key="alert.id"
                        class="flex flex-col border-b border-gray-600 transition duration-150">
                        <div class="flex items-start justify-between p-3">

                            <div @click="handleNavigationClick(alert)" class="flex-grow pr-3 cursor-pointer">
                                <p class="text-sm font-bold text-cyan-100 text-left break-words">
                                    <span class="text-red">{{ alert.project_name || alert.projectId }}</span>:
                                    <span class="text-olive">{{ alert.aoi_name || alert.aoiId }}</span> has an
                                    Alert for <span class="text-green">{{ alert.channelName }}</span>
                                </p>
                                <p class="text-xs text-start text-white mt-1 ">
                                    {{ new Date(alert.timestamp).toLocaleTimeString() }} {{ new
                                        Date(alert.timestamp).toLocaleDateString() }}
                                </p>
                            </div>


                            <div class="flex flex-col space-y-2 items-center flex-shrink-0">
                                <button @click.stop="markAsRead(alert)"
                                    class="text-red-400 hover:text-red-300 p-1 rounded-full w-6 h-6 flex items-center justify-center"
                                    title="Dismiss Alert">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                                        xmlns="http://www.w3.org/2000/svg">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M6 18L18 6M6 6l12 12"></path>
                                    </svg>
                                </button>

                                <button @click.stop="toggleExpand(alert.id)"
                                    class="text-gray-400 hover:text-white p-1 rounded-full w-6 h-6 flex items-center justify-center transition duration-200"
                                    :title="expandedAlertIds.includes(alert.id) ? 'Collapse Details' : 'Expand Details'">
                                    <svg class="w-4 h-4 transition-transform duration-200"
                                        :class="{ 'rotate-180': expandedAlertIds.includes(alert.id) }" fill="none"
                                        stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M19 9l-7 7-7-7"></path>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <div v-if="expandedAlertIds.includes(alert.id)"
                            class="p-3 pt-0 bg-gray-600/50 text-white border-t border-gray-600">

                            <p class="text-xs font-semibold mb-1 text-cyan-200">Alert Details:</p>

                            <div class="max-h-40 text-left overflow-y-auto space-y-1 p-2 bg-gray-700 rounded">
                                <div v-for="{ key, value } in formatMessage(alert.message)" :key="key"
                                    class="text-xs leading-tight">
                                    <span class="font-semibold text-cyan-300">{{ key }}:</span>
                                    <span class="text-gray-200 break-words ml-1">{{ value }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Transition>
    </div>
</template>

<style scoped>
.text-red {
    color: red !important;
}

.text-olive {
    color: olivedrab;
}

.text-green {
    color: yellow;
}
</style>