<!-- DisplayProjectUI.vue  -->

<script setup>
import { onMounted, ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectStore } from '@/stores/ProjectStore.js';
import CustomSelect from '../components/common/CustomSelect.vue';
import { UserSession } from '@/classes/UserSession.js';

const sortOptions = [
    { label: 'Sort by Name', value: 'project_name' },
    { label: 'Sort by Creation Date', value: 'creation_timestamp' },
    { label: 'Sort by Last Modified', value: 'last_modified_timestamp' },
];

const router = useRouter();
const route = useRoute();
const projectStore = useProjectStore();
const session = UserSession.getInstance();

// UI State
const isLoading = ref(true);
const errorMessage = ref('');
const isMonitorMode = computed(() => route.query.mode === 'monitor');
const showSortDropdown = ref(false); // NEW: Control dropdown visibility

// Filter/Search State
const searchTerm = ref('');
const filterStatus = ref('');
const filterDate = ref('');

// Sorting State - DEFAULT: creation_timestamp
const sortCriteria = ref({
    field: 'creation_timestamp', // FIXED: Default to creation date
    direction: 'desc', // default: latest first
});

onMounted(async () => {
    isLoading.value = true;
    try {
        const savedSort = localStorage.getItem('projectSort');
        if (savedSort) {
            sortCriteria.value = JSON.parse(savedSort);
        }
        await projectStore.fetchUserProjects();
    } catch (error) {
        errorMessage.value = 'Failed to load projects.';
    } finally {
        isLoading.value = false;
    }
});

watch(sortCriteria, (newVal) => {
    localStorage.setItem('projectSort', JSON.stringify(newVal));
}, { deep: true });

// NEW: Toggle sort dropdown
const toggleSortDropdown = () => {
    showSortDropdown.value = !showSortDropdown.value;
};

// NEW: Close dropdown when clicking outside
const closeSortDropdown = () => {
    showSortDropdown.value = false;
};

// NEW: Handle sort selection
const handleSortSelection = (value) => {
    sortCriteria.value.field = value;
    showSortDropdown.value = false;
};

// NEW: Get current sort label
const currentSortLabel = computed(() => {
    const option = sortOptions.find(opt => opt.value === sortCriteria.value.field);
    return option ? option.label : 'Sort by...';
});

// COMPUTED PROPERTY FOR FILTERING AND SORTING
const filteredProjects = computed(() => {
    if (isLoading.value) return [];

    let projects = [...projectStore.userProjects];

    // 1. Filtering Logic
    if (searchTerm.value) {
        const term = searchTerm.value.toLowerCase();
        projects = projects.filter(p =>
            p.project_name.toLowerCase().includes(term) ||
            p.description?.toLowerCase().includes(term)
        );
    }

    if (filterStatus.value) {
        // NOTE: This logic seems flawed (filtering by project_name starting with 'A' for 'Active')
        // I'll leave it as is but recommend fixing the status filtering logic.
        if (filterStatus.value === 'Active') {
            projects = projects.filter(p => p.project_name.startsWith('A'));
        }
    }

    // 2. Sorting Logic (same as before)
    const { field, direction } = sortCriteria.value;

    projects.sort((a, b) => {
        let comparison = 0;

        if (field === 'project_name') {
            comparison = a.project_name.localeCompare(b.project_name);
        }
        else if (field === 'creation_timestamp') {
            comparison = new Date(a.creation_timestamp) - new Date(b.creation_timestamp);
        }
        else if (field === 'last_modified_timestamp') {
            comparison = new Date(a.last_modified_timestamp) - new Date(b.last_modified_timestamp);
        }

        return direction === 'asc' ? comparison : -comparison;
    });

    // **3. Add Index for Counting**
    return projects.map((project, index) => ({
        ...project,
        index: index + 1, // 1-based index
    }));
});

const handleProjectAction = (project) => {
    if (isMonitorMode.value) {
        router.push({ name: 'monitor-map', params: { id: project.id } });
    } else {
        router.push({ name: 'update-project', params: { id: project.id } });
    }
};

