import { AlertsService } from './AlertsService.js';
import { DBClient } from '../db/DBClient.js';


export class ProcessingService {

    constructor() {
        this.processingApiUrl =
            process.env.PROCESSING_API_URL ||
            'http://localhost:8000';

        this.alertsService =
            new AlertsService();

        this.db = DBClient.getInstance();
    }


    /**
     * Sends T1 and T2 images to the Python ML processing service
     * with the specified analytical channel.
     */
    async detectChange(
        t1File,
        t2File,
        channelType = 'structural'
    ) {

        if (!t1File) {
            throw new Error('T1 image is required.');
        }

        if (!t2File) {
            throw new Error('T2 image is required.');
        }

        // ----------------------------------------------------
        // Create multipart request
        // ----------------------------------------------------
        const formData = new FormData();

        const t1Mime = t1File.mimetype || (t1File.originalname?.match(/\.(tif|tiff)$/i) ? 'image/tiff' : 'image/jpeg');
        const t2Mime = t2File.mimetype || (t2File.originalname?.match(/\.(tif|tiff)$/i) ? 'image/tiff' : 'image/jpeg');

        const t1Blob = new Blob(
            [t1File.buffer],
            { type: t1Mime }
        );

        const t2Blob = new Blob(
            [t2File.buffer],
            { type: t2Mime }
        );

        formData.append('t1', t1Blob, t1File.originalname);
        formData.append('t2', t2Blob, t2File.originalname);
        formData.append('channel_type', channelType || 'structural');

        // ----------------------------------------------------
        // Call Python API
        // ----------------------------------------------------
        console.log(
            `[Processing] Sending images to Python ML service (channel: ${channelType})...`
        );

        const response = await fetch(
            `${this.processingApiUrl}/process`,
            {
                method: 'POST',
                body: formData
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Processing service returned ${response.status}: ${errorText}`
            );
        }

        const result = await response.json();
        console.log(`[Processing] ML processing completed for ${result.channel_type || channelType}.`);

        return result;
    }


    /**
     * Resolves the channel key for a given subscription.
     */
    async resolveChannelForSubscription(subscriptionId) {
        if (!subscriptionId) return { channelKey: 'structural', channelName: 'Structural Infrastructure' };

        try {
            const query = `
                SELECT s.channel_id, acc.script_id, acc.channel_name, acc.category, acc.args
                FROM subscription s
                LEFT JOIN alert_channel_catalogue acc ON s.channel_id = acc.id
                WHERE s.id = $1
            `;
            const result = await this.db.query(query, [Number(subscriptionId)]);

            if (result.rows.length > 0) {
                const row = result.rows[0];
                const channelKey = row.args?.channel_key || 
                    (row.script_id === 'ndvi_vari_vegetation' ? 'vegetation' :
                     row.script_id === 'pixel_diff_cva' ? 'pixel_diff' : 'structural');

                return {
                    channelKey,
                    channelName: row.channel_name || 'Structural Infrastructure',
                    category: row.category || 'INFRASTRUCTURE'
                };
            }
        } catch (error) {
            console.warn('[Processing] Could not resolve channel from DB:', error.message);
        }

        return { channelKey: 'structural', channelName: 'Structural Infrastructure', category: 'INFRASTRUCTURE' };
    }


    /**
     * Runs ML processing and creates a Gagandristhi alert from the result.
     */
    async detectChangeAndCreateAlert(
        t1File,
        t2File,
        subscriptionId,
        explicitChannelType = null
    ) {

        if (!subscriptionId) {
            throw new Error('subscription_id is required.');
        }

        // ----------------------------------------------------
        // Determine channel
        // ----------------------------------------------------
        const channelMeta = await this.resolveChannelForSubscription(subscriptionId);
        const channelType = explicitChannelType || channelMeta.channelKey || 'structural';

        // ----------------------------------------------------
        // Run ML
        // ----------------------------------------------------
        const mlResult = await this.detectChange(
            t1File,
            t2File,
            channelType
        );

        // ----------------------------------------------------
        // Check whether change was detected
        // ----------------------------------------------------
        if (
            !mlResult.change_detection ||
            !mlResult.change_detection.change_detected
        ) {
            return {
                alert_created: false,
                ml_result: mlResult
            };
        }

        // ----------------------------------------------------
        // Construct channel-specific message
        // ----------------------------------------------------
        let alertMessage = 'Change detected between T1 and T2 satellite images.';
        if (mlResult.channel_type === 'VEGETATION_NDVI') {
            alertMessage = `Vegetation clearance detected: ${mlResult.change_detection.change_percentage}% canopy loss.`;
        } else if (mlResult.channel_type === 'PIXEL_DIFFERENCE') {
            alertMessage = `Tactical surface anomaly detected: ${mlResult.change_detection.change_percentage}% disturbed area.`;
        } else if (mlResult.channel_type === 'STRUCTURAL_DL') {
            alertMessage = `Structural infrastructure change detected: ${mlResult.change_detection.number_of_regions} new or altered structures.`;
        }

        // ----------------------------------------------------
        // Create alert content
        // ----------------------------------------------------
        const alertContent = {
            type: 'SATELLITE_CHANGE_DETECTION',
            channel_type: mlResult.channel_type,
            channel_name: channelMeta.channelName || mlResult.channel_type,
            category: channelMeta.category || 'INFRASTRUCTURE',
            message: alertMessage,
            severity: mlResult.change_detection.severity,
            change_percentage: mlResult.change_detection.change_percentage,
            number_of_regions: mlResult.change_detection.number_of_regions,
            regions: mlResult.change_detection.regions,
            model: mlResult.model,
            threshold: mlResult.threshold,
            probability_statistics: mlResult.probability_statistics || null,
            details: mlResult.change_detection
        };

        // ----------------------------------------------------
        // Alert metadata
        // ----------------------------------------------------
        const auxData = {
            source: 'GAGANDRISTHI_ML',
            channel_type: mlResult.channel_type,
            channel_name: channelMeta.channelName,
            model: mlResult.model,
            t1_filename: t1File.originalname,
            t2_filename: t2File.originalname,
            processing_device: mlResult.device,
            mask_url: mlResult.output_mask,
            overlay_url: mlResult.overlay_image
        };

        // ----------------------------------------------------
        // Attach GeoTIFF metadata if available (PS 2.2.6)
        // ----------------------------------------------------
        if (mlResult.geotiff_metadata && mlResult.geotiff_metadata.is_geotiff) {
            alertContent.geotiff_metadata = mlResult.geotiff_metadata;
            auxData.geotiff_metadata = mlResult.geotiff_metadata;
            if (mlResult.t1_preview) auxData.t1_preview_url = mlResult.t1_preview;
            if (mlResult.t2_preview) auxData.t2_preview_url = mlResult.t2_preview;
            if (mlResult.geotiff_metadata.epsg) {
                alertMessage += ` [EPSG:${mlResult.geotiff_metadata.epsg}]`;
                alertContent.message = alertMessage;
            }
        }

        // ----------------------------------------------------
        // Create database alert
        // ----------------------------------------------------
        const alert = await this.alertsService.recordNewAlert({
            subscription_id: Number(subscriptionId),
            content: alertContent,
            auxdata: auxData,
            feature_geojson: mlResult.feature_geojson || null
        });

        console.log(
            `[Processing] Alert created: ${alert.id} (${mlResult.channel_type})${mlResult.feature_geojson ? ' [GEOREFERENCED]' : ''}`
        );

        return {
            alert_created: true,
            alert_id: alert.id,
            alert_timestamp: alert.alertTimestamp,
            channel_type: mlResult.channel_type,
            feature_geojson: mlResult.feature_geojson || null,
            geotiff_metadata: mlResult.geotiff_metadata || null,
            ml_result: mlResult
        };
    }

    // ========================================================
    // PS 2.2.1: SEMANTIC & MULTIMODAL RETRIEVAL METHODS
    // ========================================================

    /**
     * Executes zero-shot natural language retrieval over the satellite catalog.
     */
    async retrieveByText(query, topK = 5) {
        if (!query) throw new Error('Search query is required.');

        const response = await fetch(`${this.processingApiUrl}/retrieve/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, top_k: Number(topK) || 5 })
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Retrieval service error: ${errText}`);
        }

        return await response.json();
    }

    /**
     * Executes query-by-example visual similarity search over the satellite catalog.
     */
    async retrieveByImage(imageFile, topK = 5) {
        if (!imageFile) throw new Error('Query image is required.');

        const formData = new FormData();
        const imgBlob = new Blob([imageFile.buffer], { type: imageFile.mimetype || 'image/jpeg' });
        formData.append('query_image', imgBlob, imageFile.originalname);
        formData.append('top_k', String(topK || 5));

        const response = await fetch(`${this.processingApiUrl}/retrieve/image`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Retrieval service error: ${errText}`);
        }

        return await response.json();
    }

    /**
     * Fetches current satellite tiles catalog summary.
     */
    async getCatalog() {
        const response = await fetch(`${this.processingApiUrl}/retrieve/catalog`);
        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Catalog service error: ${errText}`);
        }
        return await response.json();
    }
}