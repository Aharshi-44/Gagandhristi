// backend/src/controllers/AlertsController.js

import { Router } from 'express';
import { AlertsService } from '../services/AlertsService.js';

/**
 * AlertsController: Manages all API endpoints related to alerts, analyst verification, and dossiers.
 */
export class AlertsController {
    router;
    alertsService;

    constructor() {
        this.router = Router();
        this.alertsService = new AlertsService();
        this.initializeRoutes();
    }

    initializeRoutes() {
        // Base alert creation (used by processing pipeline)
        this.router.post('/', this.recordAlert);

        // Analyst review & dossier routes
        this.router.post('/:id/review', this.reviewAlert);
        this.router.get('/:id/reviews', this.getAlertReviews);
        this.router.get('/:id/dossier', this.getAlertDossier);
    }

    /**
     * Express handler to record a new alert based on the request body.
     * Expects: { subscription_id: number, content: object }
     */
    recordAlert = async (req, res, next) => {
        try {
            const payload = req.body;
            
            if (!payload.subscription_id || !payload.content) {
                 return res.status(400).json({ error: 'Missing required fields: subscription_id or content.' });
            }

            const newAlert = await this.alertsService.recordNewAlert(payload);

            res.status(201).json({
                message: 'Alert successfully recorded.',
                alert: {
                    id: newAlert.id,
                    subscription_id: newAlert.subscriptionId,
                    content: newAlert.content,
                    alert_timestamp: newAlert.alertTimestamp
                }
            });

        } catch (error) {
            console.error('Error in recordAlert:', error);
            res.status(400).json({ error: error.message });
        }
    };

    /**
     * POST /api/alerts/:id/review
     * Records an imagery analyst's review decision for an alert.
     */
    reviewAlert = async (req, res) => {
        try {
            const alertId = parseInt(req.params.id, 10);
            if (isNaN(alertId)) {
                return res.status(400).json({ error: 'Invalid alert ID format.' });
            }

            const reviewerId = req.header('X-User-ID') || req.body.reviewer_id || 'DEFENCE_ANALYST';
            const { review_status, notes, confidence_rating } = req.body;

            if (!review_status) {
                return res.status(400).json({ error: 'review_status is required (CONFIRMED, FALSE_ALARM, REJECTED).' });
            }

            const review = await this.alertsService.recordReview(alertId, reviewerId, {
                review_status,
                notes,
                confidence_rating
            });

            res.status(200).json({
                message: 'Analyst review recorded successfully.',
                review
            });
        } catch (error) {
            console.error('Error in reviewAlert:', error);
            res.status(400).json({ error: error.message });
        }
    };

    /**
     * GET /api/alerts/:id/reviews
     * Retrieves the audit trail of reviews for a given alert.
     */
    getAlertReviews = async (req, res) => {
        try {
            const alertId = parseInt(req.params.id, 10);
            if (isNaN(alertId)) {
                return res.status(400).json({ error: 'Invalid alert ID format.' });
            }

            const reviews = await this.alertsService.getReviews(alertId);
            res.status(200).json({ reviews });
        } catch (error) {
            console.error('Error in getAlertReviews:', error);
            res.status(500).json({ error: error.message });
        }
    };

    /**
     * GET /api/alerts/:id/dossier
     * Generates a formal military intelligence dossier for the alert.
     */
    getAlertDossier = async (req, res) => {
        try {
            const alertId = parseInt(req.params.id, 10);
            if (isNaN(alertId)) {
                return res.status(400).json({ error: 'Invalid alert ID format.' });
            }

            const dossier = await this.alertsService.generateDossier(alertId);
            res.status(200).json({ dossier });
        } catch (error) {
            console.error('Error in getAlertDossier:', error);
            res.status(404).json({ error: error.message });
        }
    };
}