// stores/ProjectStore.js - Updated to handle auxData properly

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { ProjectFormData } from '../classes/ProjectFormData.js';
import { ProjectBundleModel } from '../models/ProjectBundleModel.js';
import { AreaOfInterestDraft } from '../classes/AreaOfInterestDraft.js';
import { ApiClient } from '../api/backendAPIendpoint.js';
import { UserSession } from '../classes/UserSession.js';

const api = ApiClient.getInstance();

/**
 * Maps backend data to ProjectFormData for editing
 * Now uses ProjectBundleModel for cleaner mapping, but maintains AreaOfInterestDraft for UI compatibility
 */
function mapBackendToForm(data) {
    const form = new ProjectFormData(true, data.id);

    form.auxDataDrafts = data.auxdata ? Object.entries(data.auxdata).map(([key, value]) => ({
        key,
        value: typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
    })) : [];

    // Convert users - use UserProjectModel for bundle, but keep simple format for form
    const userModels = (data.users || []).map(user => {
        if (typeof user === 'object' && user.userId) {
            return { userId: user.userId, roles: user.roles || [] };
        }
        return { userId: user, roles: [] };
    });
    form.users.splice(0, form.users.length, ...userModels);

    // Convert AOIs to drafts (components use AreaOfInterestDraft)
    let aoiCounter = 1;
    const aoiDrafts = data.aois.map((aoi) => {
        let geometry = aoi.geomGeoJson;

        if (!geometry) {
            console.error(`AOI ${aoi.name} has no geometry!`);
            return null;
        }

        let geometryType = geometry.type;

        if (geometryType === 'GeometryCollection') {
            if (!geometry.geometries || geometry.geometries.length === 0) {
                console.error(`AOI ${aoi.name} has empty GeometryCollection`);
                return null;
            }
        } else {
            if (!geometry.coordinates || geometry.coordinates.length === 0) {
                console.error(`AOI ${aoi.name} has invalid coordinates`);
                return null;
            }
        }

        const bufferDistance = aoi.geom_properties?.buffer || null;

        const aoiDraft = new AreaOfInterestDraft(
            aoi.name,
            geometry,
            aoiCounter++,
            geometryType,
            bufferDistance
        );

        aoiDraft.aoiId = aoi.aoi_id;
        aoiDraft.dbId = aoi.id;
        aoiDraft.status = aoi.status || 1;

        aoiDraft.geomProperties = {
            ...(aoi.geom_properties || {}),
            originalType: geometryType,
            buffer: bufferDistance,
            bufferConfig: aoi.geom_properties?.bufferConfig || null,
            originalCoordinates: aoi.geom_properties?.originalCoordinates || null
        };

        aoiDraft.setAuxData(aoi.auxdata || null);

        return aoiDraft;
    }).filter(draft => draft !== null);
    
    form.aoiDrafts.splice(0, form.aoiDrafts.length, ...aoiDrafts);

    // Convert subscriptions - create SubscriptionModel instances for bundle
    const subscriptions = [];
    data.aois.forEach(aoi => {
        if (aoi.subscriptions && aoi.subscriptions.length > 0) {
            aoi.subscriptions.forEach(sub => {
                const aoiDraft = form.aoiDrafts.find(d => d.aoiId === aoi.aoi_id);
                if (aoiDraft) {
                    subscriptions.push({
                        aoiId: aoi.aoi_id,
                        clientAoiId: aoiDraft.clientAoiId,
                        channelId: sub.channelId,
                        userIds: sub.userIds || [],
                        subscriptionId: sub.subscriptionId,
                        status: sub.status || 1,
                        alertDisseminationMode: sub.alertDisseminationMode || ['notify'],
                        auxData: sub.auxData || null
                    });
                }
            });
        }
    });
    
    form.subscriptions.splice(0, form.subscriptions.length, ...subscriptions);

    // Update bundle's project basic info
    form.bundle.project = ProjectBundleModel.fromBackend(data).project;

    console.log('[ProjectStore] Mapped form data:', {
        users: form.users.length,
        aois: form.aoiDrafts.length,
        subscriptions: form.subscriptions.length
    });

    form.currentStep = 1;
    return form;
}

/**
 * ProjectStore: Manages project state and operations
 */