const handleDelete = async (projectId, projectName) => {
    const confirmed = prompt(`Type DELETE to confirm deletion of project: "${projectName}"`);
    if (confirmed === 'DELETE') {
        try {
            await projectStore.deleteProject(projectId);
            await projectStore.fetchUserProjects();
            alert(`Project "${projectName}" deleted successfully.`);
        } catch (error) {
            alert('Deletion failed: You must be the project owner. See console for details.');
            console.error(error);
        }
    }
};

const goToHome = () => {
    if (session.isLoggedIn) {
        router.push('/');
    }
};


</script>
<template>
    <div id="manage-view" class="h-[85vh] text-white flex-col justify-start bg-gray-900">
        <div class="sticky top-0 z-10 w-full p-3 shadow-2xl flex justify-center items-center"
            :class="{ 'bg-orange-600/90': !isMonitorMode, 'bg-[#b49400]/90': isMonitorMode }">

            <div class="absolute pl-3 left-0 text-gray-100 items-center  cursor-pointer" @click="goToHome">
                <svg xmlns="http://www.w3.org/2000/svg" width="4vh" height="3.7vh" fill="currentColor"
                    viewBox="0 0 16 16">
                    <path fill-rule="evenodd"
                        d="M15 8a.5.5 0 0 0-.5-.5H2.707l3.147-3.146a.5.5 0 1 0-.708-.708l-4 4a.5.5 0 0 0 0 .708l4 4a.5.5 0 0 0 .708-.708L2.707 8.5H14.5A.5.5 0 0 0 15 8z" />
                </svg>
            </div>
            <h1 class="text-3xl font-extrabold text-white tracking-wide">
                {{ isMonitorMode ? 'Monitor Projects' : 'Manage Projects' }}
            </h1>
        </div>

        <div class="w-full max-w-4xl h-[80vh] pb-2 mx-auto px-4 relative">

            <div class="flex items-center mb-2 gap-3 p-2 rounded-xl shadow-lg">

                <div class="relative flex-1">
                    <input type="text" v-model="searchTerm" placeholder="Search projects by Name or Description..."
                        class="w-full pl-10 pr-10 py-2 rounded-xl bg-gray-700 text-white 
                           border border-gray-600 focus:ring-cyan-500 focus:border-cyan-500 
                           transition duration-200 shadow-inner text-sm" />

                    <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none"
                        stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>

                    <button v-if="searchTerm" @click="searchTerm = ''"
                        class="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full text-gray-400 hover:text-white hover:bg-gray-600 transition duration-150"
                        title="Clear Search">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>

                <div class="relative flex-shrink-0">
                    <button @click="toggleSortDropdown" class="flex items-center gap-2 px-3 bg-gray-700 hover:bg-gray-600 
                               border border-gray-600 rounded-xl text-white transition duration-200 text-sm h-10"
                        title="Sort Options">

                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M3 4h18M3 8h18m-6 4h6m-6 4h6"></path>
                        </svg>

                        <span class="hidden sm:inline">{{ currentSortLabel.replace('Sort by ', '') }}</span>

                        <svg class="w-3 h-3 transition-transform duration-200"
                            :class="{ 'rotate-180': showSortDropdown }" fill="none" stroke="currentColor"
                            viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7">
                            </path>
                        </svg>
                    </button>

                    <div v-if="showSortDropdown" v-click-outside="closeSortDropdown" class="absolute top-full right-0 mt-2 w-56 bg-gray-800 border border-cyan-500/50 
                               rounded-lg shadow-2xl z-50 overflow-hidden">
                        <div class="py-1">
                            <button v-for="option in sortOptions" :key="option.value"
                                @click="handleSortSelection(option.value)" class="w-full px-4 py-2 text-left text-sm hover:bg-gray-700 
                                       transition duration-150 flex items-center justify-between" :class="{
                                        'bg-cyan-900/30 text-cyan-400 font-semibold': sortCriteria.field === option.value,
                                        'text-gray-300': sortCriteria.field !== option.value
                                    }">
                                <span>{{ option.label }}</span>
                                <svg v-if="sortCriteria.field === option.value" class="w-4 h-4 text-cyan-400"
                                    fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M5 13l4 4L19 7"></path>
                                </svg>
                            </button>
                        </div>

                        <div class="border-t border-gray-700 px-4 py-2 bg-gray-900/50">
                            <button @click="sortCriteria.direction = sortCriteria.direction === 'asc' ? 'desc' : 'asc'"
                                class="w-full flex items-center justify-between text-xs text-gray-300 hover:text-white transition duration-150">
                                <span class="font-medium">Sort Direction:</span>
                                <div class="flex items-center gap-1">
                                    <span class="text-xs text-cyan-400 font-semibold">
                                        {{ sortCriteria.direction === 'asc' ? 'A → Z (Asc)' : 'Z → A (Desc)' }}
                                    </span>
                                    <svg class="w-3 h-3 transition-transform duration-200"
                                        :class="{ 'rotate-180': sortCriteria.direction === 'desc' }" fill="none"
                                        stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M5 15l7-7 7 7"></path>
                                    </svg>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>

            </div>


            <div class="space-y-2 h-[70vh] overflow-y-auto pr-3">
                <p v-if="isLoading" class="text-center py-8 text-gray-400">Loading projects...</p>
                <p v-else-if="errorMessage" class="text-center py-8 text-red-500 font-medium">{{ errorMessage }}</p>
                <p v-else-if="filteredProjects.length === 0" class="text-center py-8 text-gray-400 text-lg">
                    No projects match your criteria. 🧐
                </p>

                <div v-for="project in filteredProjects" :key="project.id"
                    class="flex justify-between items-center p-4 rounded-xl bg-gray-800 hover:bg-gray-700 transition duration-200 shadow-xl border-l-4 cursor-pointer"
                    @click="handleProjectAction(project)"
                    :class="{ 'border-orange-600/90': !isMonitorMode, 'border-[#b49400]/90': isMonitorMode }">

                    <div class="flex items-center gap-4 min-w-0">
                        <span class="text-2xl font-extrabold flex-shrink-0 w-6 text-right"
                            :class="{ 'text-orange-600/90': !isMonitorMode, 'text-[#b49400]/90': isMonitorMode }">
                            {{ project.index }}.
                        </span>

                        <div class="flex flex-col text-left min-w-0 flex-grow">
                            <h3 class="text-xl font-bold text-white truncate">{{ project.project_name }}</h3>

                            <p class="text-sm text-gray-400 truncate mt-1">
                                <span class="hidden sm:inline">Last Modified: {{ project.last_modified_timestamp ? new
                                    Date(project.last_modified_timestamp).toLocaleDateString() : 'N/A' }}</span>
                                <span class="block sm:hidden text-xs italic">{{ project.description || 'No description.'
                                    }}</span>
                            </p>
                        </div>
                    </div>

                    <div class="flex space-x-3 flex-shrink-0 ml-4">
                        <button @click.stop="handleProjectAction(project)"
                            class="p-2 rounded-full bg-blue-600 hover:bg-blue-500 text-white transition duration-150 shadow-md"
                            :title="isMonitorMode ? 'View Live Map' : 'Edit Project'">
                            <svg v-if="isMonitorMode" class="w-5 h-5" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z">
                                </path>
                            </svg>
                            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z">
                                </path>
                            </svg>
                        </button>

                        <button v-if="!isMonitorMode" @click.stop="handleDelete(project.id, project.project_name)"
                            class="p-2 rounded-full bg-red-600 hover:bg-red-500 text-white transition duration-150 shadow-md"
                            title="Delete Project (Requires Owner Role)">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16">
                                </path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Keeping original styles and adding the new scrollbar style for sleeker appearance */
.min-h-screen {
    min-height: 100vh;
}

.bg-gray-900 {
    background-color: #111827;
}

.bg-gray-800 {
    background-color: #1f2937;
}

.bg-gray-700 {
    background-color: #374151;
}

/* Custom scrollbar - darker for a sleeker look */
.overflow-y-auto::-webkit-scrollbar {
    width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
    background-color: #4b5563;
    /* Darker thumb */
    border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-track {
    background-color: #1f2937;
    /* Dark track */
}

/* Smooth rotation for dropdown arrow */
.rotate-180 {
    transform: rotate(180deg);
}

/* Ensure dropdown is above other elements */
.z-50 {
    z-index: 50;
}
</style>
