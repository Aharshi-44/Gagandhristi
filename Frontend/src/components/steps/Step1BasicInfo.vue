<!-- Step1BasicInfo.vue  -->

<script setup>
import { ref } from 'vue';
import { useProjectStore } from '@/stores/ProjectStore.js'; // Import the store

const projectStore = useProjectStore();
const projectData = projectStore.projectForm; // Still keep a reference for auxDataDrafts

const newAuxKey = ref('');
const newAuxValue = ref('');
const showNewAuxFields = ref(false);

const addAuxData = () => {
    if (newAuxKey.value && newAuxValue.value) {
        // Direct mutation on the array property is usually fine
        projectData.auxDataDrafts.push({
            key: newAuxKey.value,
            value: newAuxValue.value
        }); // REMOVED: as AuxDataDraft
        newAuxKey.value = '';
        newAuxValue.value = '';
        showNewAuxFields.value = false;
    }
};

const removeAuxData = (key) => {
    projectData.auxDataDrafts = projectData.auxDataDrafts.filter(draft => draft.key !== key);
};


</script>


<template>
    <div class="h-[68vh] pt-[1vh] ">

        <div class="form-group mb-1">
            <label class="text-gray-400">Project Name:</label>
            <input type="text" v-model="projectStore.projectName" required
                class="w-full p-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-cyan-500" />
        </div>
        <div class="form-group mb-2">
            <label class="text-gray-400">Description:</label>
            <textarea v-model="projectStore.description" rows="3"
                class="w-full p-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-cyan-500"></textarea>
        </div>

        <!-- <h4 class="text-lg font-semibold text-cyan-400 mt-6 mb-3">Custom Auxiliary Data (JSONB)</h4> -->

        <button @click="showNewAuxFields = true" v-if="!showNewAuxFields"
            class="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition duration-200 mb-4">
            <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6">
                </path>
            </svg>
            Add More Fields
        </button>
        <div v-if="showNewAuxFields" class="aux-data-entry  p-2 bg-gray-700 items-center flex-col rounded-lg">

            <div class="flex flex-row w-full sm:flex-row gap-3">
                <input type="text" v-model="newAuxKey" placeholder="Key (e.g., Client)"
                    class="w-full sm:w-1/2 p-2 bg-gray-600 text-white rounded border border-gray-500" />
                <input type="text" v-model="newAuxValue" placeholder="Value (e.g., ISRO)"
                    class="w-full sm:w-2/3 p-2 bg-gray-600 text-white rounded border border-gray-500" />
            </div>

            <div class="flex w-full justify-end items-center gap-3">

                
                <button @click="showNewAuxFields = false"
                    class="bg-red-500 px-3 py-1.5 text-white rounded-lg text-sm font-semibold transition duration-150"
                    title="Cancel"> Cancel
                    
                </button>

                <button @click="addAuxData"
                    class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition duration-150"
                    title="Save this custom field">
                    Save Field
                </button>
            </div>
        </div>



        <div class="aux-list max-h-[40vh] mt-3 overflow-y-auto">
            <div v-for="draft in projectData.auxDataDrafts" :key="draft.key"
                class="aux-item flex justify-between items-center p-2 bg-gray-700 rounded border border-gray-600">
                <span class="text-cyan-300 truncate w-[85%] mr-2">
                    {{ draft.key }}: <span class="text-white font-mono">{{ draft.value }}</span>
                </span>

                <button @click="removeAuxData(draft.key)"
                    class="text-red-400 hover:text-red-500 font-bold text-xl p-1 leading-none flex-shrink-0">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <line x1="4" y1="4" x2="20" y2="20" stroke="currentColor" stroke-width="2" />
                        <line x1="20" y1="4" x2="4" y2="20" stroke="currentColor" stroke-width="2" />
                    </svg>
                </button>
            </div>
            <p v-if="projectData.auxDataDrafts.length === 0" class="text-center text-gray-400 p-2 text-sm">No custom
                fields defined.</p>
        </div>





    </div>
</template>

<style scoped>
label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="text"],
textarea {
    width: 100%;
    padding: 8px;
    box-sizing: border-box;
}

.aux-data-entry,
.aux-item {
    display: flex;
    gap: 10px;
    margin-bottom: 5px;
}

.aux-data-entry input {
    flex-grow: 1;
}
</style>
