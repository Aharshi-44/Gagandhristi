<!-- frontend/src/components/common/CustomSelect.vue -->

<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({
  modelValue: [Object, String, Number, null],
  options: { type: Array, required: true },
  labelKey: { type: String, default: 'name' },
  valueKey: { type: String, default: 'aoiId' },
  placeholder: { type: String, default: 'Select an Item' }
});

const emit = defineEmits(['update:modelValue']);
const isOpen = ref(false);
const selectedValue = ref(props.modelValue);

const displayLabel = computed(() => {
  if (!selectedValue.value) return props.placeholder;

  // Detect whether modelValue is an object or primitive
  if (typeof selectedValue.value === 'object') {
    return selectedValue.value[props.labelKey] ||
           `${selectedValue.value[props.labelKey]} (${selectedValue.value[props.valueKey]})` ||
           props.placeholder;
  }

  const found = props.options.find(opt => opt[props.valueKey] === selectedValue.value);
  return found ? found[props.labelKey] : props.placeholder;
});

watch(
  () => props.modelValue,
  newVal => (selectedValue.value = newVal)
);

const selectOption = option => {
  // Emit full object if original modelValue was object (AOI mode)
  const isObjectModel = typeof props.modelValue === 'object' && props.modelValue !== null;
  const emittedValue = isObjectModel ? option : option[props.valueKey];

  selectedValue.value = emittedValue;
  emit('update:modelValue', emittedValue);
  isOpen.value = false;
};
</script>

<template>
  <div class="relative w-full">
    <button
      type="button"
      @click="isOpen = !isOpen"
      class="w-full p-2 bg-gray-700 text-white rounded border border-gray-600 flex justify-between items-center transition-colors duration-150"
      :class="{ 'ring-2 ring-cyan-500 border-cyan-500': isOpen }"
    >
      <span class="truncate pr-2" :class="{ 'text-gray-400': !selectedValue }">
        {{ displayLabel }}
      </span>
      <svg
        class="w-4 h-4 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </button>

    <div
      v-if="isOpen"
      class="absolute mt-1 w-full rounded-lg bg-gray-700 shadow-xl border border-gray-600 z-50 max-h-40 overflow-y-auto"
      tabindex="-1"
    >
      <div
        v-for="option in options"
        :key="option[valueKey]"
        @click="selectOption(option)"
        class="p-2 cursor-pointer hover:bg-gray-600 transition-colors duration-100 truncate"
        :class="{ 'bg-gray-600 font-semibold': option === selectedValue || option[valueKey] === selectedValue }"
      >
        {{ option[labelKey] }}
        <span v-if="props.valueKey === 'aoiId'" class="text-gray-400 text-xs">({{ option[valueKey] }})</span>
      </div>

      <div v-if="options.length === 0" class="p-2 text-gray-400 italic">No options available</div>
    </div>
  </div>
</template>
