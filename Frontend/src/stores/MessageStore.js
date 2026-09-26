import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useMessageStore = defineStore('messageStore', () => {
  const message = ref(null);  // text
  const type = ref(null);     // "error" | "success" | "info"

  function showMessage(msg, msgType = "info", duration = 2500) {
    message.value = msg;
    type.value = msgType;

    if (duration !== 0) {
      setTimeout(() => {
        message.value = null;
        type.value = null;
      }, duration);
    }
  }

  return { message, type, showMessage };
});
