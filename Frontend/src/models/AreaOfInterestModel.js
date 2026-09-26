// models/AreaOfInterestModel.js

/**
 * AreaOfInterestModel: Represents an Area of Interest (AOI)
 * Acts as a blueprint for AOI data structure
 */
export class AreaOfInterestModel {
    id = null; 
    aoiId = null; 
    clientAoiId = null; 
    projectId = null;
    name = '';
    geomGeoJson = null; 
    geomProperties = null; 
    auxData = null; 
    status = 1; 
    mappedAlgorithms = []; 

    /**
     * @param {Object} data - Data to initialize the model
     */
    constructor(data = {}) {
        this.id = data.id || data.dbId || null;
        this.aoiId = data.aoiId || null;
        this.clientAoiId = data.clientAoiId || null;
        this.projectId = data.projectId || null;
        this.name = data.name || '';
        this.geomGeoJson = data.geomGeoJson || data.geometry || null;
        this.geomProperties = data.geomProperties || data.geom_properties || null;
        this.auxData = data.auxData || data.auxdata || null;
        this.status = data.status ?? 1;
        this.mappedAlgorithms = data.mappedAlgorithms || [];
    }

    /**
     * Validates the AOI model
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
        const errors = [];

        if (!this.name || this.name.trim() === '') {
            errors.push('AOI name is required');
        }

        if (!this.geomGeoJson) {
            errors.push('AOI geometry is required');
        } else {
            // Validate geometry structure
            if (this.geomGeoJson.type === 'GeometryCollection') {
                if (!this.geomGeoJson.geometries || this.geomGeoJson.geometries.length === 0) {
                    errors.push('AOI geometry cannot be an empty GeometryCollection');
                }
            } else {
                if (!this.geomGeoJson.coordinates || this.geomGeoJson.coordinates.length === 0) {
                    errors.push('AOI geometry must have valid coordinates');
                }
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Converts to backend bundle format (aoiData)
     * @returns {Object} Backend bundle format
     */
    toBackendBundle() {
        const validation = this.validate();
        if (!validation.valid) {
            throw new Error(`Cannot serialize AOI "${this.name}": ${validation.errors.join(', ')}`);
        }

        return {
            aoiId: this.aoiId || `aoi_${this.clientAoiId}`,
            dbId: this.id,
            name: this.name,
            geomGeoJson: this.geomGeoJson,
            geomProperties: this.geomProperties,
            auxData: this.auxData,
            status: this.status,
            mappedAlgorithms: this.mappedAlgorithms.map(algo => ({
                algoId: algo.algoId,
                configArgs: algo.configArgs || {},
                status: algo.status ?? 1,
                mappingId: algo.mappingId || null
            }))
        };
    }

    /**
     * Creates an AreaOfInterestModel from backend response
     * @param {Object} data - Backend response data
     * @param {number} clientAoiId - Client-side ID for mapping
     * @returns {AreaOfInterestModel}
     */
    static fromBackend(data, clientAoiId = null) {
        return new AreaOfInterestModel({
            id: data.id,
            aoiId: data.aoi_id,
            clientAoiId: clientAoiId,
            projectId: data.project_id,
            name: data.name,
            geomGeoJson: data.geomGeoJson,
            geom_properties: data.geom_properties,
            auxdata: data.auxdata,
            status: data.status ?? 1,
            mappedAlgorithms: data.mappedAlgorithms || []
        });
    }

    /**
     * Creates an AreaOfInterestModel from AreaOfInterestDraft
     * @param {AreaOfInterestDraft} draft - Draft object
     * @returns {AreaOfInterestModel}
     */
    static fromDraft(draft) {
        return new AreaOfInterestModel({
            id: draft.dbId,
            aoiId: draft.aoiId,
            clientAoiId: draft.clientAoiId,
            name: draft.name,
            geomGeoJson: draft.geomGeoJson || draft.geometry,
            geomProperties: draft.geomProperties,
            auxData: draft.auxData,
            status: draft.status,
            mappedAlgorithms: draft.mappedAlgorithms || []
        });
    }

    /**
     * Sets auxiliary data
     * @param {Object|null} auxData - Auxiliary data object
     */
    setAuxData(auxData) {
        this.auxData = auxData;
    }

    /**
     * Marks the AOI as deleted (soft delete)
     */
    markAsDeleted() {
        this.status = 2;
        // Also mark all mapped algorithms as deleted
        this.mappedAlgorithms.forEach(algo => {
            if (algo.mappingId) {
                algo.status = 2;
            }
        });
    }

    /**
     * Toggles AOI status between active (1) and inactive (0)
     */
    toggleStatus() {
        if (this.status === 2) {
            throw new Error('Cannot toggle status of deleted AOI');
        }
        this.status = this.status === 1 ? 0 : 1;
    }

    /**
     * Gets active (non-deleted) mapped algorithms
     * @returns {Array}
     */
    getActiveAlgorithms() {
        return this.mappedAlgorithms.filter(algo => algo.status !== 2);
    }
}



