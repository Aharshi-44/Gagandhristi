<!-- GARUDA-Frontend/src/components/common/InlineMessage.vue -->

<script setup>
import { useMessageStore } from '@/stores/MessageStore.js';
const messageStore = useMessageStore();
</script>

<template>
  <transition name="fade">
    <div v-if="messageStore.message"
      :class="{
        'bg-red-700': messageStore.type === 'error',
        'bg-green-700': messageStore.type === 'success',
        'bg-blue-700': messageStore.type === 'info'
      }"
      class="fixed px-4 z-[1000] py-2 mx-auto text-center text-white font-medium border-b border-gray-600">
      {{ messageStore.message }}
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
