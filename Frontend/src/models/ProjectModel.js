// models/ProjectModel.js

/**
 * ProjectModel: Represents project basic information
 * Acts as a blueprint for project data structure
 */
export class ProjectModel {
    id = null;
    projectName = '';
    description = null;
    auxData = null;
    createdByUserId = null;
    creationDate = null;
    lastModifiedDate = null;

    /**
     * @param {Object} data - Data to initialize the model
     */
    constructor(data = {}) {
        this.id = data.id || null;
        this.projectName = data.projectName || data.name || '';
        this.description = data.description || null;
        this.auxData = data.auxData || data.auxdata || null;
        this.createdByUserId = data.createdByUserId || data.created_by_userid || null;
        this.creationDate = data.creationDate || data.creation_timestamp || null;
        this.lastModifiedDate = data.lastModifiedDate || data.last_modified_timestamp || null;
    }

    /**
     * Validates the project model
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
        const errors = [];

        if (!this.projectName || this.projectName.trim() === '') {
            errors.push('Project name is required');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Converts to backend bundle format (projectBasicInfo)
     * @returns {Object} Backend bundle format
     */
    toBackendBundle() {
        return {
            projectName: this.projectName,
            description: this.description,
            auxData: this.auxData
        };
    }

    /**
     * Creates a ProjectModel from backend response
     * @param {Object} data - Backend response data
     * @returns {ProjectModel}
     */
    static fromBackend(data) {
        return new ProjectModel({
            id: data.id,
            name: data.project_name || data.name,
            description: data.description,
            auxdata: data.auxdata,
            created_by_userid: data.created_by_userid,
            creation_timestamp: data.creation_timestamp,
            last_modified_timestamp: data.last_modified_timestamp
        });
    }

    /**
     * Creates a ProjectModel from form data (auxDataDrafts array)
     * @param {Object} formData - Form data with auxDataDrafts
     * @returns {ProjectModel}
     */
    static fromFormData(formData) {
        const auxData = {};
        if (formData.auxDataDrafts && formData.auxDataDrafts.length > 0) {
            formData.auxDataDrafts.forEach(item => {
                if (item.key && item.value) {
                    try {
                        auxData[item.key] = JSON.parse(item.value);
                    } catch {
                        auxData[item.key] = item.value;
                    }
                }
            });
        }

        return new ProjectModel({
            id: formData.projectIdToUpdate,
            projectName: formData.projectName,
            description: formData.description,
            auxData: Object.keys(auxData).length > 0 ? auxData : null
        });
    }

    /**
     * Resets the model to default values
     */
    reset() {
        this.id = null;
        this.projectName = '';
        this.description = null;
        this.auxData = null;
        this.createdByUserId = null;
        this.creationDate = null;
        this.lastModifiedDate = null;
    }
}