export const useProjectStore = defineStore('project', () => {

    const userPermissions = ref({
        isOwner: false,
        isAdmin: false,
        roles: [],
        permissions: {
            canEditProjectInfo: true,
            canEditUsers: true,
            canEditAOI: true,
            canEditSubscriptions: true,
            canDelete: true
        }
    });

    const projectForm = ref(new ProjectFormData());
    const userProjects = ref([]);
    const activeAlerts = ref([]);

    // Add this computed property:
    const hasStepPermission = computed(() => {
        return (step) => {
            if (userPermissions.value.isOwner || userPermissions.value.isAdmin) {
                return true;
            }

            switch (step) {
                case 1: return userPermissions.value.permissions.canEditProjectInfo;
                case 2: return userPermissions.value.permissions.canEditUsers;
                case 3: return userPermissions.value.permissions.canEditAOI;
                case 4: return userPermissions.value.permissions.canEditSubscriptions;
                default: return false;
            }
        };
    });

    const isEditing = computed(() => projectForm.value.isUpdateMode);
    const currentStep = computed(() => projectForm.value.currentStep);
    const totalAlerts = computed(() => activeAlerts.value.length);

    function initNewProjectForm() {
        projectForm.value = new ProjectFormData(false, null);
    }

    async function fetchProjectPermissions(projectId) {
        try {
            const permissions = await api.getProjectPermissions(projectId);
            userPermissions.value = permissions;
            console.log('[ProjectStore] User permissions loaded:', permissions);
            return permissions;
        } catch (error) {
            console.error('Error fetching permissions:', error);
            // Default to no permissions on error
            userPermissions.value = {
                isOwner: false,
                isAdmin: false,
                roles: [],
                permissions: {
                    canEditProjectInfo: false,
                    canEditUsers: false,
                    canEditAOI: false,
                    canEditSubscriptions: false,
                    canDelete: false
                }
            };
            throw error;
        }
    }

    async function submitProject() {
        const bundle = projectForm.value.toBackendBundle();

        console.log("--- SUBMIT PAYLOAD ---");
        console.log("Is Update Mode:", projectForm.value.isUpdateMode);
        console.log("Project Name:", bundle.projectBasicInfo.projectName);
        console.log("User Count:", bundle.userData.length);
        console.log("AOI Count:", bundle.aoiData.length);
        console.log("Subscription Count:", bundle.subscriptionData?.length || 0);
        console.log("AOI Details:", JSON.stringify(bundle.aoiData.map(a => ({
            name: a.name,
            hasAuxData: !!a.auxData,
            hasOriginalCoords: !!a.geomProperties?.originalCoordinates
        })), null, 2));
        console.log("------------------------");

        try {
            let response;
            if (projectForm.value.isUpdateMode && projectForm.value.projectIdToUpdate) {
                response = await api.updateProject(projectForm.value.projectIdToUpdate, bundle);
            } else {
                response = await api.createProject(bundle);
            }

            console.log('Project submitted successfully:', response.data);
            projectForm.value.reset();

        } catch (error) {
            console.error('Error submitting project:', error);
            
            // Extract error message from API response
            const errorMessage = error.response?.data?.message || 
                               error.response?.data?.error || 
                               error.message || 
                               'Failed to submit project. See console for API error details.';
            
            throw new Error(errorMessage);
        }
    }

    async function fetchUserProjects() {
        try {
            const projects = await api.getProjects();
            userProjects.value = projects;
        } catch (error) {
            console.error('Error fetching projects:', error);
            userProjects.value = [];
        }
    }

    async function loadProjectForUpdate(projectId) {
        try {
            // Load permissions first
            await fetchProjectPermissions(projectId);

            const response = await api.getProjectDetails(projectId);
            console.log('[ProjectStore] Loaded project data:', response);

            projectForm.value = mapBackendToForm(response);

            console.log('[ProjectStore] Mapped form data:', {
                users: projectForm.value.users.length,
                aois: projectForm.value.aoiDrafts.length,
                subscriptions: projectForm.value.subscriptions.length,
                aoisWithAuxData: projectForm.value.aoiDrafts.filter(a => a.auxData).length
            });
        } catch (error) {
            console.error(`Error loading project ${projectId}:`, error);
            throw new Error('Failed to load project data for editing.');
        }
    }

    async function deleteProject(projectId) {
        await api.deleteProject(projectId);
    }

    function addAlert(alert) {
        if (!activeAlerts.value.some(a => a.id === alert.id)) {
            activeAlerts.value.unshift(alert);
        }
    }

    async function markAlertAsRead(alertId) {
        const session = UserSession.getInstance();
        const userId = session.userId;

        if (!userId) return;

        try {
            await api.client.post('/alerts/mark-read', { userId, notificationId: alertId });
        } catch (error) {
            console.error('Failed to mark alert as read:', error);
            throw error;
        }
    }

    function nextStep() {
        projectForm.value.nextStep();
    }

    function prevStep() {
        projectForm.value.prevStep();
    }

    return {
        projectForm,
        userProjects,
        isEditing,
        currentStep,
        initNewProjectForm,
        submitProject,
        fetchUserProjects,
        loadProjectForUpdate,
        deleteProject,
        nextStep,
        prevStep,
        activeAlerts,
        totalAlerts,
        addAlert,
        markAlertAsRead,
        userPermissions,
        hasStepPermission,
        fetchProjectPermissions,
        projectName: computed({
            get: () => projectForm.value.projectName,
            set: (val) => { projectForm.value.projectName = val; }
        }),
        description: computed({
            get: () => projectForm.value.description,
            set: (val) => { projectForm.value.description = val; }
        }),
    };
});