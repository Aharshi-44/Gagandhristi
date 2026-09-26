// AlertReviewModel.js
import { DBClient } from '../db/DBClient.js';

const db = DBClient.getInstance();

/**
 * AlertReviewModel: Handles database interactions for human-in-the-loop analyst reviews.
 */
export class AlertReviewModel {
    id = null;
    alertId = null;
    reviewerId = null;
    reviewStatus = null;
    confidenceRating = null;
    notes = null;
    reviewedAt = null;

    constructor(data) {
        this.id = data.id || null;
        this.alertId = data.alert_id || null;
        this.reviewerId = data.reviewer_id || null;
        this.reviewStatus = data.review_status || null;
        this.confidenceRating = data.confidence_rating || 'HIGH';
        this.notes = data.notes || '';
        this.reviewedAt = data.reviewed_at || null;
    }

    /**
     * Inserts a new review record for an alert.
     */
    static async create({ alertId, reviewerId, reviewStatus, confidenceRating = 'HIGH', notes = '' }) {
        if (!alertId || !reviewerId || !reviewStatus) {
            throw new Error('alertId, reviewerId, and reviewStatus are required to record a review.');
        }

        const validStatuses = ['CONFIRMED', 'FALSE_ALARM', 'REJECTED', 'INVESTIGATING'];
        if (!validStatuses.includes(reviewStatus)) {
            throw new Error(`Invalid review status: ${reviewStatus}. Allowed: ${validStatuses.join(', ')}`);
        }

        const query = `
            INSERT INTO alert_reviews (alert_id, reviewer_id, review_status, confidence_rating, notes, reviewed_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            RETURNING id, alert_id, reviewer_id, review_status, confidence_rating, notes, reviewed_at;
        `;
        const values = [alertId, reviewerId, reviewStatus, confidenceRating, notes];
        const result = await db.query(query, values);
        return new AlertReviewModel(result.rows[0]);
    }

    /**
     * Retrieves all review history for a specific alert, newest first.
     */
    static async findByAlertId(alertId) {
        const query = `
            SELECT id, alert_id, reviewer_id, review_status, confidence_rating, notes, reviewed_at
            FROM alert_reviews
            WHERE alert_id = $1
            ORDER BY reviewed_at DESC;
        `;
        const result = await db.query(query, [alertId]);
        return result.rows.map(row => new AlertReviewModel(row));
    }

    /**
     * Retrieves the latest review for an alert.
     */
    static async getLatestByAlertId(alertId) {
        const query = `
            SELECT id, alert_id, reviewer_id, review_status, confidence_rating, notes, reviewed_at
            FROM alert_reviews
            WHERE alert_id = $1
            ORDER BY reviewed_at DESC
            LIMIT 1;
        `;
        const result = await db.query(query, [alertId]);
        if (result.rows.length === 0) return null;
        return new AlertReviewModel(result.rows[0]);
    }
}
