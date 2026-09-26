<!-- frontend/src/components/steps/RoleSelectionPopup.vue -->
<template>
  <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-gray-800 p-6 rounded-xl w-96 max-w-[90vw]">
      <h3 class="text-lg text-cyan-400 font-semibold mb-4">
        Assign permissions to {{ userId }}
      </h3>

      <div v-if="roles.length === 0" class="text-gray-400 text-center py-4">
        No permissions available
      </div>

      <div v-else class="space-y-2 max-h-60 overflow-y-auto pr-2">
        <label 
          v-for="r in roles" 
          :key="r.id" 
          class="flex items-center gap-2 p-2 rounded hover:bg-gray-700 transition cursor-pointer"
        >
          <input 
            type="checkbox" 
            v-model="selected" 
            :value="r.id"
            class="w-4 h-4 cursor-pointer"
          />
          <span class="text-white">{{ r.role }}</span>
        </label>
      </div>

      <div class="flex justify-end gap-3 mt-5">
        <button 
          class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded transition" 
          @click="$emit('close')"
        >
          Cancel
        </button>
        <button 
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition" 
          @click="save"
        >
          Save Permissions
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  userId: String,
  roles: Array, // Array of {id: number, role: string}
  preselected: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['save', 'close']);

const selected = ref([...props.preselected]);

// Watch for changes in preselected prop
watch(() => props.preselected, (newVal) => {
  selected.value = [...newVal];
}, { immediate: true });

const save = () => {
  emit('save', selected.value);
};
</script>

<style scoped>
/* Custom scrollbar for role list */
div::-webkit-scrollbar {
  width: 6px;
}

div::-webkit-scrollbar-track {
  background: #374151;
  border-radius: 3px;
}

div::-webkit-scrollbar-thumb {
  background: #4B5563;
  border-radius: 3px;
}

div::-webkit-scrollbar-thumb:hover {
  background: #6B7280;
}
</style>