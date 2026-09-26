import { Router } from 'express';
import multer from 'multer';

import { ProcessingService } from '../services/ProcessingService.js';


export class ProcessingController {

    router;

    processingService;

    upload;


    constructor() {

        this.router =
            Router();

        this.processingService =
            new ProcessingService();


        // ----------------------------------------------------
        // Store uploaded images in memory.
        // They are immediately forwarded to Python.
        // ----------------------------------------------------

        this.upload =
            multer({
                storage:
                    multer.memoryStorage(),

                limits: {
                    fileSize:
                        50 * 1024 * 1024
                }
            });


        this.initializeRoutes();
    }


    initializeRoutes() {

        // ----------------------------------------------------
        // Process T1 + T2 and create alert
        // ----------------------------------------------------

        this.router.post(
            '/detect-change',
            this.upload.fields([
                {
                    name: 't1',
                    maxCount: 1
                },
                {
                    name: 't2',
                    maxCount: 1
                }
            ]),
            this.detectChange
        );

        // PS 2.2.1: Semantic & Multimodal Retrieval Endpoints
        this.router.post('/retrieve-text', this.retrieveByText);
        this.router.post('/retrieve-image', this.upload.single('query_image'), this.retrieveByImage);
        this.router.get('/retrieve-catalog', this.getCatalog);
    }


    detectChange =
        async (
            req,
            res
        ) => {

            try {

                // ------------------------------------------------
                // Get subscription
                // ------------------------------------------------

                const subscriptionId =
                    req.body.subscription_id;

                const channelType =
                    req.body.channel_type || null;

                if (!subscriptionId) {

                    return res.status(400).json({

                        error:
                            'subscription_id is required.'
                    });
                }


                // ------------------------------------------------
                // Get uploaded files
                // ------------------------------------------------

                const t1 =
                    req.files?.t1?.[0];

                const t2 =
                    req.files?.t2?.[0];


                if (!t1) {

                    return res.status(400).json({

                        error:
                            'T1 image is required.'
                    });
                }


                if (!t2) {

                    return res.status(400).json({

                        error:
                            'T2 image is required.'
                    });
                }


                // ------------------------------------------------
                // Validate image MIME types
                // ------------------------------------------------

                const allowedTypes = [
                    'image/jpeg',
                    'image/jpg',
                    'image/png',
                    'image/tiff',
                    'image/tif',
                    'image/geotiff',
                    'application/octet-stream'
                ];

                const isTiff1 = t1.originalname && Boolean(t1.originalname.match(/\.(tif|tiff|geotiff)$/i));
                const isTiff2 = t2.originalname && Boolean(t2.originalname.match(/\.(tif|tiff|geotiff)$/i));

                if (!allowedTypes.includes(t1.mimetype) && !isTiff1) {
                    return res.status(400).json({
                        error: 'T1 must be a JPEG, PNG, or GeoTIFF image.'
                    });
                }

                if (!allowedTypes.includes(t2.mimetype) && !isTiff2) {
                    return res.status(400).json({
                        error: 'T2 must be a JPEG, PNG, or GeoTIFF image.'
                    });
                }


                // ------------------------------------------------
                // Run processing + create alert
                // ------------------------------------------------

                console.log(
                    `\n[Processing] Change detection request received (channel: ${channelType || 'auto'}).`
                );


                const result =
                    await this.processingService
                        .detectChangeAndCreateAlert(
                            t1,
                            t2,
                            subscriptionId,
                            channelType
                        );


                // ------------------------------------------------
                // Return result
                // ------------------------------------------------

                return res.status(200).json(
                    result
                );

            } catch (error) {

                console.error(
                    '[Processing] Error:',
                    error
                );


                return res.status(500).json({
                    error:
                        error.message
                });
            }
        };

    /**
     * POST /api/processing/retrieve-text
     */
    retrieveByText = async (req, res) => {
        try {
            const { query, top_k } = req.body;
            if (!query) {
                return res.status(400).json({ error: 'Search query is required.' });
            }
            const result = await this.processingService.retrieveByText(query, top_k);
            return res.status(200).json(result);
        } catch (error) {
            console.error('[ProcessingController] Error in retrieveByText:', error);
            return res.status(500).json({ error: error.message });
        }
    };

    /**
     * POST /api/processing/retrieve-image
     */
    retrieveByImage = async (req, res) => {
        try {
            const file = req.file;
            const topK = req.body.top_k || 5;
            if (!file) {
                return res.status(400).json({ error: 'query_image file is required.' });
            }
            const result = await this.processingService.retrieveByImage(file, topK);
            return res.status(200).json(result);
        } catch (error) {
            console.error('[ProcessingController] Error in retrieveByImage:', error);
            return res.status(500).json({ error: error.message });
        }
    };

    /**
     * GET /api/processing/retrieve-catalog
     */
    getCatalog = async (req, res) => {
        try {
            const result = await this.processingService.getCatalog();
            return res.status(200).json(result);
        } catch (error) {
            console.error('[ProcessingController] Error in getCatalog:', error);
            return res.status(500).json({ error: error.message });
        }
    };
}