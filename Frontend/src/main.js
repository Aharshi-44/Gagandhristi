import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import HighchartsVue from 'highcharts-vue'; // Import the wrapper
import Highcharts from 'highcharts'; // Already imported by highcharts-vue, but ensure its reference is available

import router from './router/index.js'; 
// import 'virtual:tailwindcss';
import './style.css'; // Global styles



// Create the root Vue application instance
const app = createApp(App);

// Install the Vue Router
app.use(router);

// 1. Register the Highcharts Vue wrapper globally
app.use(HighchartsVue);
// Accessibility(Highcharts);

// Install Pinia for state management (used by your ProjectStore)
app.use(createPinia());



// Mount the application to the DOM (assuming index.html has <div id="app"></div>)
app.mount('#app');
