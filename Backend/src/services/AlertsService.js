// AlertsService.js

import { AlertModel } from '../models/AlertModel.js';
import { AlertReviewModel } from '../models/AlertReviewModel.js';
import { DBClient } from '../db/DBClient.js';

const db = DBClient.getInstance();

function normalizeFeatureGeoJson(input) {
    if (!input) return null;

    // Already a Feature
    if (input.type === "Feature") return input;

    // If raw geometry → wrap as Feature
    if (input.type && input.coordinates) {
        return {
            type: "Feature",
            geometry: input,
            properties: {}
        };
    }

    // If FeatureCollection → keep as is
    return input;
}

/**
 * AlertsService: Manages business logic related to alerts and analyst reviews.
 */
export class AlertsService {

    /**
     * Records a new alert using the data provided in the API request body.
     */
    async recordNewAlert(payload) {
        if (!payload.subscription_id || !payload.content) {
            throw new Error("Missing required fields for alert: subscription_id or content.");
        }

        const newAlert = new AlertModel({
            subscription_id: payload.subscription_id,
            content: payload.content,
            auxdata: payload.auxdata || null,
            feature_geojson: normalizeFeatureGeoJson(payload.feature_geojson),
        });

        await newAlert.save();
        return newAlert;
    }

    /**
     * Records a human-in-the-loop analyst review for an alert.
     */
    async recordReview(alertId, reviewerId, reviewData) {
        const { review_status, notes = '', confidence_rating = 'HIGH' } = reviewData;

        // Verify alert exists
        const alertCheck = await db.query('SELECT id FROM alerts WHERE id = $1', [alertId]);
        if (alertCheck.rows.length === 0) {
            throw new Error(`Alert with ID ${alertId} not found.`);
        }

        const review = await AlertReviewModel.create({
            alertId: parseInt(alertId, 10),
            reviewerId,
            reviewStatus: review_status,
            confidenceRating: confidence_rating,
            notes
        });

        return review;
    }

    /**
     * Retrieves all review audit history for an alert.
     */
    async getReviews(alertId) {
        return await AlertReviewModel.findByAlertId(parseInt(alertId, 10));
    }

    /**
     * Generates a formal military intelligence dossier (SITREP) for an alert.
     */
    async generateDossier(alertId) {
        const alertIdInt = parseInt(alertId, 10);

        const query = `
            SELECT
                a.id AS alert_id,
                a.content AS alert_content,
                a.alert_timestamp,
                a.auxdata,
                a.feature_geojson,
                s.id AS subscription_id,
                s.project_id,
                s.aoi_id,
                s.channel_id,
                p.name AS project_name,
                p.description AS project_description,
                aoi.name AS aoi_name,
                ST_AsGeoJSON(aoi.geom) AS aoi_geojson,
                acc.channel_name,
                acc.category AS channel_category,
                acc.script_name AS channel_script_name
            FROM alerts a
            JOIN subscription s ON a.subscription_id = s.id
            JOIN project p ON s.project_id = p.id
            JOIN area_of_interest aoi 
                ON s.project_id = aoi.project_id 
                AND s.aoi_id = aoi.aoi_id
            JOIN alert_channel_catalogue acc ON s.channel_id = acc.id
            WHERE a.id = $1;
        `;

        const result = await db.query(query, [alertIdInt]);
        if (result.rows.length === 0) {
            throw new Error(`Alert with ID ${alertId} not found.`);
        }

        const row = result.rows[0];
        const reviewHistory = await AlertReviewModel.findByAlertId(alertIdInt);
        const latestReview = reviewHistory.length > 0 ? reviewHistory[0] : null;

        // Parse content safely
        let contentObj = row.alert_content;
        if (typeof contentObj === 'string') {
            try {
                contentObj = JSON.parse(contentObj);
            } catch {
                contentObj = { raw: contentObj };
            }
        }

        // Construct standard Defence Military Intelligence Dossier / SITREP
        return {
            dossier_id: `DOSSIER-GARUDA-${row.alert_id}-${Date.now().toString(36).toUpperCase()}`,
            classification: "SECRET // RESTRICTED - DEFENCE SPACE AGENCY",
            mission_title: "GARUDA SATELLITE MULTI-TEMPORAL CHANGE SURVEILLANCE",
            generated_at: new Date().toISOString(),
            alert_id: row.alert_id,
            target_aoi: {
                aoi_id: row.aoi_id,
                aoi_name: row.aoi_name,
                project_id: row.project_id,
                project_name: row.project_name,
                project_description: row.project_description,
                aoi_geojson: row.aoi_geojson ? (typeof row.aoi_geojson === 'string' ? JSON.parse(row.aoi_geojson) : row.aoi_geojson) : null,
                feature_geojson: row.feature_geojson
            },
            sensor_and_algorithm: {
                channel_id: row.channel_id,
                channel_name: row.channel_name,
                category: row.channel_category,
                script_name: row.channel_script_name,
                detection_timestamp: row.alert_timestamp
            },
            quantitative_metrics: contentObj,
            analyst_verification: {
                status: latestReview ? latestReview.reviewStatus : "PENDING",
                reviewer_id: latestReview ? latestReview.reviewerId : null,
                reviewed_at: latestReview ? latestReview.reviewedAt : null,
                confidence_rating: latestReview ? latestReview.confidenceRating : null,
                notes: latestReview ? latestReview.notes : null,
                audit_trail: reviewHistory.map(r => ({
                    id: r.id,
                    reviewer_id: r.reviewerId,
                    status: r.reviewStatus,
                    confidence: r.confidenceRating,
                    notes: r.notes,
                    reviewed_at: r.reviewedAt
                }))
            }
        };
    }
}