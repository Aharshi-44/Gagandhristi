// ProjectTypes.js 


/**
 * @typedef {Object} GeoJsonPolygon
 * @property {'Polygon'} type
 * @property {number[][][]} coordinates
 */

/**
 * Defines the complete data structure that the frontend's ProjectFormData.toBackendBundle() 
 * method must produce, and which the backend's ProjectService.createProject() expects.
 * @typedef {Object} ProjectCreationBundle
 * @property {Object} projectBasicInfo
 * @property {string} projectBasicInfo.projectName
 * @property {string | null} projectBasicInfo.description
 * @property {Record<string, any> | null} projectBasicInfo.auxData
 * @property {Array<Object>} aoiData
 * @property {string} aoiData[].aoiId
 * @property {string} aoiData[].name
 * @property {GeoJsonPolygon} aoiData[].geomGeoJson
 * @property {Record<string, any> | null} aoiData[].geomProperties
 * @property {Array<Object>} aoiData[].mappedAlgorithms
 * @property {string} aoiData[].mappedAlgorithms[].algoId
 * @property {Record<string, any>} aoiData[].mappedAlgorithms[].configArgs
 * @property {Array<Object>} userData
 * @property {string} userData[].userId
 * @property {string} userData[].role
 */
