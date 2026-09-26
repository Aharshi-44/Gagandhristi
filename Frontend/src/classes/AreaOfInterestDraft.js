// classes/AreaOfInterestDraft.js - Updated to store auxData and original coordinates

export class AreaOfInterestDraft {
    clientAoiId;
    name;
    aoiId;
    geometry;
    geomGeoJson; 
    mappedAlgorithms = [];
    bufferDistance = null;
    geometryType = 'Polygon';
    geomProperties = {};
    auxData = null; 
    status = 1;
    dbId = null;

    constructor(
        name,
        geometry,
        clientAoiId,
        geometryType = 'Polygon',
        bufferDistance = null
    ) {
        this.clientAoiId = clientAoiId;
        this.name = name;
        this.aoiId = `aoi-${clientAoiId}`;
        
        if (!geometry) {
            throw new Error(`AOI ${name} must have valid geometry`);
        }
        
        this.geometry = geometry;
        this.geomGeoJson = geometry;
        this.geometryType = geometryType;
        this.bufferDistance = bufferDistance;

        this.geomProperties = {
            originalType: geometryType,
            buffer: bufferDistance
        };
    }

    mapAlgorithm(algoId, name, configArgs = {}, status = 1, mappingId = null) { 
        const existing = this.mappedAlgorithms.find(a => 
            a.algoId === algoId && a.mappingId === mappingId
        );

        if (existing) {
            existing.configArgs = configArgs;
            existing.status = status;
        } else {
            this.mappedAlgorithms.push({ 
                algoId, 
                name, 
                configArgs, 
                status: status, 
                mappingId: mappingId 
            });
        }
    }

    removeAlgorithm(algoId, mappingId = null) {
        const mapping = this.mappedAlgorithms.find(a => 
            a.algoId === algoId && a.mappingId === mappingId
        );
        
        if (mapping) {
            if (mapping.mappingId) {
                mapping.status = 2;
            } else {
                this.mappedAlgorithms = this.mappedAlgorithms.filter(a => 
                    !(a.algoId === algoId && a.mappingId === mappingId)
                );
            }
        }
    }

    toggleAlgorithmStatus(algoId, mappingId = null) {
        const mapping = this.mappedAlgorithms.find(a => 
            a.algoId === algoId && a.mappingId === mappingId
        );
        
        if (mapping && mapping.mappingId) {
            mapping.status = mapping.status === 1 ? 0 : 1;
        }
    }

    getActiveAlgorithms() {
        return this.mappedAlgorithms.filter(a => a.status !== 2);
    }

    markForDeletion() {
        this.status = 2;
        this.mappedAlgorithms.forEach(a => {
            if (a.mappingId) a.status = 2;
        });
    }

    /**
     * NEW: Set auxiliary data for this AOI
     */
    setAuxData(auxData) {
        this.auxData = auxData;
    }

    toBackendData() {
        if (!this.geometry) {
            throw new Error(`Cannot serialize AOI ${this.name} - missing geometry`);
        }

        // Validate geometry structure
        if (this.geometry.type === 'GeometryCollection') {
            if (!this.geometry.geometries || this.geometry.geometries.length === 0) {
                throw new Error(`Cannot serialize AOI ${this.name} - empty GeometryCollection`);
            }
        } else {
            if (!this.geometry.coordinates || this.geometry.coordinates.length === 0) {
                throw new Error(`Cannot serialize AOI ${this.name} - invalid coordinates`);
            }
        }

        // this Store original coordinates in geomProperties
        const geomProps = {
            ...this.geomProperties,
            originalType: this.geometryType,
            buffer: this.bufferDistance,
        };

        return {
            aoiId: this.aoiId,
            dbId: this.dbId,
            name: this.name,
            geomGeoJson: this.geometry,
            geomProperties: geomProps,
            auxData: this.auxData, 
            status: this.status,
            mappedAlgorithms: this.mappedAlgorithms.map(a => ({
                algoId: a.algoId,
                configArgs: a.configArgs,
                status: a.status,
                mappingId: a.mappingId
            }))
        };
    }
}