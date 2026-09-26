// api/backendAPIendpoint.js
import axios from 'axios';

/**
 * backendAPIendpoint: Manages all API calls, including setting headers for authentication.
 * Updated for subscription-based flow.
 */

export class ApiClient {
    client;
    static instance;
    userId = null;


    constructor() {
        this.client = axios.create({
            baseURL: '/api',
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }
    

    static getInstance() {
        if (!ApiClient.instance) {
            ApiClient.instance = new ApiClient();
        }
        return ApiClient.instance;
    }

    setUserId(userId) {
        this.userId = userId;
        this.client.defaults.headers['X-User-ID'] = userId;
    }

    getUserId() {
        return this.userId;
    }
    
    // --- Auth Endpoints ---
    async login(username, password) {
        const response = await this.client.post('/auth/login', { username, password });
        const { userId, username: returnedUsername } = response.data;
        this.setUserId(userId);
        return { userId, username: returnedUsername };
    }

    async signup(username, password, email, contactno) {
        const response = await this.client.post('/auth/signup', { username, password, email, contactno });
        const { userId, username: returnedUsername } = response.data;
        return { userId, username: returnedUsername };
    }

    async getUserProfile(userId) {
        const response = await this.client.get(`/auth/profile/${userId}`);
        return response.data;
    }

    async userExists(userId) {
        const response = await this.client.get(`/auth/exists/${userId}`);
        return response.data.exists;
    }
    async getAllRoles() {
    const response = await this.client.get('/projects/roles');
    return response.data;
}


    // --- Project Endpoints ---
    async createProject(bundle) {
        return this.client.post('/projects', bundle);
    }

    async updateProject(projectId, bundle) {
        return this.client.put(`/projects/${projectId}`, bundle);
    }

    // NEW: Get alert channel catalogue
    async getAlertChannelCatalogue() {
        const response = await this.client.get('/projects/alert-channels');
        return response.data;
    }
    
    async getProjects() {
        const response = await this.client.get('/projects');
        return response.data;
    }
    
    async getProjectDetails(projectId) {
        const response = await this.client.get(`/projects/${projectId}`);
        return response.data;
    }

    async getProjectPermissions(projectId) {
    const response = await this.client.get(`/projects/${projectId}/permissions`);
    return response.data;
}
    
    async deleteProject(projectId) {
        await this.client.delete(`/projects/${projectId}`);
    }

    async getProjectAlerts(projectId, aoiId = null) {
        const params = {};
        if (aoiId) params.aoiId = aoiId;

        const response = await this.client.get(`/projects/${projectId}/alerts`, { params });
        return response.data; 
    }

    // --- Analyst Verification & Dossier Endpoints (PS 2.2.5) ---
    async reviewAlert(alertId, reviewData) {
        const response = await this.client.post(`/alerts/${alertId}/review`, reviewData);
        return response.data;
    }

    async getAlertReviews(alertId) {
        const response = await this.client.get(`/alerts/${alertId}/reviews`);
        return response.data;
    }

    async getAlertDossier(alertId) {
        const response = await this.client.get(`/alerts/${alertId}/dossier`);
        return response.data;
    }
    // --- Processing / ML Endpoints ---

    async detectChange(subscriptionId, t1File, t2File, channelType = null) {
        const formData = new FormData();

        formData.append(
            'subscription_id',
            String(subscriptionId)
        );

        formData.append(
            't1',
            t1File
        );

        formData.append(
            't2',
            t2File
        );

        if (channelType) {
            formData.append(
                'channel_type',
                channelType
            );
        }

        const response = await this.client.post(
            '/processing/detect-change',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );

        return response.data;
    }

    // --- PS 2.2.1: Semantic & Multimodal Retrieval Endpoints ---
    async retrieveByText(query, topK = 6) {
        const response = await this.client.post('/processing/retrieve-text', {
            query,
            top_k: topK
        });
        return response.data;
    }

    async retrieveByImage(queryFile, topK = 6) {
        const formData = new FormData();
        formData.append('query_image', queryFile);
        formData.append('top_k', String(topK));

        const response = await this.client.post('/processing/retrieve-image', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }

    async getRetrievalCatalog() {
        const response = await this.client.get('/processing/retrieve-catalog');
        return response.data;
    }
}