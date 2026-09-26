<!-- frontend/src/components/common/KeyValueEditor.vue -->

<script setup>
import { ref, watch, onMounted } from 'vue';

const props = defineProps({
    initialData: {
        type: Object,
        required: true
    }
});

const emit = defineEmits(['save', 'cancel']);
const argFields = ref([]);

/**
 * Converts the initial object (prop) into the local array state.
 */
const loadInitialData = () => {
    const newFields = Object.entries(props.initialData).map(([key, value]) => ({
        key,
        value: typeof value === 'object' ? JSON.stringify(value) : String(value),
        id: Math.random().toString(36).substring(7) // Simple unique ID for the key
    }));
    argFields.value = newFields;
};

/**
 * Processes the key/value array back into a configuration object.
 */
const finalizeArguments = () => {
    const finalArgs = {};
    for (const field of argFields.value) {
        if (field.key.trim() === '') continue; // Skip empty keys
        
        const key = field.key.trim();
        let value = field.value.trim();
        
        try {
            if (value.startsWith('{') || value.startsWith('[') || value === 'true' || value === 'false' || !isNaN(value)) {
                value = JSON.parse(value);
            }
        } catch (e) {
            console.warn(`Argument for key "${key}" could not be parsed as JSON/Number. Kept as string.`);
        }
        
        finalArgs[key] = value;
    }
    return finalArgs;
};

const addNewField = () => {
    // Only add a new field if the last one isn't empty
    const lastField = argFields.value[argFields.value.length - 1];
    if (lastField?.key.trim() !== '' || lastField?.value.trim() !== '') {
        argFields.value.push({ key: '', value: '', id: Math.random().toString(36).substring(7) });
    }
};

const removeField = (id) => {
    argFields.value = argFields.value.filter(field => field.id !== id);
    // Ensure there is at least one blank field if all were removed
    if (argFields.value.length === 0) {
        addNewField();
    }
};

const handleSave = () => {
    const finalArgs = finalizeArguments();
    emit('save', finalArgs);
};

onMounted(loadInitialData);
// Watch initialData prop to reset fields if the user switches algorithm during editing
watch(() => props.initialData, loadInitialData, { deep: true });
</script>

<template>
    <div class="space-y-4">
        <div class="max-h-60 overflow-y-auto space-y-2 pr-2 border-b border-gray-700 pb-3">
            <div 
                v-for="(field, index) in argFields" :key="field.id" 
                class="flex gap-2 items-center"
            >
                <input 
                    type="text" 
                    v-model="field.key" 
                    placeholder="Argument Key" 
                    class="w-5/12 p-2 bg-gray-700 text-white rounded border border-gray-600 text-sm"
                >
                <input 
                    type="text" 
                    v-model="field.value" 
                    placeholder="Value (string, number, or JSON)" 
                    class="w-6/12 p-2 bg-gray-700 text-white rounded border border-gray-600 text-sm"
                >
                <button 
                    @click="removeField(field.id)" 
                    :disabled="argFields.length === 1 && index === 0"
                    class="w-1/12 text-red-400 hover:text-red-500 font-bold p-2 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    &times;
                </button>
            </div>
        </div>
        
        <div class="flex justify-between items-center">
            <button @click="addNewField" class="text-blue-400 hover:text-blue-300 text-sm flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                Add Parameter
            </button>
            
            <div class="flex space-x-3">
                <button @click="$emit('cancel')" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg">Cancel</button>
                <button @click="handleSave" class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold">Apply Changes</button>
            </div>
        </div>
    </div>
</template>