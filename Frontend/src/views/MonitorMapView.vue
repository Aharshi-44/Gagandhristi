<!-- GARUDA-Frontend/src/views/MonitorMapView.vue -->

<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ApiClient } from '@/api/backendAPIendpoint.js';

import MapVisualization from '@/components/map/MapVisualization.vue';
import AoiVizPanel from '@/components/map/AoiVizPanel.vue';
import ChangeDetectionPanel from '@/components/processing/ChangeDetectionPanel.vue';
import SemanticRetrievalPanel from '@/components/processing/SemanticRetrievalPanel.vue';


const props = defineProps({
  id: String,
});


const router = useRouter();
const apiClient = ApiClient.getInstance();


// ============================================================
// PAGE STATE
// ============================================================

const isLoading = ref(true);
const project = ref(null);

const projectAlerts = ref([]);
const alertFeatures = ref([]);

const showVizPanel = ref(false);
const activeAoiDetails = ref(null);

// PS 2.2.1 Semantic Retrieval Console
const showSemanticPanel = ref(false);
const toggleSemanticPanel = () => {
  showSemanticPanel.value = !showSemanticPanel.value;
};

const mapKey = ref(0);

const alertTimeRange = ref({
  from: null,
  to: null,
});


// ============================================================
// LOAD PROJECT
// ============================================================

onMounted(async () => {

  try {

    const data =
      await apiClient.getProjectDetails(
        parseInt(props.id)
      );

    project.value = data;

    console.log(
      '[MonitorMapView] Project loaded:',
      data
    );

  } catch (error) {

    console.error(
      'Error loading project for monitoring:',
      error
    );

    router.push('/');

  } finally {

    isLoading.value = false;

  }

});


// ============================================================
// AOI CLICK
// ============================================================

const handleAoiClick = async (aoi) => {

  console.log(
    '[MonitorMapView] AOI clicked:',
    aoi
  );

  activeAoiDetails.value = aoi;

  showVizPanel.value = true;

  await fetchAlertsForAoi(
    aoi.aoi_id
  );
};


// ============================================================
// CLOSE AOI PANEL
// ============================================================

const closeVizPanel = () => {

  showVizPanel.value = false;

  activeAoiDetails.value = null;

  projectAlerts.value = [];

  alertTimeRange.value = {
    from: null,
    to: null,
  };

  alertFeatures.value = [];

  mapKey.value++;

};


// ============================================================
// FETCH AOI ALERTS
// ============================================================

const fetchAlertsForAoi = async (aoiId) => {

  try {

    console.log(
      '[MonitorMapView] Fetching alerts for AOI:',
      aoiId,
      'Project:',
      project.value.id
    );


    const {
      alerts,
      timeRange
    } = await apiClient.getProjectAlerts(
      project.value.id,
      aoiId
    );


    console.log(
      '[MonitorMapView] Raw alerts received:',
      alerts
    );

    console.log(
      '[MonitorMapView] Alert count:',
      alerts.length
    );


    // --------------------------------------------------------
    // Store alerts
    // --------------------------------------------------------

    projectAlerts.value = alerts;

    alertTimeRange.value = timeRange;


    // --------------------------------------------------------
    // Extract GeoJSON
    // --------------------------------------------------------

    alertFeatures.value = alerts
      .map((alert, idx) => {

        const geojson =
          alert.featureGeoJson;


        console.log(
          `[MonitorMapView] Alert ${idx + 1}:`,
          {
            id: alert.id,
            hasFeature: !!geojson,
            featureType: geojson?.type,
            message: alert.message,
          }
        );


        return geojson;

      })
      .filter((geojson) => {

        const isValid =
          geojson &&
          (
            geojson.type === 'Feature' ||
            geojson.type === 'FeatureCollection' ||
            (
              geojson.type &&
              geojson.coordinates
            )
          );


        if (
          geojson &&
          !isValid
        ) {

          console.warn(
            '[MonitorMapView] Invalid GeoJSON structure:',
            geojson
          );

        }


        return isValid;

      });


    console.log(
      '[MonitorMapView] Valid alert features:',
      alertFeatures.value.length
    );


    console.log(
      '[MonitorMapView] Features to display:',
      alertFeatures.value
    );


  } catch (e) {

    console.error(
      '[MonitorMapView] Failed to load alerts:',
      e
    );

    console.error(
      'Error details:',
      e.response?.data || e.message
    );

  }

};

</script>


<template>

  <div
    class="monitor-map-view
           h-[85vh]
           flex
           flex-col
           relative"
  >

    <!-- ======================================================
         LOADING
         ====================================================== -->

    <div
      v-if="isLoading"
      class="flex-grow
             flex
             items-center
             justify-center
             text-white"
    >
      Loading Monitor Data...
    </div>


    <!-- ======================================================
         MAIN CONTENT
         ====================================================== -->

    <div
      v-else-if="project"
      class="flex-grow
             h-[80vh]
             mt-[1.4vh]
             relative
             min-h-0"
    >

      <!-- ====================================================
           MAP
           ==================================================== -->

      <div
        class="h-full
               inset-0"
      >

        <MapVisualization
          :key="mapKey"
          :aois-to-display="project.aois"
          :is-monitor-mode="true"
          @aoi-clicked="handleAoiClick"
          :alert-features-to-display="alertFeatures"
        />

      </div>


      <!-- ====================================================
           AOI VISUALIZATION PANEL
           ==================================================== -->

      <AoiVizPanel
        :is-visible="showVizPanel"
        :project-id="project.id"
        :selected-aoi="activeAoiDetails"
        :project-alerts="projectAlerts"
        :alert-time-range="alertTimeRange"
        @close="closeVizPanel"
      />


      <!-- ====================================================
           ML CHANGE DETECTION PANEL
           ==================================================== -->

      <div
        class="absolute
               top-4
               right-4
               z-[100]"
      >

        <ChangeDetectionPanel
          :subscription-id="1"
        />

      </div>


      <!-- ====================================================
           PS 2.2.1: SEMANTIC RETRIEVAL TRIGGER & PANEL
           ==================================================== -->
      <div
        class="absolute
               top-4
               left-4
               z-[100]"
      >
        <button
          @click="toggleSemanticPanel"
          class="px-4 py-2.5 rounded-xl font-bold text-xs shadow-2xl flex items-center gap-2 border transition-all duration-200 transform active:scale-95 backdrop-blur-md"
          :class="showSemanticPanel
            ? 'bg-cyan-600 text-white border-cyan-400 ring-2 ring-cyan-500/50'
            : 'bg-gray-900/90 text-cyan-300 hover:text-white hover:bg-gray-800 border-cyan-500/40'"
          title="Open Semantic & Multimodal Retrieval Console (PS 2.2.1)"
        >
          <span class="text-base">🛰️</span>
          <span>Semantic Retrieval</span>
          <span class="text-[9px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 font-mono border border-cyan-700/60">
            PS 2.2.1
          </span>
        </button>
      </div>

      <SemanticRetrievalPanel
        v-if="showSemanticPanel"
        @close="showSemanticPanel = false"
      />

    </div>


    <!-- ======================================================
         ERROR
         ====================================================== -->

    <div
      v-else
      class="flex-grow
             flex
             items-center
             justify-center
             text-red-400"
    >

      Project not found.

    </div>

  </div>

</template>


<style scoped>

.monitor-map-view {
  background-color: #111827;
}

</style>